from django.conf import settings
import uuid
from django.db import models
from apps.core.models import BaseModel
from django.conf import settings

class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="location", # Singular, porque ahora solo es UNA
        db_column="user_id"      # O el nombre que prefieras en DB
    )
    latitude = models.DecimalField(max_digits=18, decimal_places=15)
    longitude = models.DecimalField(max_digits=18, decimal_places=15)
    timestamp = models.DateTimeField(auto_now_add=True)
    description =models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        db_table = "geo_location"
    def __str__(self):
        return f"{self.user} @ ({self.latitude}, {self.longitude})"
class LImages(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Django crea el 'id' SERIAL/BIGSERIAL automáticamente, no hace falta declararlo.
    # products_product_id integer NOT NULL + FK
    # 'Product' es el nombre del modelo al que hace referencia.
    # db_column es vital para que coincida con el nombre exacto en tu SQL.
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        db_column="location_id",
        related_name="images",)
    # url_image TEXT NOT NULL
    url_image = models.ImageField(upload_to="locations/images/")
    # is_main boolean DEFAULT false
    is_main = models.BooleanField(default=False)
    # date_created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    date_created = models.DateTimeField(auto_now_add=True)
    class Meta:
        # Esto le dice a Django que use exactamente el nombre de tu script
        db_table = "locations_images"
    def __str__(self):
        return f"Imagen de {self.location} - Principal: {self.is_main}"
