import uuid
from django.conf import settings
from django.db import models
from apps.core.models import BaseModel
from apps.products.models import Product
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import transaction
from django.utils import timezone

class Order(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        RESERVED = "RESERVED", "Reservado"
        PAID = "PAID", "Pagado"
        CANCELLED = "CANCELLED", "Cancelado"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders_as_client",
        null=True,
        blank=True)
    
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders_as_vendor",
        null=True,
        blank=True,
        editable=False)
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        related_name="orders", 
        null=True)
    
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING)
    
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, editable=False)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    payment_notified = models.BooleanField(default=False) # 🔥 Flag para que el vendedor sepa que el cliente ya reportó el pago
    expires_at = models.DateTimeField(null=True, blank=True) # 🔥 Límite para pagar antes de liberar stock

    class Meta:
        db_table = "orders_order"

    def clean(self):
        """Validaciones de integridad antes de guardar."""
        if not self.product:
            raise ValidationError("La orden debe tener un producto.")
        
        # Validar que el producto esté disponible (stock como booleano gestionado por el vendedor)
        if self._state.adding and not self.product.stock:
            raise ValidationError("Este producto no tiene disponibilidad en este momento.")

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        # 1. Congelar datos económicos
        if is_new and self.product:
            # BLOQUEO DE SEGURIDAD: Solo se pueden comprar productos aprobados y disponibles
            if self.product.status not in [Product.ProductStatus.AVAILABLE, Product.ProductStatus.RESERVED, Product.ProductStatus.SOLD]:
                raise ValidationError(f"Este producto no está disponible para la venta (Estado: {self.product.status}).")
            
            self.unit_price = self.product.price
            self.vendor = self.product.vendor
        
        if self.unit_price:
            self.total = self.unit_price * self.quantity

        # 2. Lógica Transaccional de Estados (Consistencia Global)
        with transaction.atomic():
            # Bloquear el producto para evitar Race Conditions (SELECT FOR UPDATE)
            product = Product.objects.select_for_update().get(pk=self.product.pk)

            if is_new:
                # Al crear una orden, nace como RESERVADA.
                # El stock NO se decrementa: es gestionado exclusivamente por el vendedor
                # desde Gestión de Productos.
                if not product.stock:
                    raise ValidationError("Este producto no tiene disponibilidad en este momento.")
                
                # Configurar expiración (15 minutos para pagar)
                self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
                self.status = self.Status.RESERVED
                
                # Marcar el producto como RESERVADO
                product.status = Product.ProductStatus.RESERVED
                product.save()
            else:
                # Si la orden ya existe, evaluamos cambios de estado (Pago/Cancelación)
                old_order = Order.objects.select_for_update().get(pk=self.pk)
                
                # De RESERVADO a PAGADO: marcar el producto como SOLD
                if self.status == self.Status.PAID and old_order.status != self.Status.PAID:
                    product.status = Product.ProductStatus.SOLD
                    product.save()

                # CANCELACIÓN: restaurar disponibilidad del producto sin tocar el stock
                elif self.status == self.Status.CANCELLED and old_order.status != self.Status.CANCELLED:
                    product.status = Product.ProductStatus.AVAILABLE
                    product.save()

            super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.id} - {self.product.name} ({self.status})"
