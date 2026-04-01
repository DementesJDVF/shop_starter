"""Serializer for public catalog products."""

from rest_framework import serializers

from apps.products.models import Product


class PublicProductSerializer(serializers.ModelSerializer):
    """Expose only public-facing fields for catalog listing."""
    category_name = serializers.CharField(source="category.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.user.business_name", read_only=True, default="")

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "status",
            "category_name",
            "vendor",
            "vendor_name",
            "created_at",
        ]
        read_only_fields = fields
