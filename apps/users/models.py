import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import UserRoles


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        ACTIVE = "ACTIVE", "Activo"
        REJECTED = "REJECTED", "Negado"
        INACTIVE = "INACTIVE", "Inactivo"
        BLOCKED = "BLOCKED", "Bloqueado"

    class DocumentType(models.TextChoices):
        CC = "CC", "Cédula de ciudadanía"
        CE = "CE", "Cédula de extranjería"
        NIT = "NIT", "NIT"
        PASSPORT = "PASSPORT", "Pasaporte"

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, default="")
    document_type = models.CharField(max_length=20, choices=DocumentType.choices, blank=True, default="")
    document_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    document_issue_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    business_name = models.CharField(max_length=255, blank=True, default="")
    product_types = models.TextField(blank=True, default="")
    role = models.CharField(max_length=20, choices=UserRoles.CHOICES, default=UserRoles.CLIENTE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users_user"

    def __str__(self):
        return f"{self.username} - {self.role}"