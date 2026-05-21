"""Serializers for orders endpoints."""
from rest_framework import serializers
from apps.products.models import Product
from apps.users.models import User
from apps.orders.models import Order

class OrderSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    client = serializers.PrimaryKeyRelatedField(read_only=True)
    vendor = serializers.PrimaryKeyRelatedField(source='product.vendor', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    client_name = serializers.CharField(source='client.username', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)
    vendor_phone = serializers.CharField(source='vendor.phone_number', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'client', 'client_name', 'vendor', 'vendor_name', 'vendor_phone',
            'status', 'created_at', 'product', 'product_name', 
            'quantity', 'unit_price', 'total', 'payment_notified'
        ]
        read_only_fields = ['vendor', 'unit_price', 'total']

    def validate(self, data):
        product = data.get('product')
        quantity = data.get('quantity')
        user = self.context['request'].user

        # Validar existencia de datos
        if not quantity or quantity <= 0:
            raise serializers.ValidationError({"quantity": "Cantidad no válida."})

        # Validar que el producto tenga disponibilidad (stock gestionado solo por el vendedor)
        if not product.stock:
            raise serializers.ValidationError({"product": "Este producto no está disponible en este momento."})
        
        # Bloqueo Anti-Fraude
        if product.vendor == user:
            raise serializers.ValidationError({"product": "No puedes comprar tus propios productos."})

        return data