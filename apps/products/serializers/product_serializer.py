"""Serializers for product endpoints."""

from rest_framework import serializers

from apps.products.models import Product
from apps.products.services.product_service import ProductService


class ProductCreateSerializer(serializers.Serializer):
    """Serializer for product create/update payloads.

    This serializer centralizes vendor role validation for create flows to keep
    views thin and aligned with clean architecture boundaries.
    """

    name = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField(required=False, min_value=0)

    def validate_price(self, value):
        """Ensure product price is greater than zero."""
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0")
        return value

    def validate(self, attrs):
        """Validate acting user is vendor (role-based) before create."""
        request = self.context.get("request")
        if request and self.instance is None:
            # Raises PermissionDenied/ValidationError when role/profile is invalid.
            ProductService.validate_vendor_can_manage_products(user=request.user)
        return attrs

    def create(self, validated_data):
        """Create product by resolving vendor profile from authenticated user."""
        request = self.context["request"]
        vendor_profile = ProductService.validate_vendor_can_manage_products(user=request.user)
        return ProductService.create_product(vendor_profile=vendor_profile, data=validated_data)


class ProductSerializer(serializers.ModelSerializer):
    """Read serializer for products."""

    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "name",
            "description",
            "price",
            "stock",
            "status",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "vendor", "status", "created_at", "updated_at", "is_deleted"]