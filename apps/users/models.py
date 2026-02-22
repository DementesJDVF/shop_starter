from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):  # ← DEBE DECIR "User", NO "CustomUser"
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('VENDOR', 'Vendor'),
        ('CUSTOMER', 'Customer'),
    )
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CUSTOMER')
    
    def __str__(self):
        return f"{self.username} - {self.role}"