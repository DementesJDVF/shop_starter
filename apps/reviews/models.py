import uuid
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Quitamos null=True: una reseña DEBE tener autor y destino
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_reviews",
        null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_reviews",
        null=True)
    # Si usas TextField, el MaxLengthValidator funciona,
    # pero a nivel de DB un CharField(max_length=500) es más eficiente para búsquedas.
    content = models.TextField(validators=[MaxLengthValidator(500)], blank=True)
    rate = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        # Default en 5.0 es buena práctica para que no sea nulo
        default=5.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Para saber CUÁNDO se editó
    is_edited = models.BooleanField(default=False)
    class Meta:
        db_table = "products_comments"
        constraints = [
            # Evita duplicados y es más moderno que unique_together
            models.UniqueConstraint(fields=['vendor', 'user'], name='unique_vendor_user_review')]
    def clean(self):
        # Validación extra: ¡Que un vendedor no se califique a sí mismo!
        if self.user == self.vendor:
            raise ValidationError("No puedes escribir una reseña sobre ti mismo.")
    def save(self, *args, **kwargs):
        # Lógica para marcar como editado automáticamente
        if not self._state.adding: # Si el objeto ya existe y se está guardando de nuevo
            self.is_edited = True
        self.full_clean()
        super().save(*args, **kwargs)
    def __str__(self):
        # Usamos .get_username() o manejamos posibles nulos por seguridad
        return f"{self.user} -> {self.vendor} ({self.rate}★)"