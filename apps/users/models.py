from django.contrib.auth.models import AbstractUser
from django.db import models
from .constants import UserRoles


class User(AbstractUser):

    role = models.CharField(
        max_length=20,
        choices=UserRoles.CHOICES,
        default=UserRoles.CLIENTE
    )

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        INACTIVE = "INACTIVE", "Inactivo"
        BLOCKED = "BLOCKED", "Bloqueado"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRoles.CHOICES)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    
    def __str__(self):
        return f"{self.username} - {self.role}"
