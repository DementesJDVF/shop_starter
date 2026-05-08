from rest_framework import viewsets, status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order
from apps.products.models import Product
from .serializers import OrderSerializer
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError as DjangoValidationError

import logging
logger = logging.getLogger(__name__)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'user'
    
    # 🔴 SEGURIDAD CRÍTICA: Bloquear manipulación directa
    # Solo permitimos GET (leer), POST (crear y acciones custom)
    # Bloqueamos PUT, PATCH, DELETE para que el status no sea inyectable
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        
        qs = Order.objects.select_related('client', 'vendor', 'product')
        if user.role == 'ADMIN':
            return qs.order_by('-created_at')
        if user.role == 'VENDEDOR':
            return qs.filter(vendor=user).order_by('-created_at')
        return qs.filter(client=user).order_by('-created_at')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # 1. Obtener producto y validar existencia
        product_id = request.data.get('product')
        try:
            product_obj = Product.objects.get(id=product_id)
        except (Product.DoesNotExist, ValidationError):
            return Response({"error": "Producto no encontrado."}, status=404)

        # 2. Idempotencia (Evitar duplicados en 1 min)
        if Order.objects.filter(
            client=request.user, 
            product=product_obj, 
            status=Order.Status.RESERVED,
            created_at__gte=timezone.now() - timedelta(minutes=1)
        ).exists():
            return Response({"error": "Ya tienes una reserva reciente."}, status=409)

        # 3. Validar con el Serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 4. Guardar inyectando los datos del producto
        order = serializer.save(
            client=request.user,
            vendor=product_obj.vendor, # Lo sacamos del objeto que ya buscamos
            unit_price=product_obj.price,
            status=Order.Status.RESERVED
        )

        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='mark-as-paid')
    def mark_as_paid(self, request, pk=None):
        """Botón del Vendedor: Confirma el pago de forma idempotente y SEGURA."""
        # select_for_update() asegura que si llegan dos clicks simultáneos, se bloquee la fila
        with transaction.atomic():
            # IDEMPOTENCIA a nivel de DB
            order = Order.objects.select_for_update().get(pk=pk)
            
            # 🔴 SEGURIDAD: Solo el Vendedor DUEÑO del producto puede confirmar
            if order.vendor != request.user and not request.user.is_superuser:
                return Response({"error": "No tienes permiso para confirmar pagos de esta orden (No eres el vendedor)."}, status=status.HTTP_403_FORBIDDEN)
                
            # Si ya está pagado, devolvemos 200 sin error para ser idempotentes
            if order.status == Order.Status.PAID:
                return Response({"message": "La orden ya estaba pagada."}, status=status.HTTP_200_OK)
                
            if order.status != Order.Status.RESERVED:
                return Response({"error": f"Transición inválida. No se puede pagar una orden en estado {order.status}."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                order.status = Order.Status.PAID
                order.save()
                logger.info(f"[AUDIT] Pago confirmado para orden {order.id} por el vendedor {request.user.username}.")
                return Response({"message": "Pago confirmado exitosamente."})
            except DjangoValidationError as e:
                return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
            
    @action(detail=True, methods=['post'], url_path='notify-payment')
    def mark_as_paid_client(self, request, pk=None):
        """Botón del Cliente: Notifica que ya pagó."""
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=pk)
            
            if order.client != request.user:
                return Response({"error": "Solo el comprador puede notificar el pago."}, status=status.HTTP_403_FORBIDDEN)
            
            if order.status != Order.Status.RESERVED:
                return Response({"error": "Solo se pueden pagar órdenes reservadas."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Aquí podríamos cambiar a un estado intermedio 'PAYMENT_SENT' si existiera,
            # pero el usuario pide que sea 'ya pago'. Para simplificar y no cambiar el modelo
            # (que es complejo), vamos a dejarlo en RESERVED pero añadir un flag o nota?
            # En realidad, el usuario dijo "el cliente tiene una opcion de ya pago".
            # Vamos a marcarlo como PAID y que el vendedor lo valide.
            try:
                order.payment_notified = True
                order.save()
                logger.info(f"[AUDIT] Cliente {request.user.username} notifica pago para orden {order.id}.")
                return Response({"message": "Notificación de pago enviada al vendedor."})
            except DjangoValidationError as e:
                return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela la orden y libera el stock/producto de forma transaccional."""
        with transaction.atomic():
            # Bloqueo de fila para evitar que alguien pague mientras cancelamos
            order = Order.objects.select_for_update().get(pk=pk)
            
            # Solo el dueño o el vendedor pueden cancelar
            if order.client != request.user and order.vendor != request.user and request.user.role != 'ADMIN' and not request.user.is_superuser:
                 return Response({"error": "No tienes permiso para cancelar esta orden."}, status=status.HTTP_403_FORBIDDEN)

            if order.status == Order.Status.PAID:
                return Response({"error": "No se puede cancelar una orden ya pagada."}, status=status.HTTP_400_BAD_REQUEST)
            
            if order.status == Order.Status.CANCELLED:
                return Response({"message": "La orden ya está cancelada."}, status=status.HTTP_200_OK)

            try:
                order.status = Order.Status.CANCELLED
                order.save()
                logger.info(f"[AUDIT] Orden {order.id} cancelada por {request.user.username}. Stock liberado.")
                return Response({"message": "Orden cancelada. El producto ha sido liberado."})
            except DjangoValidationError as e:
                return Response({"error": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
