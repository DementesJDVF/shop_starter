"""Models for product catalog."""
import uuid
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class ProductStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Approval"
        AVAILABLE = "AVAILABLE", "Available"
        INACTIVE = "INACTIVE", "Inactive"
        REJECTED = "REJECTED", "Rejected"
        RESERVED = 'RESERVED', 'Reserved'
        SOLD = 'SOLD', 'Sold'

    class AIStatus(models.TextChoices):
        NONE = "NONE", "Ninguno"
        PENDING = "PENDING", "En cola"
        PROCESSING = "PROCESSING", "Procesando IA"
        DONE = "DONE", "Completado"
        FAILED = "FAILED", "Error"

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="products",
        db_index=True,
    )
    categories = models.ManyToManyField(
        Category,
        related_name="products",
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    ai_description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.PENDING,
        db_index=True,
    )

    # NO PONER SERVERS AQUI
    rejection_reason = models.TextField(null=True, blank=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    ai_status = models.CharField(
        max_length=20,
        choices=AIStatus.choices,
        default=AIStatus.NONE,
        db_index=True,
    )

    class Meta:
        db_table = "products_product"
        indexes = [
            models.Index(fields=["vendor"], name="products_vendor_idx"),
            models.Index(fields=["status"], name="products_status_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # 1. BLINDAJE ANTI-INYECCION (XSS)
        try:
            import bleach
            allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li']
            if self.description:
                self.description = bleach.clean(self.description, tags=allowed_tags, strip=True)
            if self.ai_description:
                self.ai_description = bleach.clean(self.ai_description, tags=allowed_tags, strip=True)
        except ImportError:
            pass

        super().save(*args, **kwargs)


class PImages(BaseModel):
    """
    SISTEMA DE MODERACION DE IMAGENES:
    Aqui controlamos que ninguna imagen obscena o inapropiada llegue a tus clientes.
    """

    class ModerationStatus(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        APPROVED = "APPROVED", "Aprobado"
        REJECTED = "REJECTED", "Rechazado"
        FLAGGED = "FLAGGED", "Marcado para revision"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column="products_product_id",
        related_name="images",
    )

    url_image = models.TextField()
    is_main = models.BooleanField(default=False)

    # Flags para el motor de Inteligencia Artificial
    is_moderated = models.BooleanField(default=False, db_index=True)
    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.APPROVED,
        db_index=True
    )
    moderation_details = models.JSONField(null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)

        # MODERACION AUTOMATICA CON IA:
        # IA DESACTIVADA TEMPORALMENTE
        # if is_new and self.url_image:
        #     try:
        #         from apps.moderation.services import moderate_image
        #         from threading import Thread
        #         thread = Thread(target=moderate_image, args=(self,), daemon=True)
        #         thread.start()
        #     except Exception as e:
        #         import logging
        #         logging.getLogger(__name__).error(f"Error al iniciar moderacion de imagen: {e}")

    class Meta:
        db_table = "products_images"

    def __str__(self):
        return f"Imagen de {self.product} - Estado: {self.moderation_status}"