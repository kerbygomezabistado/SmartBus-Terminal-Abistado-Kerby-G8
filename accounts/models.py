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

    def __str__(self):
        return f"{self.get_full_name() or self.username} - {self.get_role_display()}"
