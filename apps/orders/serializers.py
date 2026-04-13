"""Serializers for orders endpoints."""
from rest_framework import serializers
from apps.products.models import Product
from apps.users.models import User
from apps.orders.models import Order
class OrderSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    product_name = serializers.CharField(source='product.name', read_only=True)
    client_name = serializers.CharField(source='client.username', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'client', 'client_name', 'vendor', 'vendor_name',
        'status', 'created_at', 'product', 'product_name', 
        'quantity', 'description']
        read_only_fields = ['vendor']
    def validate(self, data):
        product = data.get('product')
        quantity = data.get('quantity')
        if quantity > product.stock:
            raise serializers.ValidationError({
                "quantity": f"No puedes pedir {quantity} unidades. Solo quedan {product.stock} en stock."})
        return data