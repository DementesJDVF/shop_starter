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
        on_delete=models.CASCADE, 
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
            self.unit_price = self.product.price
            self.vendor = self.product.vendor
        
        if self.unit_price:
            self.total = self.unit_price * self.quantity

        # 2. Lógica Transaccional de Estados (Consistencia Global)
        with transaction.atomic():
            # Bloquear el producto para evitar Race Conditions
            product = Product.objects.select_for_update().get(pk=self.product.pk)

            if is_new:
                # Al nacer una orden, descontamos el stock inmediatamente (Reserva implícita)
                if product.stock < self.quantity:
                    raise ValidationError("El stock se agotó justo antes de procesar tu orden.")
                product.stock -= self.quantity
                
                # Si el stock llega a 0, ocultamos el producto
                if product.stock <= 0:
                    product.status = Product.ProductStatus.SOLD
                else:
                    product.status = Product.ProductStatus.RESERVED
                
                product.reserved_at = timezone.now()
                product.reserved_by = self.client
                product.save()
            else:
                # Si la orden ya existe, evaluamos cambios de estado
                old_order = Order.objects.get(pk=self.pk)
                
                # CASO: De Pendiente/Reservado a PAGADO
                if self.status == self.Status.PAID and old_order.status != self.Status.PAID:
                    # El stock ya se descontó al crear, así que solo confirmamos el fin del ciclo
                    if product.stock <= 0:
                        product.status = Product.ProductStatus.SOLD
                    product.reserved_at = None
                    product.reserved_by = None
                    product.save()

                # CASO: CANCELACIÓN (Restaurar Stock)
                elif self.status == self.Status.CANCELLED and old_order.status != self.Status.CANCELLED:
                    product.stock += self.quantity
                    product.status = Product.ProductStatus.ACTIVE
                    product.reserved_at = None
                    product.reserved_by = None
                    product.save()

            super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.id} - {self.product.name} ({self.status})"
