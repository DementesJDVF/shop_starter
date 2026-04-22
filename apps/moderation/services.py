"""
Motor de Moderación Automática de Imágenes con IA.

Usa HuggingFace Inference API (modelo especializado en NSFW) para analizar
cada imagen subida y decidir si es apta para la plataforma.

Flujo:
  IMAGEN SUBIDA → IA ANALIZA → 
    SEGURA    → APPROVED    → Si todas las imágenes OK → Product.ACTIVE
    RIESGOSA  → FLAGGED     → Admin lo revisa manualmente
    OBSCENA   → REJECTED    → Se notifica al vendedor
    ERROR API → PENDING     → Queda en cola para admin

El modelo nsfw_image_detection clasifica en:
  - "normal":   Imagen apta para todo público → APPROVED
  - "nsfw":     Contenido sexual explícito → REJECTED
  
Umbral de confianza: 85% para rechazar automáticamente.
"""

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Modelo especializado en detección de contenido inapropiado
NSFW_MODEL_URL = "https://api-inference.huggingface.co/models/Falconsai/nsfw_image_detection"
NSFW_REJECTION_THRESHOLD = 0.85  # Si la IA está 85%+ segura de que es NSFW, se rechaza

# Palabras clave ilegales que detectamos en el nombre/descripción del producto
ILLEGAL_KEYWORDS = [
    # Drogas
    'cocaína', 'coca', 'marihuana', 'heroína', 'droga', 'crack', 'éxtasis',
    'metanfetamina', 'psilocibina', 'fentanilo', 'ácido', 'perico',
    # Armas
    'pistola', 'revolver', 'fusil', 'ak-47', 'glock', 'arma', 'balas', 'explosivo', 'granada',
    # Contenido ilegal
    'menor', 'niño', 'infantil', 'porno', 'xxx',
]


def analyze_image_with_ai(image_url: str) -> dict:
    """
    Analiza una imagen con el modelo de IA de HuggingFace.
    
    Returns:
        dict con keys: 'is_safe', 'confidence', 'label', 'error'
    """
    hf_token = getattr(settings, 'HUGGINGFACE_API_TOKEN', '')
    
    if not hf_token:
        logger.warning("HUGGINGFACE_API_TOKEN no configurado. Moderación de IA desactivada.")
        return {'is_safe': None, 'confidence': 0, 'label': 'unknown', 'error': 'No API token'}

    try:
        # Descargamos la imagen para enviarla como bytes a HuggingFace
        img_response = requests.get(image_url, timeout=10)
        img_response.raise_for_status()
        image_data = img_response.content

        # Enviamos la imagen al modelo de moderación
        headers = {"Authorization": f"Bearer {hf_token}"}
        response = requests.post(
            NSFW_MODEL_URL,
            headers=headers,
            data=image_data,
            timeout=20
        )
        response.raise_for_status()
        results = response.json()

        # El modelo devuelve: [{"label": "normal", "score": 0.99}, {"label": "nsfw", "score": 0.01}]
        if isinstance(results, list):
            score_map = {r['label']: r['score'] for r in results}
            nsfw_score = score_map.get('nsfw', 0)
            normal_score = score_map.get('normal', 1)
            
            is_safe = nsfw_score < NSFW_REJECTION_THRESHOLD
            top_label = 'normal' if normal_score > nsfw_score else 'nsfw'
            confidence = max(nsfw_score, normal_score)
            
            logger.info(f"Moderación IA: label={top_label}, nsfw={nsfw_score:.2f}, normal={normal_score:.2f}")
            return {
                'is_safe': is_safe,
                'confidence': confidence,
                'label': top_label,
                'nsfw_score': nsfw_score,
                'normal_score': normal_score,
                'error': None,
            }

        logger.warning(f"Respuesta inesperada de HuggingFace: {results}")
        return {'is_safe': None, 'confidence': 0, 'label': 'unknown', 'error': 'Unexpected response'}

    except requests.exceptions.Timeout:
        logger.error("Timeout al conectar con HuggingFace API.")
        return {'is_safe': None, 'confidence': 0, 'label': 'timeout', 'error': 'API timeout'}
    except Exception as e:
        logger.error(f"Error en moderación de imagen: {e}")
        return {'is_safe': None, 'confidence': 0, 'label': 'error', 'error': str(e)}


def check_product_text(name: str, description: str) -> dict:
    """
    Verifica si el texto del producto contiene palabras clave ilegales.
    
    Returns:
        dict con keys: 'is_safe', 'found_keywords'
    """
    combined = f"{name} {description}".lower()
    found = [kw for kw in ILLEGAL_KEYWORDS if kw in combined]
    return {
        'is_safe': len(found) == 0,
        'found_keywords': found
    }


