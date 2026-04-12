"""Serializers for orders endpoints."""
from rest_framework import serializers
from apps.products.models import Product
from apps.geo.models import Location
from apps.orders.models import Order
class OrderSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.username', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all(), required=False)

    class Meta:
        model = Order
        fields = [
            'id', 'client', 'client_name', 'vendor', 'vendor_name', 
            'status', 'total', 'created_at', 'product', 'product_name', 
            'location', 'quantity', 'unit_price', 'shipping', 'description'
        ]
        read_only_fields = ['client', 'status', 'total', 'vendor', 'unit_price']
    def validate(self, data):
        product = data.get('product')
        quantity = data.get('quantity')
        if quantity > product.stock:
            raise serializers.ValidationError({
                "quantity": f"No puedes pedir {quantity} unidades. Solo quedan {product.stock} en stock."})
        return data