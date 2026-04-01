"""Service layer for product business logic."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.products.models import Category, Product
from apps.users.constants import UserRoles
from apps.vendors.models import Vendor


class ProductService:
    """Encapsulates product-related business rules."""
    
    @staticmethod
    def list_active_categories():
        """Return active categories for catalog assignment."""
        return Category.objects.filter(is_active=True, is_deleted=False).order_by("name")

    @staticmethod
    @transaction.atomic
    def create_category(*, data: dict[str, Any]) -> Category:
        """Create a product category."""
        return Category.objects.create(**data)

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
        if "price" in data and Decimal(str(data["price"])) <= 0:
            raise ValidationError("Product price must be greater than zero")

    @staticmethod
    def validate_product_ownership(*, product: Product, vendor_profile: Vendor) -> None:
        """Ensure the product belongs to the acting vendor."""
        if product.vendor_id != vendor_profile.id:
            raise PermissionDenied("You do not own this product")

    @staticmethod
    def get_vendor_product_for_update(*, product_id: int, user: Any) -> tuple[Product, Vendor]:
        """Resolve and validate a vendor-owned product for update workflows."""
        vendor_profile = ProductService.validate_vendor_can_manage_products(user=user)

        try:
            product = Product.all_objects.get(id=product_id)
        except Product.DoesNotExist as exc:
            raise NotFound("Product not found") from exc

        ProductService.validate_product_ownership(product=product, vendor_profile=vendor_profile)

        if product.is_deleted:
            raise ValidationError("Deleted products cannot be updated")

        return product, vendor_profile

    @staticmethod
    @transaction.atomic
    def create_product(*, vendor_profile: Vendor, data: dict[str, Any]) -> Product:
        """Create a product owned by the given vendor profile."""
        ProductService._validate_create_payload(data=data)

        product = Product(
            vendor=vendor_profile,
            name=data["name"],
            description=data["description"],
            price=data["price"],
            stock=data.get("stock", 0),
        )
        product.status = ProductService.evaluate_product_status(product=product)
        product.save()
        return product

    @staticmethod
    def evaluate_product_status(*, product: Product) -> str:
        """Evaluate the product status based on business rules."""
        if product.is_deleted:
            return Product.ProductStatus.INACTIVE

        is_complete = bool(product.name and product.description and product.price)
        if is_complete:
            return Product.ProductStatus.ACTIVE

        return Product.ProductStatus.DRAFT

    @staticmethod
    @transaction.atomic
    def update_product(*, product_id: int, user: Any, data: dict[str, Any]) -> Product:
        """Update mutable product fields for the owner vendor."""
        product, _ = ProductService.get_vendor_product_for_update(product_id=product_id, user=user)

        ProductService._validate_create_payload(data=data)

        for field in ("name", "description", "price", "stock"):
            if field in data:
                setattr(product, field, data[field])

        product.status = ProductService.evaluate_product_status(product=product)
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
        product.status = Product.ProductStatus.INACTIVE
        product.save(update_fields=["is_deleted", "status", "updated_at"])

    @staticmethod
    def get_vendor_products(*, vendor_profile: Vendor):
        """Return non-deleted products owned by a vendor profile."""
        return Product.objects.filter(vendor=vendor_profile, is_deleted=False).order_by("-created_at")

    @staticmethod
    def get_public_catalog():
        """Return publicly visible catalog products with optimized query."""
        return (
            Product.objects.select_related("vendor")
            .filter(
                status=Product.ProductStatus.ACTIVE,
                is_deleted=False,
                vendor__status=Vendor.Status.ACTIVE,
                vendor__user__is_active=True,
            )
            .order_by("-created_at")
        )
