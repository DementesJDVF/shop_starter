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
        on_delete=models.CASCADE,
        related_name="orders_as_client",
        null=True,
        blank=True)
    
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
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

    class Meta:
        db_table = "orders_order"

    def clean(self):
        """Validaciones de integridad antes de guardar."""
        if not self.product:
            raise ValidationError("La orden debe tener un producto.")
        
        # Al crear, validar que haya stock físico
        if self._state.adding and self.quantity > self.product.stock:
             raise ValidationError(f"Stock insuficiente. Disponible: {self.product.stock}")

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        # 1. Congelar datos económicos
        if is_new and self.product:
            # BLOQUEO DE SEGURIDAD: Solo se pueden comprar productos aprobados y disponibles
            if self.product.status != Product.ProductStatus.AVAILABLE:
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
                # Al crear una orden, validamos y descontamos el stock
                if product.stock < self.quantity:
                    raise ValidationError("Stock insuficiente para procesar la orden.")
                
                product.stock -= self.quantity
                
                # El estado del producto solo cambia a SOLD si el stock llega a 0
                if product.stock <= 0:
                    product.status = Product.ProductStatus.SOLD
                # IMPORTANTE: Ya NO cambiamos a RESERVED si hay más stock,
                # para que el producto siga siendo visible para otros clientes.
                
                product.reserved_at = timezone.now()
                product.reserved_by = self.client
                product.save()
            else:
                # Si la orden ya existe, evaluamos cambios de estado (Pago/Cancelación)
                old_order = Order.objects.get(pk=self.pk)
                
                # De Pendiente a PAGADO
                if self.status == self.Status.PAID and old_order.status != self.Status.PAID:
                    if product.stock <= 0:
                        product.status = Product.ProductStatus.SOLD
                    product.reserved_at = None
                    product.reserved_by = None
                    product.save()

                # CANCELACIÓN (Liberar Stock)
                elif self.status == self.Status.CANCELLED and old_order.status != self.Status.CANCELLED:
                    product.stock += self.quantity
                    product.status = Product.ProductStatus.AVAILABLE
                    product.reserved_at = None
                    product.reserved_by = None
                    product.save()

            super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.id} - {self.product.name} ({self.status})"
