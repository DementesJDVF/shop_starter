import uuid

from django.db import models


class ModerationFlag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEWED = "REVIEWED", "Reviewed"
        DISMISSED = "DISMISSED", "Dismissed"

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="moderation_flags",
    )
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "moderation_flag"

    def __str__(self):
        return f"{self.product} - {self.status}"


class RejectedImage(models.Model):
    """Rastreo de imágenes rechazadas por el sistema de moderación IA."""

    class ReviewStatus(models.TextChoices):
        PENDING = "PENDING", "Pendiente revisión"
        REVIEWED = "REVIEWED", "Revisado por admin"
        APPROVED = "APPROVED", "Aprobado por admin"
        CONFIRMED_REJECTED = "CONFIRMED_REJECTED", "Rechazo confirmado"

    image = models.OneToOneField(
        "products.PImages",
        on_delete=models.CASCADE,
        related_name="rejected_record"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="rejected_images"
    )
    vendor = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name="rejected_product_images"
    )

    # Datos del análisis de IA
    ai_reason = models.TextField()
    ai_confidence = models.FloatField(default=0.0)

    # Revisión del admin
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_rejected_images"
    )
    admin_notes = models.TextField(blank=True)

    rejected_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "moderation_rejected_image"
        ordering = ["-rejected_at"]
        indexes = [
            models.Index(fields=["review_status", "-rejected_at"]),
            models.Index(fields=["vendor"]),
        ]

    def __str__(self):
        return f"Imagen rechazada: {self.product} - {self.review_status}"


class ProductReview(models.Model):
    """Producto completo enviado a revisión por imágenes inapropiadas."""

    class ReviewStatus(models.TextChoices):
        PENDING = "PENDING", "Pendiente revisión"
        REVIEWED = "REVIEWED", "Revisado"
        APPROVED_PRODUCT = "APPROVED_PRODUCT", "Producto aprobado"
        REJECTED_PRODUCT = "REJECTED_PRODUCT", "Producto rechazado completamente"
        APPROVED_IMAGES = "APPROVED_IMAGES", "Solo imágenes aprobadas"

    product = models.OneToOneField(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="review_record"
    )
    vendor = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name="products_in_review"
    )

    # Imágenes que dispararon la revisión
    rejected_images_count = models.PositiveIntegerField(default=0)

    # Decisión del admin
    review_status = models.CharField(
        max_length=30,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_products"
    )

    # Notas detalladas del admin
    admin_notes = models.TextField(
        blank=True,
        help_text="Razones por las que se rechaza/aprueba el producto completo"
    )

    # Hallazgos del admin
    content_issues = models.JSONField(
        null=True,
        blank=True,
        help_text="{'name': bool, 'description': bool, 'images': bool, ...}"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "moderation_product_review"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["review_status", "-created_at"]),
            models.Index(fields=["vendor"]),
        ]

    def __str__(self):
        return f"Revisión de {self.product.name} - {self.review_status}"