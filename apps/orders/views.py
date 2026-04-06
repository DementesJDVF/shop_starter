from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.orders.services.order_service import OrderService
from apps.orders.models import Order
from apps.users.constants import UserRoles
from .serializers import OrderCreateSerializer, OrderCreatedResponseSerializer, VendorOrderSerializer


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # Validar rol cliente
        if request.user.role != UserRoles.CUSTOMER:
            return Response(
                {"error": "Solo clientes pueden crear pedidos"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = OrderService.create_order(
                client=request.user,
                items_data=serializer.validated_data["items"]
            )

            return Response(
                OrderCreatedResponseSerializer(order).data,
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VendorOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != UserRoles.VENDOR:
            return Response(
                {"error": "Solo vendedores pueden consultar pedidos"},
                status=status.HTTP_403_FORBIDDEN
            )

        orders = Order.objects.filter(vendor__user=request.user).select_related("client")
        return Response(VendorOrderSerializer(orders, many=True).data, status=status.HTTP_200_OK)