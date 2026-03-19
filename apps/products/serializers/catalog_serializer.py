"""Serializer for public catalog products."""
from rest_framework import serializers
from apps.products.models import Product
class PublicProductSerializer(serializers.ModelSerializer):
    """Expose only public-facing fields for catalog listing."""
    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "status", "vendor", "created_at"]
        read_only_fields = fields
