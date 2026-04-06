from rest_framework import serializers

from apps.products.models import Product
from apps.products.models import Category


class ProductCreateSerializer(serializers.Serializer):

    name = serializers.CharField(max_length=255)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(is_deleted=False, is_active=True))
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField(required=False, min_value=0)

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0")
        return value


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "name",
            "category",
            "description",
            "price",
            "stock",
            "status",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "vendor", "status", "created_at", "updated_at", "is_deleted"]
