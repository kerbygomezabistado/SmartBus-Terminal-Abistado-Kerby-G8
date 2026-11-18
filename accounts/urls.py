from django.urls import path
from . import views

urlpatterns = [
    path('kiosk/', views.kiosk_view, name='kiosk'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('driver/<int:driver_id>/toggle-availability/', views.toggle_driver_availability, name='toggle_driver_availability'),
    path('driver/<int:driver_id>/toggle-active/', views.toggle_driver_active, name='toggle_driver_active'),
    path('driver-dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('profile/', views.profile_view, name='profile'),
]
