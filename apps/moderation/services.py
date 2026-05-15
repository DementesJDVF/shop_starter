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
Eres un sistema de moderación de contenido para una plataforma de comercio colombiana.
Tu responsabilidad: DETECTAR y RECHAZAR CUALQUIER MATERIAL SENSIBLE o INAPROPIADO.

ANALIZA esta imagen con MÁXIMA RIGUROSIDAD y responde con JSON (sin markdown):

{
  "verdict": "APPROVED" | "REJECTED" | "FLAGGED",
  "reason": "explicación en español",
  "confidence": 0.0 a 1.0,
  "category": "categoría del problema si aplica"
}

─────────────────────────────────────────────────────────────────

CRITERIOS DE RECHAZO ESTRICTO (REJECTED):
1. SEXUAL: Desnudez, semidesndez, contenido sexual explícito, actos sexuales.
2. VIOLENCIA: Sangre, heridas abiertas, muerte, combates violentos.
3. DROGAS & SUSTANCIAS: Marihuana, cocaína, heroína, cualquier droga, paraphernalia.
4. ARMAS: Pistolas, revólveres, rifles, cuchillos, explosivos, armas blancas peligrosas.
5. MENORES: Cualquier imagen que sexualice o ponga en riesgo a menores de edad.
6. ALCOHOL/TABACO: Promoción de bebidas alcohólicas o tabaco (solo se rechaza si es promoción clara).
7. ODIO: Símbolos nazis, contenido racista, homofóbico o discriminatorio.
8. EXPLOTACIÓN: Tráfico de personas, esclavitud, abuso.

CRITERIOS DE APROBACIÓN (APPROVED):
- Comida, bebidas (sin promoción de alcohol)
- Ropa, accesorios, calzado
- Electrónica, muebles, decoración
- Herramientas, servicios, artesanías
- Plantas, flores, mascotas
- Cualquier producto o servicio LEGÍTIMO

CRITERIOS AMBIGUOS (FLAGGED - requiere revisión humana):
- Imagen borrosa o de baja calidad (imposible confirmar contenido)
- Borderline: casi sexual pero no explícito, o casi violento
- Texto en imagen: ofensivo, ilegal o de mal gusto
- Imposible determinar si es producto o no
- Potencial engaño o estafa

─────────────────────────────────────────────────────────────────
⚠️  PRIORIDAD: MEJOR RECHAZAR UNO LEGÍTIMO QUE DEJAR PASAR UNO INAPROPIADO.
Si tienes dudas → FLAGGED para revisión manual.
Responde SOLO con el JSON, nada más.
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


def _log_pending_notification(product, admin_emails, error):
    """Log de notificaciones fallidas para que admins puedan revisarlas manualmente."""
    notification_log = {
        'product_id': str(product.id),
        'product_name': product.name,
        'admin_emails': admin_emails,
        'error': error,
        'timestamp': str(logger.handlers[0].formatter._fmt if logger.handlers else 'N/A')
    }
    logger.warning(f"Notificación pendiente registrada: {notification_log}")

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
        Product.objects.filter(pk=product.pk).update(status=Product.ProductStatus.AVAILABLE)
        logger.info(f"Producto '{product.name}' AUTO-APROBADO por Groq IA.")
        try:
            from apps.core.services.email_service import send_product_status_notification
            product.status = Product.ProductStatus.AVAILABLE
            send_product_status_notification(product)
        except Exception as e:
            logger.warning(f"No se pudo enviar email de aprobación: {e}")


