from django.conf import settings
import uuid
from django.db import models
from django.conf import settings

class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="location", # Singular, porque ahora solo es UNA
        db_column="user_id"      # O el nombre que prefieras en DB
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    description =models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        db_table = "geo_location"
    def __str__(self):
        return f"{self.user} @ ({self.latitude}, {self.longitude})"