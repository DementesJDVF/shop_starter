"""Models for product catalog."""
# import uuid
from django.db import models
from apps.core.models import BaseModel
from django.conf import settings
class Category(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(null=True, blank=True)
    emoji = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = "products_category"
    def __str__(self) -> str:
        return self.name
class Product(BaseModel):
    """Represents a product published by a vendor profile."""
    class ProductStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Approval"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        PAUSED = "PAUSED", "Paused"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Out of stock"
        REJECTED = "REJECTED", "Rejected"
        RESERVED = "RESERVED", "Reserved"

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Apunta dinámicamente a tu clase User personalizada
        on_delete=models.CASCADE,
        related_name="products",
        db_index=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="category",
        null=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.PENDING,
        db_index=True)
    rejection_reason = models.TextField(null=True, blank=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    class Meta:
        db_table = "products_product"
        indexes = [
            models.Index(fields=["vendor"], name="products_vendor_idx"),
            models.Index(fields=["status"], name="products_status_idx"),]
    def __str__(self) -> str:
        return self.name
class PImages(BaseModel):
    # Django crea el 'id' SERIAL/BIGSERIAL automáticamente, no hace falta declararlo.
    # products_product_id integer NOT NULL + FK
    # 'Product' es el nombre del modelo al que hace referencia.
    # db_column es vital para que coincida con el nombre exacto en tu SQL.
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column="products_product_id",
        related_name="images",)
    # url_image TEXT NOT NULL
    url_image = models.ImageField(upload_to="products/images/")
    # is_main boolean DEFAULT false
    is_main = models.BooleanField(default=False)
    # date_created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    date_created = models.DateTimeField(auto_now_add=True)
    class Meta:
        # Esto le dice a Django que use exactamente el nombre de tu script
        db_table = "products_images"
    def __str__(self):
        return f"Imagen de {self.product} - Principal: {self.is_main}"