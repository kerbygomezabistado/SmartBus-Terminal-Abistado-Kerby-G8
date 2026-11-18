from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SmartBusRegisterForm, ProfileUpdateForm
from .models import CustomUser

def kiosk_view(request):
    return render(request, 'accounts/kiosk.html')

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

    context = {
        'drivers': drivers,
        'total_drivers': drivers.count(),
        'available_count': available_count,
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
    return render(request, 'accounts/driver_dashboard.html')

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
