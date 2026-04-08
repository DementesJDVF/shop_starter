from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    def perform_create(self, serializer):
        serializer.save()
