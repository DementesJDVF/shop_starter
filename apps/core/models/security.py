from django.db import models
from .base import BaseModel

class BannedIP(BaseModel):
    """
    REGISTRO DE BLOQUEOS (Lista Negra):
    Aquí se guardan las direcciones IP que han sido expulsadas del sistema 
    por comportamiento malicioso (bots, inyecciones, etc).
    """
    ip_address = models.GenericIPAddressField(unique=True, db_index=True)
    reason = models.TextField(help_text="Razón del bloqueo")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Si está vacío, el bloqueo es permanente")

    class Meta:
        db_table = "core_banned_ip"
        verbose_name = "IP Bloqueada"
        verbose_name_plural = "IPs Bloqueadas"

    def __str__(self):
        return f"{self.ip_address} - Bloqueado por: {self.reason}"
