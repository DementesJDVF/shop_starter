import uuid
from typing import TypeVar

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count

from apps.core.models import BaseModel
from apps.core.models.querysets import SoftDeleteQuerySet


VendorProfileQuerySetType = TypeVar("VendorProfileQuerySetType", bound="VendorProfileQuerySet")


class VendorProfileQuerySet(SoftDeleteQuerySet):
    """QuerySet utilities for vendor profile read models."""

    def with_rating(self: VendorProfileQuerySetType) -> VendorProfileQuerySetType:
        """Annotate vendor profiles with rating summary fields."""
        return self.annotate(
            average_rating=Avg("reviews__rating"),
            total_reviews=Count("reviews"),
        )


class VendorProfile(BaseModel):
    objects = VendorProfileQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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
        return f"VendorProfile({self.user.email})"


class Vendor(VendorProfile):
    """Backward-compatible proxy for code that still references vendors.Vendor."""

    class Meta:
        proxy = True
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"
