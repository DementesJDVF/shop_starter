import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import UserRoles


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        INACTIVE = "INACTIVE", "Inactivo"
        PENDING = "PENDING", "Pendiente de Aprobación"
        BLOCKED = "BLOCKED", "Bloqueado"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRoles.CHOICES, default=UserRoles.CLIENTE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    reputation_score = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    
    # Datos de contacto y perfil
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    document_type = models.CharField(max_length=20, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    # Términos y Condiciones
    acepto_terminos = models.BooleanField(default=False)
    fecha_aceptacion_terminos = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users_user"

    def __str__(self):
        return f"{self.username} - {self.role}"
