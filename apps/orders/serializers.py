from rest_framework import serializers
 
from apps.orders.models import Order

 
class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
 
 
class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True)


class OrderCreatedResponseSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Order
        fields = ["order_id", "status", "total"]


class VendorOrderSerializer(serializers.ModelSerializer):
    client_id = serializers.UUIDField(source="client.id", read_only=True)
    client_email = serializers.EmailField(source="client.email", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "total", "client_id", "client_email", "created_at"]