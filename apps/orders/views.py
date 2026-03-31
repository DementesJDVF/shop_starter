from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.orders.services.order_service import OrderService
from .serializers import OrderCreateSerializer


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # Validar rol cliente
        if request.user.role != "CLIENT":
            return Response(
                {"error": "Solo clientes pueden crear pedidos"},
                status=403
            )

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = OrderService.create_order(
                client=request.user,
                items_data=serializer.validated_data["items"]
            )

            return Response({
                "order_id": str(order.id),
                "status": order.status,
                "total": order.total
            }, status=201)

        except ValueError as e:
            return Response({"error": str(e)}, status=400)