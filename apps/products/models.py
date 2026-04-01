"""Models for product catalog."""

import uuid
from django.db import models
from apps.core.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "products_category"

    def __str__(self) -> str:
        return self.name


class Product(BaseModel):
    """Represents a product published by a vendor profile."""

    class ProductStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        PAUSED = "PAUSED", "Paused"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Out of stock"
        REJECTED = "REJECTED", "Rejected"

    vendor = models.ForeignKey(
        "vendors.VendorProfile",
        on_delete=models.CASCADE,
        related_name="products",
        db_index=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
    )

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        db_index=True,
    )

    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "products_product"
        indexes = [
            models.Index(fields=["vendor"], name="products_vendor_idx"),
            models.Index(fields=["status"], name="products_status_idx"),
        ]

    def __str__(self) -> str:
        return self.name