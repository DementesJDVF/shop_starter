from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .serializers import OrderCreateSerializer


class CreateOrderView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderCreateSerializer