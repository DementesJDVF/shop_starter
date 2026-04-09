"""Serializers for orders endpoints."""
from rest_framework import serializers
from apps.products.models import Product
from apps.geo.models import Location
from apps.orders.models import Order
class OrderSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    class Meta:
        model = Order
        fields = "__all__"
    def validate(self, data):
        product = data.get('product')
        quantity = data.get('quantity')
        if quantity > product.stock:
            raise serializers.ValidationError({
                "quantity": f"No puedes pedir {quantity} unidades. Solo quedan {product.stock} en stock."})
        return data