from django.db import models
from django.conf import settings


class Vendor(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        ACTIVE = "ACTIVE", "Activo"
        BLOCKED = "BLOCKED", "Bloqueado"

    class LocationType(models.TextChoices):
        FIJA = "FIJA", "Fija"
        MOVIL = "MOVIL", "Móvil"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)
    location_type = models.CharField(max_length=10, choices=LocationType.choices)
    reputation = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return self.user.email