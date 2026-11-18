from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SmartBusRegisterForm, ProfileUpdateForm

def register_view(request):
    if request.method == 'POST':
        form = SmartBusRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'SmartBus account created! You can now log in.')
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
            if user.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('passenger_dashboard')
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
def admin_dashboard(request):
    if request.user.role != 'admin':
        messages.error(request, 'Access denied: Terminal Admins only.')
        return redirect('passenger_dashboard')
    return render(request, 'accounts/admin_dashboard.html')

@login_required
def passenger_dashboard(request):
    if request.user.role != 'passenger':
        return redirect('admin_dashboard')
    return render(request, 'accounts/passenger_dashboard.html')

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