def _handle_rejected_product(product):
    """
    Envía TODO el producto a revisión cuando una imagen es rechazada.
    Crea ProductReview para que admin revise el producto completo.
    """
    from apps.products.models import Product, PImages
    from apps.moderation.models import RejectedImage, ProductReview
    from django.contrib.auth import get_user_model

    User = get_user_model()

    # Cambiar estado del producto a REJECTED
    if product.status != Product.ProductStatus.REJECTED:
        Product.objects.filter(pk=product.pk).update(
            status=Product.ProductStatus.REJECTED,
            rejection_reason="Una o más imágenes fueron rechazadas. El producto ha sido enviado a revisión manual."
        )
        logger.warning(f"Producto '{product.name}' AUTO-RECHAZADO por Groq IA - Enviado a revisión completa.")

    # Obtener imágenes rechazadas
    rejected_images = product.images.filter(moderation_status=PImages.ModerationStatus.REJECTED)

    # Crear registros de RejectedImage
    for image in rejected_images:
        moderation_details = image.moderation_details or {}
        try:
            RejectedImage.objects.get_or_create(
                image=image,
                defaults={
                    'product': product,
                    'vendor': product.vendor,
                    'ai_reason': moderation_details.get('reason', 'Contenido inapropiado detectado'),
                    'ai_confidence': moderation_details.get('confidence', 0),
                }
            )
        except Exception as e:
            logger.error(f"Error creando RejectedImage para {image.pk}: {e}")

    # Crear ProductReview: Enviar TODO el producto a revisión
    try:
        product_review, created = ProductReview.objects.get_or_create(
            product=product,
            defaults={
                'vendor': product.vendor,
                'rejected_images_count': rejected_images.count(),
                'review_status': ProductReview.ReviewStatus.PENDING,
            }
        )
        if not created:
            # Actualizar si ya existe
            product_review.rejected_images_count = rejected_images.count()
            product_review.review_status = ProductReview.ReviewStatus.PENDING
            product_review.save()

        logger.info(f"ProductReview creado para {product.name} (ID: {product_review.id})")
    except Exception as e:
        logger.error(f"Error creando ProductReview: {e}")

    # Notificar a admins con detalles COMPLETOS del producto
    try:
        _notify_admins_full_product_review(product, rejected_images, product_review)
    except Exception as e:
        logger.warning(f"Error enviando notificación a admins: {e}")

    # Notificar al vendedor
    try:
        from apps.core.services.email_service import send_product_status_notification
        product.status = Product.ProductStatus.REJECTED
        send_product_status_notification(product)
    except Exception as e:
        logger.warning(f"No se pudo enviar email de rechazo: {e}")


def _notify_admins_full_product_review(product, rejected_images, product_review):
    """
    Notifica a TODOS los admins sobre PRODUCTO COMPLETO que necesita revisión.
    Incluye: Nombre, Descripción, Categoría, Precio, Stock, TODAS las imágenes.
    """
    from django.contrib.auth import get_user_model
    from django.core.mail import send_mass_mail
    from django.template.loader import render_to_string
    from django.conf import settings

    User = get_user_model()

    # Obtener admins
    admins = User.objects.filter(is_staff=True, is_active=True)
    if not admins.exists():
        logger.warning("No hay admins configurados para notificar")
        return

    admin_emails = [admin.email for admin in admins if admin.email]
    if not admin_emails:
        logger.warning("No hay emails de admin configurados")
        return

    # Preparar datos COMPLETOS del producto
    all_images = product.images.all()
    rejected_images_list = []
    approved_images_list = []

    for image in all_images:
        img_data = {
            'image_url': str(image.url_image),
            'is_main': image.is_main,
            'moderation_status': image.moderation_status,
        }

        if image.moderation_status == 'REJECTED':
            details = image.moderation_details or {}
            img_data.update({
                'reason': details.get('reason', 'Contenido inapropiado'),
                'confidence': f"{details.get('confidence', 0):.1%}",
                'is_rejected': True,
            })
            rejected_images_list.append(img_data)
        else:
            approved_images_list.append(img_data)

    context = {
        # INFORMACIÓN COMPLETA DEL PRODUCTO
        'product_id': str(product.id),
        'product_name': product.name,
        'product_description': product.description,
        'product_category': ', '.join([c.name for c in product.categories.all()]) if product.categories.exists() else 'Sin categoría',
        'product_price': f"${product.price:,.0f}",
        'product_stock': product.stock,
        'product_status': product.status,

        # INFORMACIÓN DEL VENDEDOR
        'vendor_name': product.vendor.get_full_name() or product.vendor.username,
        'vendor_email': product.vendor.email,
        'vendor_phone': getattr(product.vendor, 'phone', 'No disponible'),
        'vendor_username': product.vendor.username,

        # IMÁGENES COMPLETAS
        'rejected_images': rejected_images_list,
        'approved_images': approved_images_list,
        'rejected_images_count': len(rejected_images_list),
        'approved_images_count': len(approved_images_list),
        'total_images': len(all_images),

        # ENLACES
        'product_review_id': str(product_review.id),
        'admin_review_url': f"{settings.FRONTEND_URL}/admin/moderation/product-reviews/{product_review.id}",
        'product_detail_url': f"{settings.FRONTEND_URL}/admin/products/{product.id}",
    }

    try:
        subject = f"🚨 REVISIÓN COMPLETA DE PRODUCTO: {product.name} ({rejected_images_list.__len__()} imágenes rechazadas)"
        html_message = render_to_string('moderation/admin_full_product_review_email.html', context)

        send_mass_mail(
            tuple((
                subject,
                '',  # plain text
                html_message,
                settings.DEFAULT_FROM_EMAIL,
                [email]
            ) for email in admin_emails),
            fail_silently=True,
        )
        logger.info(f"Notificación de revisión completa enviada a {len(admin_emails)} admins")
    except Exception as e:
        logger.error(f"Error enviando emails a admins: {e}")
        _log_pending_notification(product, admin_emails, str(e))