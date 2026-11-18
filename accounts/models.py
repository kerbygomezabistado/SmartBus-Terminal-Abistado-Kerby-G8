import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('manager', 'Terminal Manager'),
        ('driver', 'Bus Driver / Operator'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='driver')
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    employee_id = models.CharField(max_length=30, unique=True, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} - {self.get_role_display()}"

class Ticket(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('online', 'Online Prepaid'),
        ('cash', 'Cash at Boarding'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
    )

    ticket_code = models.CharField(max_length=12, unique=True, editable=False)
    route_name = models.CharField(max_length=100, default='Cebu South Bus Terminal - Carcar City')
    seat_number = models.PositiveIntegerField()
    official_fare = models.DecimalField(max_digits=8, decimal_places=2, default=85.00)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    is_boarded = models.BooleanField(default=False)
    scanned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='scanned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    boarded_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            self.ticket_code = f"SBT-{uuid.uuid4().hex[:6].upper()}"
        if self.payment_method == 'online' and not self.pk:
            self.payment_status = 'Paid'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_code} (Seat #{self.seat_number})"