def moderate_image(pimage_instance) -> str:
    """
    Función principal: modera una imagen y actualiza su estado.
    
    Args:
        pimage_instance: Instancia del modelo PImages
    
    Returns:
        str: El nuevo moderation_status ('APPROVED', 'REJECTED', 'FLAGGED', 'PENDING')
    """
    from apps.products.models import PImages, Product
    
    if not pimage_instance.url_image:
        return PImages.ModerationStatus.PENDING

    try:
        # Construimos la URL de la imagen
        image_url = pimage_instance.url_image.url
        if not image_url.startswith('http'):
            # Imagen local (solo en desarrollo) - no podemos analizarla remotamente
            logger.info("Imagen local detectada - moderación IA omitida en desarrollo.")
            # Auto-aprobamos en desarrollo para no bloquear el flujo
            new_status = PImages.ModerationStatus.APPROVED
            pimage_instance.is_moderated = True
            pimage_instance.moderation_status = new_status
            pimage_instance.moderation_details = {'reason': 'local_dev_auto_approved'}
            PImages.objects.filter(pk=pimage_instance.pk).update(
                is_moderated=True,
                moderation_status=new_status,
                moderation_details={'reason': 'local_dev_auto_approved'}
            )
            _check_and_auto_approve_product(pimage_instance.product)
            return new_status

        # Análisis con IA
        ai_result = analyze_image_with_ai(image_url)

        if ai_result['error'] and ai_result['is_safe'] is None:
            # Si la IA falla, dejamos en PENDING para revisión manual
            new_status = PImages.ModerationStatus.PENDING
            details = {'reason': 'api_error', 'error': ai_result['error']}
        elif not ai_result['is_safe'] and ai_result.get('nsfw_score', 0) >= NSFW_REJECTION_THRESHOLD:
            # Contenido NSFW confirmado → Rechazar
            new_status = PImages.ModerationStatus.REJECTED
            details = {
                'reason': 'nsfw_detected',
                'nsfw_score': ai_result.get('nsfw_score', 0),
                'confidence': ai_result.get('confidence', 0),
            }
        elif not ai_result['is_safe']:
            # Dudoso pero no confirmado → Marcar para revisión
            new_status = PImages.ModerationStatus.FLAGGED
            details = {
                'reason': 'flagged_for_review',
                'nsfw_score': ai_result.get('nsfw_score', 0),
            }
        else:
            # Imagen limpia → Aprobar
            new_status = PImages.ModerationStatus.APPROVED
            details = {
                'reason': 'ai_approved',
                'normal_score': ai_result.get('normal_score', 0),
            }

        # Guardamos el resultado en la imagen
        PImages.objects.filter(pk=pimage_instance.pk).update(
            is_moderated=True,
            moderation_status=new_status,
            moderation_details=details
        )

        logger.info(f"Imagen {pimage_instance.pk} moderada: {new_status}")

        # Si la imagen fue aprobada, verificar si el producto ya puede publicarse
        if new_status == PImages.ModerationStatus.APPROVED:
            _check_and_auto_approve_product(pimage_instance.product)
        elif new_status == PImages.ModerationStatus.REJECTED:
            _handle_rejected_product(pimage_instance.product)

        return new_status

    except Exception as e:
        logger.error(f"Error crítico en moderate_image: {e}")
        return PImages.ModerationStatus.PENDING


def _check_and_auto_approve_product(product):
    """
    Auto-aprueba un producto si todas sus imágenes pasaron la moderación.
    """
    from apps.products.models import PImages, Product
    
    images = product.images.all()
    if not images.exists():
        return

    all_approved = all(
        img.moderation_status == PImages.ModerationStatus.APPROVED
        for img in images
    )

    if all_approved and product.status == Product.ProductStatus.PENDING:
        Product.objects.filter(pk=product.pk).update(
            status=Product.ProductStatus.ACTIVE
        )
        logger.info(f"Producto '{product.name}' auto-aprobado por IA.")
        
        # Notificar al vendedor
        try:
            from apps.core.services.email_service import send_product_status_notification
            product.status = Product.ProductStatus.ACTIVE
            send_product_status_notification(product)
        except Exception as e:
            logger.warning(f"No se pudo enviar notificación al vendedor: {e}")


def _handle_rejected_product(product):
    """
    Si una imagen fue rechazada, el producto completo queda rechazado.
    """
    from apps.products.models import Product
    
    if product.status != Product.ProductStatus.REJECTED:
        Product.objects.filter(pk=product.pk).update(
            status=Product.ProductStatus.REJECTED,
            rejection_reason="Una o más imágenes del producto fueron detectadas como contenido inapropiado por nuestro sistema de moderación automática."
        )
        logger.warning(f"Producto '{product.name}' rechazado automáticamente por contenido inapropiado.")
        
        try:
            from apps.core.services.email_service import send_product_status_notification
            product.status = Product.ProductStatus.REJECTED
            send_product_status_notification(product)
        except Exception as e:
            logger.warning(f"No se pudo notificar el rechazo: {e}")
