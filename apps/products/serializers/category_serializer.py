"""Serializers for category endpoints."""

from rest_framework import serializers

from apps.products.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Read/write serializer for product categories."""

    class Meta:
        model = Category
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value: str) -> str:
        """Normalize category name to avoid duplicated values by case/spacing."""
        normalized_name = " ".join(value.split())
        if not normalized_name:
            raise serializers.ValidationError("El nombre de la categoría no puede estar vacío")
        return normalized_name