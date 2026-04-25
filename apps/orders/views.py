from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from decimal import Decimal
from .models import Order
from apps.products.models import Product

from .serializers import OrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
            
        qs = Order.objects.select_related('client', 'vendor', 'product')
        
        if user.role == 'ADMIN':
            return qs.order_by('-created_at')
        if user.role == 'VENDEDOR':
            return qs.filter(vendor=user).order_by('-created_at')
        return qs.filter(client=user).order_by('-created_at')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # 1. Validación estricta a través del API Serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_instance = serializer.validated_data.get('product')
        quantity = serializer.validated_data.get('quantity', 1)
        
        # 2. Atrapar el objeto real en la BD con seguro anti-condición de carrera
        try:
            product = Product.objects.select_for_update().get(id=product_instance.id)
        except Product.DoesNotExist:
            return Response({"error": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if product.status != Product.ProductStatus.ACTIVE:
            return Response({"error": "El producto no está disponible para reserva."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Comprobación estricta de concurrencia después de asegurar el recurso
        if hasattr(product, 'stock') and quantity > product.stock:
            return Response({"error": f"No stock suficiente. Quedan {product.stock} unidades."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Crear el pedido
        order = Order.objects.create(
            client=self.request.user,
            vendor=product.vendor,
            product=product,
            quantity=quantity,
            unit_price=product.price,
            total=product.price * quantity
        )

        # 4. Ajustar inventarios y estado
        if hasattr(product, 'stock'):
            product.stock -= quantity
            if product.stock <= 0:
                product.status = Product.ProductStatus.RESERVED
        else:
            product.status = Product.ProductStatus.RESERVED
            
        product.save()

        # Respuesta con payload serializado
        out_serializer = self.get_serializer(order)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            return Response({"error": "Solo se pueden cancelar reservas pendientes."}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = Order.Status.CANCELLED
        order.save()

        # Penalización si el vendedor marca que el cliente no vino ('cancel' desde el panel del vendedor)
        if request.user.role == 'VENDEDOR' and order.vendor == request.user:
            client = order.client
            client.reputation_score = max(Decimal('0.0'), client.reputation_score - Decimal('1.0'))
            client.save()

        # Liberar el producto
        if order.product:
            product = Product.objects.select_for_update().get(id=order.product.id)
            product.status = Product.ProductStatus.ACTIVE
            product.save()

        return Response({"status": "Reserva cancelada, producto liberado y penalización aplicada si corresponde."})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def complete(self, request, pk=None):
        order = self.get_object()
        
        if order.vendor != request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Solo el vendedor puede completar esta orden.")
            
        if order.status != Order.Status.PENDING:
            return Response({"error": "Solo se pueden completar reservas pendientes."}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = Order.Status.COMPLETED
        order.save()

        # Recompensa por completar la transaccion exitosamente
        from django.db.models import F
        
        # Omitimos MIN para no complicar F() con Case/When si no es estrictamente necesario 
        # (O podríamos usar post-save signal, pero por paridad transaccional es más rápido)
        # Vamos a dejar F() simple y un clamp posterior si es necesario, o simplemente sumarlo atómicamente
        Order.objects.filter(id=order.id).update(status=Order.Status.COMPLETED)
        
        client = order.client
        vendor = order.vendor
        
        # Operaciones Atómicas Sólidas
        client.__class__.objects.filter(id=client.id).update(reputation_score=F('reputation_score') + Decimal('0.1'))
        vendor.__class__.objects.filter(id=vendor.id).update(reputation_score=F('reputation_score') + Decimal('0.1'))

        return Response({"status": "Venta completada y reputación actualizada atómicamente."})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def report_vendor(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            return Response({"error": "Solo se pueden reportar reservas pendientes."}, status=status.HTTP_400_BAD_REQUEST)
        
        # El cliente reporta que el vendedor vendió el producto a otro
        Order.objects.filter(id=order.id).update(status=Order.Status.CANCELLED)

        # Penalización fuerte al vendedor - Atomic SQL Update
        from django.db.models import F
        vendor = order.vendor
        vendor.__class__.objects.filter(id=vendor.id).update(reputation_score=F('reputation_score') - Decimal('1.5'))

        # Liberar el producto
        if order.product:
            product = order.product
            product.status = Product.ProductStatus.ACTIVE
            product.save()

        return Response({"status": "Reporte enviado. Se ha castigado atómicamente al vendedor."})
