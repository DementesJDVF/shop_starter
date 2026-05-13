import logging
import billiard
from celery import shared_task
from django.db import transaction
from apps.products.models import Product
from apps.ai.services.ai_service import generate_product_description

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=3,
    soft_time_limit=120,
    time_limit=150
)
def generate_ai_description_task(self, product_id, image_source, is_url=True):
    logger.info(f"[Celery] Iniciando IA para product_id={product_id}")
    try:
        product = Product.objects.get(id=product_id)
        if product.ai_status == Product.AIStatus.DONE:
            return f"Product {product_id} already has a generated description."

        product.ai_status = Product.AIStatus.PROCESSING
        product.save(update_fields=['ai_status'])

        ai_text = generate_product_description(image_source, is_url=is_url)

        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=product_id)
            product.ai_description = ai_text
            product.ai_status = Product.AIStatus.DONE
            product.save(update_fields=['ai_description', 'ai_status'])
            
        logger.info(f"[Celery] Éxito IA en product_id={product_id}")
        return "Success"

    except Product.DoesNotExist:
        return "Not found"
    except billiard.exceptions.SoftTimeLimitExceeded:
        Product.objects.filter(id=product_id).update(ai_status=Product.AIStatus.FAILED)
        return "Timeout"
    except Exception as e:
        logger.error(f"[SRE] Error crítico en generate_ai_description_task para prod_{product_id}: {str(e)}")
        if self.request.retries >= self.max_retries:
            Product.objects.filter(id=product_id).update(ai_status=Product.AIStatus.FAILED)
        raise e

from datetime import timedelta
from django.utils import timezone

@shared_task
def reap_zombie_ai_tasks():
    threshold = timezone.now() - timedelta(minutes=10)
    zombies = Product.objects.filter(ai_status=Product.AIStatus.PROCESSING, updated_at__lt=threshold)
    count = zombies.update(ai_status=Product.AIStatus.FAILED)
    return f"Reaped {count} zombies"

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=1,
    soft_time_limit=45,
    time_limit=60
)
def task_generate_suggestion(self, image_source, is_url=True):
    try:
        if not is_url:
            import base64
            import io
            image_source = io.BytesIO(base64.b64decode(image_source))

        try:
            return generate_product_description(image_source, is_url=is_url)
        finally:
            if not is_url and 'image_source' in locals() and hasattr(image_source, 'close'):
                image_source.close()
    except Exception as e:
        logger.error(f"[SRE] Error en task_generate_suggestion: {str(e)}")
        raise e
