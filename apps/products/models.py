"""Models for product catalog."""

from django.db import models

from apps.core.models import BaseModel


class Product(BaseModel):
    """Represents a product published by a vendor profile."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Out of stock"
        REJECTED = "REJECTED", "Rejected"

    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="products",
        db_index=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    is_deleted = models.BooleanField(default=False, db_index=False)

    class Meta:
        indexes = [
            models.Index(fields=["vendor"], name="products_vendor_idx"),
            models.Index(fields=["status"], name="products_status_idx"),
            models.Index(fields=["is_deleted"], name="products_is_deleted_idx"),
        ]

    def __str__(self) -> str:
        return self.name
