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
        if self.quantity > self.product.stock:
            raise ValidationError(
                f"No puedes pedir {self.quantity} unidades. Solo quedan {self.product.stock} en stock.")
    def save(self, *args, **kwargs):
        #  Congelar el precio si es la primera vez que se guarda
        if self._state.adding:
        # Aquí 'congelamos' el precio del momento de la compra
            self.unit_price = self.product.price
        # 2. Calcular total usando el precio congelado
        self.total = (self.unit_price * self.quantity)
        # Asignación automática del vendor
        if self.product:
            self.vendor = self.product.vendor
        # Lógica de actualización de stock por estado
        if self.pk:
            # Obtenemos la orden como está actualmente en la BD antes de guardar
            old_instance = Order.objects.get(pk=self.pk)
            # Si cambia a CONFIRMED y antes no lo estaba
            if self.status == self.Status.CONFIRMED and old_instance.status != self.Status.CONFIRMED:
                with transaction.atomic():
                    # Doble validación de seguridad antes de restar
                    if self.product.stock >= self.quantity:
                        self.product.stock -= self.quantity
                        self.product.save(update_fields=['stock'])
                    else:
                        raise ValidationError(f"No hay stock suficiente para confirmar (Disponible: {self.product.stock})")
        else:
            # Si la orden se crea directamente como CONFIRMED
            if self.status == self.Status.CONFIRMED:
                with transaction.atomic():
                    # Doble validación de seguridad antes de restar
                    if self.product.stock >= self.quantity:
                        self.product.stock -= self.quantity
                        self.product.save(update_fields=['stock'])
                    else:
                        raise ValidationError(f"No hay stock suficiente para confirmar (Disponible: {self.product.stock})")
        # Validar todo
        self.full_clean()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"Pedido {self.id} - {self.product.name}"
