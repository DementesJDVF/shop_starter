import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# ===== NUEVO: Sprint IA y Funcionalidad =====
def notify_ia_failure(error: Exception, context: dict = None):
    """
    Registra y notifica cuando un servicio de IA falla.
    No interrumpe el flujo principal.
    """
    timestamp = timezone.now().isoformat()
    logger.error(
        f"[IA FAILURE] {timestamp} | Error: {str(error)} | Contexto: {context}"
    )
    # Aquí se puede extender: envío a Slack, email, webhook, etc.
# ===== FIN NUEVO =====
