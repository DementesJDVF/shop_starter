"""Service layer for product business logic."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.products.models import Product
from apps.users.constants import UserRoles
from apps.vendors.models import Vendor


class ProductService:
    """Encapsulates product-related business rules."""

    @staticmethod
    def validate_vendor_can_manage_products(*, user: Any) -> Vendor:
        """Validate that the authenticated user is an active vendor."""
        if not getattr(user, "is_authenticated", False):
            raise ValueError("Authentication required")

        if user.role != UserRoles.VENDEDOR:
            raise ValueError("Only vendor users can manage products")

        try:
            vendor_profile = user.vendor
        except Vendor.DoesNotExist as exc:
            raise ValueError("Vendor profile not found") from exc

        if vendor_profile.status != Vendor.Status.ACTIVE:
            raise ValueError("Vendor profile must be active")

        return vendor_profile

    @staticmethod
    @transaction.atomic
    def create_product(*, vendor_profile: Vendor, data: dict[str, Any]) -> Product:
        """Create a product owned by the given vendor profile."""
        return Product.objects.create(
            vendor=vendor_profile,
            name=data["name"],
            description=data["description"],
            price=data["price"],
            stock=data.get("stock", 0),
            status=Product.Status.DRAFT,
        )

    @staticmethod
    @transaction.atomic
    def update_product(*, product: Product, data: dict[str, Any]) -> Product:
        """Update mutable product fields for the owner vendor."""
        for field in ("name", "description", "price", "stock", "status"):
            if field in data:
                setattr(product, field, data[field])

        product.save()
        return product

    @staticmethod
    @transaction.atomic
    def delete_product(*, product: Product) -> None:
        """Soft-delete a product."""
        product.delete()

    @staticmethod
    def get_vendor_products(*, vendor_profile: Vendor):
        """Return products owned by a vendor profile."""
        return Product.objects.filter(vendor=vendor_profile).order_by("-created_at")

    @staticmethod
    def validate_product_ownership(*, product: Product, vendor_profile: Vendor) -> None:
        """Ensure the product belongs to the acting vendor."""
        if product.vendor_id != vendor_profile.id:
            raise PermissionError("You do not own this product")