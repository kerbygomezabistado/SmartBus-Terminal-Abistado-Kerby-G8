from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .forms import SmartBusRegisterForm, ProfileUpdateForm
from .models import CustomUser, Ticket

ROUTE_FARES = {
    'Cebu South Terminal - Carcar City': 85.00,
    'Cebu South Terminal - Moalboal': 185.00,
    'Cebu South Terminal - Oslob': 250.00,
    'Cebu North Terminal - Danao City': 75.00,
    'Cebu North Terminal - Bogo City': 210.00,
}

def kiosk_view(request):
    taken_seats = list(Ticket.objects.values_list('seat_number', flat=True))
    remaining_seats = max(0, 40 - len(taken_seats))
    generated_ticket = None

    if request.method == 'POST':
        if remaining_seats <= 0:
            messages.error(request, 'CAPACITY FREEZE (F-05): All 40 seats on this bus are full!')
        else:
            route = request.POST.get('route_name')
            seat = int(request.POST.get('seat_number'))
            pay_method = request.POST.get('payment_method')

            if seat in taken_seats or seat < 1 or seat > 40:
                messages.error(request, f'Seat #{seat} is already taken or invalid. Please pick an open seat.')
            else:
                fare = ROUTE_FARES.get(route, 85.00)
                generated_ticket = Ticket.objects.create(
                    route_name=route,
                    seat_number=seat,
                    official_fare=fare,
                    payment_method=pay_method,
                )
                taken_seats.append(seat)
                remaining_seats = max(0, 40 - len(taken_seats))
                messages.success(request, f'Ticket {generated_ticket.ticket_code} issued for Seat #{seat}!')

    available_seats = [s for s in range(1, 41) if s not in taken_seats]
    context = {
        'routes': ROUTE_FARES,
        'available_seats': available_seats,
        'remaining_seats': remaining_seats,
        'generated_ticket': generated_ticket,
    }
    return render(request, 'accounts/kiosk.html', context)

def register_view(request):
    if request.method == 'POST':
        form = SmartBusRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff account created! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please fix the errors below.')
    else:
        form = SmartBusRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.role == 'manager':
                return redirect('manager_dashboard')
            return redirect('driver_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def manager_dashboard(request):
    if request.user.role != 'manager':
        messages.error(request, 'Access denied: Terminal Managers only.')
        return redirect('driver_dashboard')

    drivers = CustomUser.objects.filter(role='driver').order_by('-is_active', '-is_available', 'first_name')
    available_count = drivers.filter(is_active=True, is_available=True).count()
    tickets = Ticket.objects.select_related('scanned_by').order_by('-boarded_at', '-created_at')
    boarded_count = tickets.filter(is_boarded=True).count()
    total_revenue = tickets.filter(payment_status='Paid').aggregate(total=Sum('official_fare'))['total'] or 0

    context = {
        'drivers': drivers,
        'total_drivers': drivers.count(),
        'available_count': available_count,
        'tickets': tickets,
        'total_tickets': tickets.count(),
        'boarded_count': boarded_count,
        'total_revenue': total_revenue,
    }
    return render(request, 'accounts/manager_dashboard.html', context)

@login_required
def toggle_driver_availability(request, driver_id):
    if request.user.role != 'manager':
        return redirect('driver_dashboard')
    driver = get_object_or_404(CustomUser, id=driver_id, role='driver')
    driver.is_available = not driver.is_available
    driver.save()
    status_text = 'Available for Dispatch' if driver.is_available else 'Unavailable / On Duty'
    messages.success(request, f"{driver.get_full_name() or driver.username} is now marked {status_text}.")
    return redirect('manager_dashboard')

@login_required
def toggle_driver_active(request, driver_id):
    if request.user.role != 'manager':
        return redirect('driver_dashboard')
    driver = get_object_or_404(CustomUser, id=driver_id, role='driver')
    driver.is_active = not driver.is_active
    if not driver.is_active:
        driver.is_available = False
    driver.save()
    state = 'activated' if driver.is_active else 'deactivated (history preserved)'
    messages.info(request, f"Account for {driver.get_full_name() or driver.username} has been {state}.")
    return redirect('manager_dashboard')

@login_required
def driver_dashboard(request):
    if request.user.role != 'driver':
        return redirect('manager_dashboard')

    scan_result = None
    if request.method == 'POST':
        code = request.POST.get('ticket_code', '').strip().upper()
        action = request.POST.get('action', 'scan')
        ticket = Ticket.objects.filter(ticket_code=code).first()

        if not ticket:
            scan_result = {'status': 'invalid', 'message': f'REJECTED: Ticket code "{code}" not found in system.'}
        elif ticket.is_boarded:
            scan_result = {'status': 'duplicate', 'ticket': ticket, 'message': f'ALREADY BOARDED: {ticket.ticket_code} (Seat #{ticket.seat_number}) was already scanned.'}
        elif ticket.payment_status == 'Paid':
            ticket.is_boarded = True
            ticket.scanned_by = request.user
            ticket.boarded_at = timezone.now()
            ticket.save()
            scan_result = {'status': 'allow', 'ticket': ticket, 'message': f'ALLOW BOARDING — Prepaid Ticket Verified (Seat #{ticket.seat_number}).'}
        elif ticket.payment_status == 'Pending':
            if action == 'confirm_cash':
                ticket.payment_status = 'Paid'
                ticket.is_boarded = True
                ticket.scanned_by = request.user
                ticket.boarded_at = timezone.now()
                ticket.save()
                scan_result = {'status': 'allow', 'ticket': ticket, 'message': f'CASH ₱{ticket.official_fare} RECORDED & BOARDED (Seat #{ticket.seat_number}).'}
            else:
                scan_result = {'status': 'collect', 'ticket': ticket, 'message': f'COLLECT EXACT FARE: ₱{ticket.official_fare} before boarding!'}

    recent_scans = Ticket.objects.filter(is_boarded=True).order_by('-boarded_at')[:10]
    boarded_total = Ticket.objects.filter(is_boarded=True).count()
    context = {
        'scan_result': scan_result,
        'recent_scans': recent_scans,
        'boarded_total': boarded_total,
    }
    return render(request, 'accounts/driver_dashboard.html', context)

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})
