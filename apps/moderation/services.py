"""
Motor de Moderación Automática de Imágenes con Groq Llama 4 Scout.

Usa exactamente el mismo patrón que vision_service.py del chat para analizar
cada imagen subida y detectar contenido inapropiado, obsceno o ilegal.

Flujo:
  IMAGEN SUBIDA → GROQ LLAMA 4 ANALIZA → 
    SEGURA    → APPROVED → Si todas las imágenes OK → Product.ACTIVE
    RIESGOSA  → FLAGGED  → Admin lo revisa manualmente
    OBSCENA   → REJECTED → Se notifica al vendedor automáticamente
    ERROR API → PENDING  → Queda en cola para admin
"""

import os
import io
import base64
import logging
import requests
from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)

GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', os.environ.get('GROQ_API_KEY', ''))
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

MODERATION_PROMPT = """
Eres un sistema de moderación de contenido para una plataforma de comercio local colombiana.
Analiza esta imagen y determina si es apropiada para publicarse como foto de producto.

Responde ÚNICAMENTE con el siguiente formato JSON (sin markdown, sin explicación extra):
{
  "verdict": "APPROVED" | "REJECTED" | "FLAGGED",
  "reason": "breve explicación en español",
  "confidence": 0.0 a 1.0
}

Criterios:
- APPROVED: Imagen de producto normal, comida, ropa, objetos cotidianos, servicios, etc.
- REJECTED: Contenido sexual explícito, desnudez, armas ilegales, drogas, violencia explícita, contenido con menores de edad.
- FLAGGED: Imagen sospechosa o ambigua que requiere revisión humana (ej: imagen borrosa, no parece un producto, texto ofensivo, contenido parcialmente inapropiado).
"""

# Palabras clave ilegales en texto de producto
ILLEGAL_KEYWORDS = [
    'cocaína', 'marihuana', 'heroína', 'droga', 'crack', 'éxtasis',
    'metanfetamina', 'fentanilo', 'perico', 'bazuco',
    'pistola venta', 'revolver venta', 'arma ilegal', 'explosivo',
]


def _image_to_base64(image_url: str) -> str | None:
    """Descarga y convierte una imagen a base64 JPEG optimizado — igual que vision_service."""
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        img = Image.open(io.BytesIO(response.content))
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error al convertir imagen a base64: {e}")
        return None


