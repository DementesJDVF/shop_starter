from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order
from apps.products.models import Product
from .serializers import OrderSerializer
from django.utils import timezone
from datetime import timedelta

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # SRE: Limpieza automática de reservas expiradas al consultar (Timeout Real)
        self._cleanup_expired_reservations()

        qs = Order.objects.select_related('client', 'vendor', 'product')
        if user.role == 'ADMIN':
            return qs.order_by('-created_at')
        if user.role == 'VENDEDOR':
            return qs.filter(vendor=user).order_by('-created_at')
        return qs.filter(client=user).order_by('-created_at')

    def _cleanup_expired_reservations(self):
        """Lógica de SRE: Libera productos reservados hace más de 15 min."""
        timeout = timezone.now() - timedelta(minutes=15)
        expired_orders = Order.objects.filter(
            status=Order.Status.RESERVED,
            created_at__lt=timeout
        )
        for order in expired_orders:
            order.status = Order.Status.CANCELLED
            order.save()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Crea una orden y la pone en estado RESERVED automáticamente."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # El modelo Order.save() se encarga de la lógica atómica de stock y reserva
        order = serializer.save(
            client=self.request.user,
            status=Order.Status.RESERVED
        )
        
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='mark-as-paid')
    def mark_as_paid(self, request, pk=None):
        """Botón del Vendedor: Confirma el pago y marca el producto como VENDIDO."""
        order = self.get_object()
        
        if request.user.role != 'VENDEDOR' and not request.user.is_superuser:
            return Response({"error": "Solo el vendedor puede confirmar el pago."}, status=status.HTTP_403_FORBIDDEN)
            
        if order.status != Order.Status.RESERVED:
            return Response({"error": f"No se puede pagar una orden en estado {order.status}."}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            order.status = Order.Status.PAID
            order.save()
            
            # El modelo Order.save() ya marca el producto como SOLD si el stock es 0
            return Response({"message": "Pago confirmado. Producto marcado como Vendido/Fuera de catálogo."})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela la orden y libera el stock/producto."""
        order = self.get_object()
        
        # Solo el dueño o el vendedor pueden cancelar
        if order.client != request.user and order.vendor != request.user and request.user.role != 'ADMIN':
             return Response({"error": "No tienes permiso para cancelar esta orden."}, status=status.HTTP_403_FORBIDDEN)

        if order.status == Order.Status.PAID:
            return Response({"error": "No se puede cancelar una orden ya pagada."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = Order.Status.CANCELLED
        order.save()
        
        return Response({"message": "Orden cancelada. El producto ha sido liberado."})
