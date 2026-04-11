import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator
from apps.orders.models import Order

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order, # Usa string si Product está en el mismo archivo o después
        on_delete=models.CASCADE,
        db_column="products_product_id",
        related_name="product_reviews",
        null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_comments",
        null=True)
    # Límite de 500 caracteres (Play Store)
    content = models.TextField(validators=[MaxLengthValidator(500)],blank=True)
    # DecimalField para permitir 1.0, 2.5, 5.0, etc.
    # max_digits=2 (un entero y un decimal)
    rate = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    class Meta:
        db_table = "products_comments"
        # Evita que un mismo usuario comente varias veces el mismo producto
        unique_together = ['order', 'user']
    # Esto es lo que "regresa" el modelo cuando lo ves en el Admin o consola
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rate}★)"
