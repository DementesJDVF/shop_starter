from django.conf import settings
from django.db import models
from apps.core.models import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator


class Vendor(BaseModel):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        ACTIVE = "ACTIVE", "Activo"
        BLOCKED = "BLOCKED", "Bloqueado"

    class LocationType(models.TextChoices):
        FIXED = "FIXED", "Fijo"
        MOBILE = "MOBILE", "Móvil"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendor"  # ✅ Cambiar a minúscula
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    verified = models.BooleanField(default=False)

    location_type = models.CharField(
        max_length=10,
        choices=LocationType.choices
    )

    reputation = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ]
    )

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["verified"]),
        ]

    def __str__(self):
        return f"Vendor({self.user.email})"