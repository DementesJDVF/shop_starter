import logging
import billiard
from celery import shared_task
from django.db import transaction
from apps.products.models import Product
# El servicio original que hacia request a OpenAI/Hugginface lo invocaremos aquí de manera simulada o real

logger = logging.getLogger(__name__)

# NOTA: Debes de tener la funcion real importada
from apps.ai.services.ai_service import generate_product_description

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,    # Exponential backoff
    retry_backoff_max=60,  # Max backoff 60 sec
    max_retries=3,         # Maximo 3 intentos
    soft_time_limit=120,   # 2 minutos max
    time_limit=150
)
def generate_ai_description_task(self, product_id, image_source, is_url=True):
    """
    Worker Celery robusto que analiza una imagen e inyecta la descripción IA al producto.
    """
    logger.info(f"[Celery] Iniciando IA para product_id={product_id}")
    try:
        # Obtenemos producto limpio desde DB, fuera de la transaccion inicial HTTP
        product = Product.objects.get(id=product_id)
        
        # Opcional: si ya estaba completado, saltamos (idempotencia)
        if product.ai_status == Product.AIStatus.DONE:
            return f"Product {product_id} already has a generated description."

        product.ai_status = Product.AIStatus.PROCESSING
        product.save(update_fields=['ai_status'])

        # Llama a tu servicio IA (Network IO) -> Si falla, salta except y Celery hace ReTry
        ai_text = generate_product_description(image_source, is_url=is_url)

        # Transaccion Atómica Corta solo para el update
        with transaction.atomic():
            # Volver a llamar lock para evitar The Lost Update si el usuario editó en el interin
            product = Product.objects.select_for_update().get(id=product_id)
            product.ai_description = ai_text
            product.ai_status = Product.AIStatus.DONE
            product.save(update_fields=['ai_description', 'ai_status'])
            
        logger.info(f"[Celery] Éxito IA en product_id={product_id}")
        return "Success"

    except Product.DoesNotExist:
        logger.warning(f"Product {product_id} deleted before AI could process it.")
        return "Not found"
        
    except billiard.exceptions.SoftTimeLimitExceeded:
        Product.objects.filter(id=product_id).update(ai_status=Product.AIStatus.FAILED)
        logger.error(f"[Celery] SoftTimeLimit excedido para product_id={product_id}. Estado forzado a FAILED.")
        return "Timeout"
        
    except Exception as e:
        logger.error(f"[Celery] Error en IA product_id={product_id}: {e}")
        # En caso de que se superen los 3 intentos (Celery manejara el reraise), el worker aborta.
        # Capturamos manualmente si self.request.retries es maximo para setear FALLO.
        if self.request.retries >= self.max_retries:
            Product.objects.filter(id=product_id).update(ai_status=Product.AIStatus.FAILED)
            logger.error(f"[Celery] IA Abortada permanentemente en product={product_id}")
        raise e  # Lanzamos de nuevo para que Celery se entere y procese el Retry/Backoff

from datetime import timedelta
from django.utils import timezone

@shared_task
def reap_zombie_ai_tasks():
    """
    SRE Defense: Escanea productos atrapados en PROCESSING por más de 10 minutos y los mata.
    """
    threshold = timezone.now() - timedelta(minutes=10)
    # Cualquier producto atascado en PROCESSING que no haya sido modificado en 10 min es un zombie
    zombies = Product.objects.filter(ai_status=Product.AIStatus.PROCESSING, updated_at__lt=threshold)
    
    count = zombies.update(ai_status=Product.AIStatus.FAILED)
    if count > 0:
        logger.error(f"[Zombie Reaper] Se han forzado {count} productos ahogados a FAILED.")
    
    return f"Reaped {count} zombies"

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=2,
    soft_time_limit=60,
    time_limit=80
)
def task_generate_suggestion(self, image_source, is_url=True):
    """
    Tarea simple para generar una sugerencia de descripción sin tocar la DB directamente.
    """
    try:
        # Si recibimos base64 (archivo subido), lo convertimos a BytesIO para el servicio
        if not is_url:
            import base64
            import io
            logger.info("[Celery] Decodificando imagen base64")
            image_source = io.BytesIO(base64.b64decode(image_source))

        logger.info("[Celery] Solicitando sugerencia IA (sin persistencia)")
        return generate_product_description(image_source, is_url=is_url)
    except Exception as e:
        logger.error(f"[Celery] Error en sugerencia IA: {e}")
        raise e

