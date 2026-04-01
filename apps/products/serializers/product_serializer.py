"""Serializers for product endpoints."""

from rest_framework import serializers

from apps.products.models import Category, Product


class ProductCreateSerializer(serializers.Serializer):
    """Serializer for product create/update payloads."""

    name = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField(required=False, min_value=0)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="category",
    )

    def validate_price(self, value):
        """Ensure product price is greater than zero."""
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0")
        return value


class ProductSerializer(serializers.ModelSerializer):
    """Read serializer for products."""

    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "category",
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
