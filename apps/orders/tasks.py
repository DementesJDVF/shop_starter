from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task
def cleanup_expired_reservations():
    """
    SRE: Limpia reservas de órdenes que han expirado (más de 15 minutos).
    Al cancelar la orden, el modelo de Order devuelve automáticamente el stock al producto.
    """
    from apps.orders.models import Order
    
    timeout = timezone.now() - timedelta(minutes=15)
    expired_orders = Order.objects.filter(
        status=Order.Status.RESERVED,
        created_at__lt=timeout
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