def analyze_image_with_ai(image_url: str) -> dict:
    """
    Envía la imagen a Groq Llama 4 Scout para moderación automática.
    Mismo patrón que vision_service.py del chat.
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY no configurado. Moderación de IA desactivada.")
        return {'verdict': 'PENDING', 'reason': 'Sin API key configurada', 'confidence': 0, 'error': 'No API key'}

    base64_image = _image_to_base64(image_url)
    if not base64_image:
        return {'verdict': 'PENDING', 'reason': 'No se pudo descargar la imagen', 'confidence': 0, 'error': 'Download error'}

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": MODERATION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 150
        }

        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content'].strip()
            # Parsear el JSON de respuesta
            import json
            result = json.loads(content)
            logger.info(f"Moderación Groq: verdict={result.get('verdict')}, confidence={result.get('confidence')}")
            return {
                'verdict': result.get('verdict', 'FLAGGED'),
                'reason': result.get('reason', ''),
                'confidence': result.get('confidence', 0),
                'error': None,
            }
        else:
            logger.error(f"Error Groq API {response.status_code}: {response.text[:200]}")
            return {'verdict': 'PENDING', 'reason': f'API error {response.status_code}', 'confidence': 0, 'error': response.text[:100]}

    except Exception as e:
        logger.error(f"Excepción en moderación Groq: {e}")
        return {'verdict': 'PENDING', 'reason': str(e), 'confidence': 0, 'error': str(e)}


def check_product_text(name: str, description: str) -> dict:
    """Verifica si el texto tiene palabras clave ilegales."""
    combined = f"{name} {description}".lower()
    found = [kw for kw in ILLEGAL_KEYWORDS if kw in combined]
    return {'is_safe': len(found) == 0, 'found_keywords': found}


def moderate_image(pimage_instance) -> str:
    """
    Función principal: analiza la imagen con Groq y actualiza su estado en BD.
    Se llama desde PImages.save() en un Thread separado.
    """
    from apps.products.models import PImages, Product

    if not pimage_instance.url_image:
        return PImages.ModerationStatus.PENDING

    try:
        image_url = pimage_instance.url_image.url

        # Si es imagen local (desarrollo sin Cloudinary), auto-aprobamos
        if not image_url.startswith('http'):
            logger.info("Imagen local detectada — auto-aprobada en entorno de desarrollo.")
            PImages.objects.filter(pk=pimage_instance.pk).update(
                is_moderated=True,
                moderation_status=PImages.ModerationStatus.APPROVED,
                moderation_details={'reason': 'local_dev_auto_approved'}
            )
            _check_and_auto_approve_product(pimage_instance.product)
            return PImages.ModerationStatus.APPROVED

        # Análisis con Groq
        ai_result = analyze_image_with_ai(image_url)
        verdict = ai_result.get('verdict', 'PENDING')

        # Mapear veredicto al ModerationStatus
        status_map = {
            'APPROVED': PImages.ModerationStatus.APPROVED,
            'REJECTED': PImages.ModerationStatus.REJECTED,
            'FLAGGED':  PImages.ModerationStatus.FLAGGED,
            'PENDING':  PImages.ModerationStatus.PENDING,
        }
        new_status = status_map.get(verdict, PImages.ModerationStatus.PENDING)

        # Guardar resultado en BD
        PImages.objects.filter(pk=pimage_instance.pk).update(
            is_moderated=True,
            moderation_status=new_status,
            moderation_details={
                'verdict': verdict,
                'reason': ai_result.get('reason', ''),
                'confidence': ai_result.get('confidence', 0),
                'error': ai_result.get('error'),
            }
        )

        logger.info(f"Imagen {pimage_instance.pk} → {new_status} (razón: {ai_result.get('reason', '')})")

        # Acciones post-moderación
        if new_status == PImages.ModerationStatus.APPROVED:
            _check_and_auto_approve_product(pimage_instance.product)
        elif new_status == PImages.ModerationStatus.REJECTED:
            _handle_rejected_product(pimage_instance.product)

        return new_status

    except Exception as e:
        logger.error(f"Error crítico en moderate_image (ID: {pimage_instance.pk}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        return PImages.ModerationStatus.PENDING


def _check_and_auto_approve_product(product):
    """Auto-aprueba el producto si TODAS sus imágenes están aprobadas."""
    from apps.products.models import PImages, Product

    images = product.images.all()
    if not images.exists():
        return

    all_approved = all(
        img.moderation_status == PImages.ModerationStatus.APPROVED
        for img in images
    )

    if all_approved and product.status == Product.ProductStatus.PENDING:
        Product.objects.filter(pk=product.pk).update(status=Product.ProductStatus.ACTIVE)
        logger.info(f"Producto '{product.name}' AUTO-APROBADO por Groq IA.")
        try:
            from apps.core.services.email_service import send_product_status_notification
            product.status = Product.ProductStatus.ACTIVE
            send_product_status_notification(product)
        except Exception as e:
            logger.warning(f"No se pudo enviar email de aprobación: {e}")


def _handle_rejected_product(product):
    """Rechaza el producto si tiene alguna imagen con contenido inapropiado."""
    from apps.products.models import Product

    if product.status != Product.ProductStatus.REJECTED:
        Product.objects.filter(pk=product.pk).update(
            status=Product.ProductStatus.REJECTED,
            rejection_reason="Una o más imágenes fueron rechazadas por nuestro sistema de moderación automática por contener contenido inapropiado."
        )
        logger.warning(f"Producto '{product.name}' AUTO-RECHAZADO por Groq IA.")
        try:
            from apps.core.services.email_service import send_product_status_notification
            product.status = Product.ProductStatus.REJECTED
            send_product_status_notification(product)
        except Exception as e:
            logger.warning(f"No se pudo enviar email de rechazo: {e}")
