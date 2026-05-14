from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    retry_jitter=True
)
def cleanup_expired_reservations(self):
    """
    SRE: Limpia reservas de órdenes que han expirado (más de 15 minutos).
    Al cancelar, el producto vuelve a AVAILABLE. El stock NO se modifica
    (es gestionado exclusivamente por el vendedor desde Gestión de Productos).
    """
    from apps.orders.models import Order
    from django.db import transaction
    
    with transaction.atomic():
        expired_orders = Order.objects.select_for_update().filter(
            status=Order.Status.RESERVED,
            expires_at__lt=timezone.now()
        )
        
        count = expired_orders.count()
        if count > 0:
            logger.info(f"[SRE] Iniciando limpieza de {count} reservas expiradas...")
            for order in expired_orders:
                try:
                    order.status = Order.Status.CANCELLED
                    order.save()
                    logger.info(f"[SRE] Orden {order.id} expirada y cancelada. Stock liberado.")
                except Exception as e:
                    logger.error(f"[SRE] Error al limpiar orden {order.id}: {str(e)}")
            
        return f"{count} reservas expiradas limpiadas."
