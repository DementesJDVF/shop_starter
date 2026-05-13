import logging
from celery import shared_task
from apps.users.models import User
from apps.core.services.email_service import send_user_status_notification

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,    # Exponential backoff
    retry_backoff_max=30,  # Max backoff 30 sec
    max_retries=3          # Maximo 3 intentos
)
def send_user_status_notification_task(self, user_id):
    """
    Task de notificaciones. Envia el email asincronamente.
    """
    try:
        user = User.objects.get(id=user_id)
        # El servicio asume que manda un email usando Brevo/Sendgrid etc.
        send_user_status_notification(user)
        logger.info(f"[Celery] Notificacion enviada para user={user_id}")
    except User.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"[Celery] Error enviando notificacion para user={user_id}. Error: {e}")
        raise e
