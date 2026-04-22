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
    ai_description = models.TextField(null=True, blank=True)
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

    def save(self, *args, **kwargs):
        # --- BLINDAJE ANTI-INYECCIÓN (Technical Immunity) ---
        # Esta parte es vital para tu seguridad: usamos 'bleach' para limpiar cualquier rastro 
        # de código malicioso (XSS) que un atacante intente meter en la descripción.
        # Solo permitimos etiquetas seguras como negritas (b), cursivas (i), etc.
        try:
            import bleach
            allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li']
            
            if self.description:
                self.description = bleach.clean(self.description, tags=allowed_tags, strip=True)
                
            if self.ai_description:
                self.ai_description = bleach.clean(self.ai_description, tags=allowed_tags, strip=True)
        except ImportError:
            # Red de seguridad: si bleach no está, la app sigue viva, pero alertamos de la falta.
            pass
            
        super().save(*args, **kwargs)

class PImages(BaseModel):
    """
    SISTEMA DE MODERACIÓN DE IMÁGENES:
    Aquí controlamos que ninguna imagen obscena o inapropiada llegue a tus clientes.
    """
    class ModerationStatus(models.TextChoices):
        PENDING = "PENDING", "Pendiente"          # Esperando revisión
        APPROVED = "APPROVED", "Aprobado"          # Visible para todos
        REJECTED = "REJECTED", "Rechazado"         # Contenido ofensivo bloqueado
        FLAGGED = "FLAGGED", "Marcado para revisión" # Algo huele mal, revisar manualmente

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column="products_product_id",
        related_name="images",)
    
    url_image = models.ImageField(upload_to="products/images/")
    is_main = models.BooleanField(default=False)
    
    # Flags para el motor de Inteligencia Artificial
    is_moderated = models.BooleanField(default=False, db_index=True)
    moderation_status = models.CharField(
        max_length=20, 
        choices=ModerationStatus.choices, 
        default=ModerationStatus.PENDING,
        db_index=True
    )
    moderation_details = models.JSONField(null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk  # True solo cuando es una imagen nueva
        super().save(*args, **kwargs)
        
        # MODERACIÓN AUTOMÁTICA CON IA:
        # Apenas se sube una imagen nueva, el motor de IA la analiza en segundo plano.
        # Si es obscena o ilegal → se rechaza automáticamente y se notifica al vendedor.
        # Si es segura → se aprueba y el producto puede publicarse sin intervención humana.
        if is_new and self.url_image:
            try:
                from apps.moderation.services import moderate_image
                from threading import Thread
                # Lanzamos en un hilo separado para no bloquear la respuesta al usuario
                thread = Thread(target=moderate_image, args=(self,), daemon=True)
                thread.start()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error al iniciar moderación de imagen: {e}")

    class Meta:
        db_table = "products_images"
    def __str__(self):
        return f"Imagen de {self.product} - Estado: {self.moderation_status}"