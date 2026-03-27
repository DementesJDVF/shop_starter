import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import BaseModel

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
        related_name="vendor_profile",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    verified = models.BooleanField(default=False, db_index=True)
    location_type = models.CharField(
        max_length=10,
        choices=LocationType.choices,
        default=LocationType.FIXED,
    )
    reputation = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    class Meta:
        db_table = "vendors_vendorprofile"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["verified"]),
        ]

    def __str__(self):
        return f"Vendor({self.user.email})"
