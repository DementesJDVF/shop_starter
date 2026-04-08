from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order, OrderItem
from apps.products.models import Product

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price_at_purchase']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='client.username', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'client', 'client_name', 'vendor', 'vendor_name', 'status', 'total', 'items', 'created_at']
        read_only_fields = ['client', 'status', 'total', 'vendor']

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
        if user.role == 'VENDEDOR':
            return Order.objects.filter(vendor=user)
        return Order.objects.filter(client=user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Tomamos el primer item para simplificar la lógica de reserva 1-a-1 solicitada
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "Debe proporcionar un product_id."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.select_for_update().get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if product.status != Product.ProductStatus.ACTIVE:
            return Response({"error": "El producto no está disponible para reserva."}, status=status.HTTP_400_BAD_REQUEST)

        # Crear el pedido
        order = Order.objects.create(
            client=self.request.user,
            vendor=product.vendor,
            total=product.price
        )

        # Crear el item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price_at_purchase=product.price
        )

        # Cambiar estado del producto a RESERVADO
        product.status = Product.ProductStatus.RESERVED
        product.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
            client.reputation_score = max(0, client.reputation_score - 1.0)
            client.save()

        # Liberar el producto
        for item in order.items.all():
            product = item.product
            product.status = Product.ProductStatus.ACTIVE
            product.save()

        return Response({"status": "Reserva cancelada, producto liberado y penalización aplicada si corresponde."})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def complete(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            return Response({"error": "Solo se pueden completar reservas pendientes."}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = Order.Status.COMPLETED
        order.save()

        # Recompensa por completar la transacción exitosamente
        client = order.client
        vendor = order.vendor
        client.reputation_score = min(5.0, client.reputation_score + 0.1)
        vendor.reputation_score = min(5.0, vendor.reputation_score + 0.1)
        client.save()
        vendor.save()

        return Response({"status": "Venta completada y reputación actualizada."})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def report_vendor(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            return Response({"error": "Solo se pueden reportar reservas pendientes."}, status=status.HTTP_400_BAD_REQUEST)
        
        # El cliente reporta que el vendedor vendió el producto a otro
        order.status = Order.Status.CANCELLED
        order.save()

        # Penalización fuerte al vendedor
        vendor = order.vendor
        vendor.reputation_score = max(0, vendor.reputation_score - 1.5)
        vendor.save()

        # Liberar el producto (aunque supuestamente ya lo vendió, lo ponemos en ACTIVE para que el sistema sea consistente o el vendedor lo borre)
        for item in order.items.all():
            product = item.product
            product.status = Product.ProductStatus.ACTIVE
            product.save()

        return Response({"status": "Reporte enviado. Se ha llamado la atención al vendedor y se ha reducido su reputación."})
