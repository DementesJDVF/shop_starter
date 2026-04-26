import uuid
from django.conf import settings
from django.db import models

from apps.core.models import BaseModel
from apps.products.models import Product
from apps.geo.models import Location
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import transaction
class Order(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
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
        related_name="orders", # Mejorado: un producto tiene muchas "orders"
        null=True)
    location = models.ForeignKey(
        Location, 
        on_delete=models.CASCADE, 
        related_name="orders_at_location",
        null=True)
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING)
    quantity = models.PositiveIntegerField(default=1,validators=[MinValueValidator(1)]) # Antes era 'stock'
    description = models.CharField(max_length=255, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, editable=False)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False) # Editable=False porque es automático
    class Meta:
        db_table = "orders_order"
    def clean(self):
        """Validación: No pedir más de lo que hay en inventario"""
        if self.product and self.quantity > self.product.stock:
            raise ValidationError(
                f"No puedes pedir {self.quantity} unidades. Solo quedan {self.product.stock} en stock.")

    def _handle_stock_restoration(self):
        """Helper to restore stock atomically when an order is cancelled."""
        with transaction.atomic():
            self.product.refresh_from_db()
            self.product.stock += self.quantity
            self.product.save(update_fields=['stock'])

    def _handle_stock_reduction(self):
        """Helper to reduce stock atomically."""
        with transaction.atomic():
            # Refrescar instancia de producto para evitar datos obsoletos
            self.product.refresh_from_db()
            if self.product.stock >= self.quantity:
                self.product.stock -= self.quantity
                self.product.save(update_fields=['stock'])
            else:
                raise ValidationError(f"No hay stock suficiente para confirmar (Disponible: {self.product.stock})")

    def save(self, *args, **kwargs):
        # 1. Asignación automática del vendor y congelación de precio
        if self.product:
            if self._state.adding:
                self.unit_price = self.product.price
            self.vendor = self.product.vendor
        
        # 2. Calcular total usando el precio congelado
        if self.unit_price:
            self.total = (self.unit_price * self.quantity)

        # 3. Lógica de actualización de stock por estado
        if not self._state.adding:
            try:
                old_instance = Order.objects.get(pk=self.pk)
                # Caso A: Confirmación (Ya se redujo al crear, así que solo si cambia de algo no-confirmado a confirmado)
                # Pero espera: Si ya se redujo al crear (como PENDING), no debemos reducirlo de nuevo.
                # En este sistema, CUALQUIER orden activa (PENDING, CONFIRMED, COMPLETED) consume stock.
                
                # Caso B: Cancelación de una orden que consumía stock (Restaura Stock)
                if self.status == self.Status.CANCELLED and old_instance.status != self.Status.CANCELLED:
                    self._handle_stock_restoration()
                
                # Caso C: Reactivación de una orden cancelada (Reduce Stock)
                elif self.status != self.Status.CANCELLED and old_instance.status == self.Status.CANCELLED:
                    self._handle_stock_reduction()
                    
            except Order.DoesNotExist:
                if self.status != self.Status.CANCELLED:
                    self._handle_stock_reduction()
        else:
            # Al CREAR: Si la orden no nace cancelada, reservamos el stock
            if self.status != self.Status.CANCELLED:
                self._handle_stock_reduction()

        # 4. Validar y Guardar
        if self.product:
            self.full_clean()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"Pedido {self.id} - {self.product.name}"
