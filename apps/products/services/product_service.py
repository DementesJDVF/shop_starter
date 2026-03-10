"""Service layer for product business logic."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.products.models import Product
from apps.users.constants import UserRoles
from apps.vendors.models import Vendor


class ProductService:
    """Encapsulates product-related business rules."""

    @staticmethod
    def validate_vendor_can_manage_products(*, user: Any) -> Vendor:
        """Validate that the authenticated user is an active vendor."""
        if not getattr(user, "is_authenticated", False):
            raise PermissionDenied("Authentication required")

        if user.role != UserRoles.VENDEDOR:
            raise PermissionDenied("Only vendor users can manage products")

        try:
            vendor_profile = user.vendor
        except Vendor.DoesNotExist as exc:
            raise ValidationError("Vendor profile not found") from exc

        if vendor_profile.status != Vendor.Status.ACTIVE:
            raise ValidationError("Vendor profile must be active")

        return vendor_profile

    @staticmethod
    def _validate_create_payload(*, data: dict[str, Any]) -> None:
        """Run domain-level validations for product creation/update."""
        if Decimal(str(data["price"])) <= 0:
            raise ValidationError("Product price must be greater than zero")

    @staticmethod
    @transaction.atomic
    def create_product(*, vendor_profile: Vendor, data: dict[str, Any]) -> Product:
        """Create a product owned by the given vendor profile."""
        ProductService._validate_create_payload(data=data)

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
        if product.is_deleted:
            raise ValidationError("Deleted products cannot be updated")

        ProductService._validate_create_payload(data=data)

        for field in ("name", "description", "price", "stock", "status"):
            if field in data:
                setattr(product, field, data[field])

        product.save()
        return product

    @staticmethod
    @transaction.atomic
    def delete_product(*, product_id: int, user: Any) -> None:
        """Soft-delete an owned product for an authenticated active vendor."""
        vendor_profile = ProductService.validate_vendor_can_manage_products(user=user)

        try:
            product = Product.objects.get(id=product_id, is_deleted=False)
        except Product.DoesNotExist as exc:
            raise NotFound("Product not found") from exc

        ProductService.validate_product_ownership(product=product, vendor_profile=vendor_profile)

        product.is_deleted = True
        product.save(update_fields=["is_deleted", "updated_at"])

    @staticmethod
    def get_vendor_products(*, vendor_profile: Vendor):
        """Return non-deleted products owned by a vendor profile."""
        return Product.objects.filter(vendor=vendor_profile, is_deleted=False).order_by("-created_at")

    @staticmethod
    def validate_product_ownership(*, product: Product, vendor_profile: Vendor) -> None:
        """Ensure the product belongs to the acting vendor."""
        if product.vendor_id != vendor_profile.id:
            raise PermissionDenied("You do not own this product")
