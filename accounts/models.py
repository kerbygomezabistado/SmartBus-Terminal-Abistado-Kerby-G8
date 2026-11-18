from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Terminal Admin'),
        ('passenger', 'Passenger'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='passenger')
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
