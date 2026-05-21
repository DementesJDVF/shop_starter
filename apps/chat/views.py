from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
from rest_framework.permissions import AllowAny
from apps.products.models import Product
from django.db.models import Q
from apps.chat.services.vision_service import analyze_image_for_search
from apps.chat.services.ai_service import extract_search_parameters, generate_chat_response
from apps.chat.models import AIRecommendationEvent

import logging
logger = logging.getLogger(__name__)

class ChatAssistantView(APIView):
    """
    Controlador para el Chat de Asistencia de Compras.
    Acepta 'message' (texto), 'image' (archivo o URL), 'product_id' (para caché de visión).
    """
    permission_classes = [AllowAny]  # Accesible sin token para clientes anónimos
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request, *args, **kwargs):
        # 1. Obtener entradas del usuario
        message = request.data.get('message', '').strip()
        image = request.data.get('image', None)
        product_id = request.data.get('product_id', None)

        if not message and not image:
            return Response({"error": "Debe enviar un mensaje de texto o una imagen."}, status=status.HTTP_400_BAD_REQUEST)

        image_keywords = None

        # 2. Procesar imagen (Vision AI)
        if product_id:
            try:
                # Intento de ahorro de tokens usando la descripción de IA guardada
                product = Product.objects.get(id=product_id)
                if product.ai_description:
                    image_keywords = product.ai_description
            except Product.DoesNotExist:
                pass

        if image and not image_keywords:
            # Procesar imagen con Groq Vision
            is_url = isinstance(image, str) and image.startswith('http')
            vision_result = analyze_image_for_search(image, is_url=is_url)
            if "keywords" in vision_result:
                image_keywords = vision_result["keywords"]

        # 3. LLM: Extraer parámetros de búsqueda
        search_params = extract_search_parameters(message, image_keywords)
        keywords = search_params.get("keywords", "")
        max_price = search_params.get("max_price", None)

        # 4. Búsqueda Tradicional con Django ORM usando los parámetros de IA
        # Buscamos en Productos Activos
        query = Q(status="AVAILABLE")
        if keywords:
            # Separar palabras clave extraídas y buscar ocurrencias
            words = keywords.split()
            word_query = Q()
            for word in words:
                # omit commas and short words
                w = word.replace(',', '').strip()
                if len(w) > 2:
                    word_query |= Q(name__icontains=w) | Q(description__icontains=w) | Q(categories__name__icontains=w)
            if word_query:
                query &= word_query

        if max_price is not None:
            query &= Q(price__lte=max_price)

        all_matching = Product.objects.filter(query).distinct()
        
        cheapest = None
        most_expensive = None

        if image and all_matching.exists():
            cheapest = all_matching.order_by('price').first()
            most_expensive = all_matching.order_by('-price').first()
            
            # Armamos una lista donde cheapest y most_expensive están al inicio
            selected_products = [cheapest]
            if most_expensive.id != cheapest.id:
                selected_products.append(most_expensive)
            
            # Completamos hasta 5 con los demás productos
            other_products = all_matching.exclude(id__in=[p.id for p in selected_products])[:5 - len(selected_products)]
            found_products = selected_products + list(other_products)
        else:
            # Obtenemos los 5 mejores resultados por defecto
            found_products = all_matching[:5]

        # Serializamos minimalista para enviar a Groq y al FrontEnd
        products_json = []
        for p in found_products:
            # Obtener primera imagen (url_image es un TextField con la URL)
            main_img = p.images.filter(is_main=True).first() or p.images.first()
            img_url = str(main_img.url_image) if main_img and main_img.url_image else None
            
            p_data = {
                "id": str(p.id),  # UUID → str para serialización JSON y Groq
                "name": p.name,
                "price": float(p.price),
                "stock": p.stock,
                "vendor_id": str(p.vendor.id),  # UUID → str para serialización JSON
                "image_url": img_url
            }
            
            # Si se subió imagen, marcamos el más barato y más caro para que la IA lo sepa
            if image and cheapest and most_expensive:
                if p.id == cheapest.id:
                    p_data["is_cheapest"] = True
                if p.id == most_expensive.id:
                    p_data["is_most_expensive"] = True
                    
            products_json.append(p_data)

        # 5. LLM: Generar respuesta conversacional
        try:
            reply_text = generate_chat_response(message, products_json, image_keywords)
        except Exception as e:
            logger.error(f"Error en generate_chat_response: {e}")
            reply_text = "Tengo problemas para procesar tu respuesta ahora mismo, pero aquí tienes lo que encontré."

        # 6. Registrar evento para el historial de ventas del Vendor (si hay usuario autenticado y productos recomendados)
        try:
            buyer = request.user if request.user.is_authenticated else None
            for p in found_products:
                AIRecommendationEvent.objects.create(
                    buyer=buyer,
                    product=p,
                    user_query=message,
                    ai_reasoning=f"Parámetros extraídos: {search_params}"
                )
        except Exception as e:
            logger.error(f"Error al registrar evento de recomendación en la BD: {e}")

        # 7. Respuesta
        return Response({
            "reply": reply_text,
            "products": products_json
        }, status=status.HTTP_200_OK)

class VendorAIHistoryView(APIView):
    """
    Retorna el historial de productos recomendados para el vendedor autenticado.
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
            
        events = AIRecommendationEvent.objects.filter(product__vendor=request.user).order_by('-created_at')[:50]
        
        data = []
        for event in events:
            data.append({
                "id": event.id,
                "product_name": event.product.name,
                "buyer": event.buyer.username if event.buyer else "Anónimo",
                "user_query": event.user_query,
                "ai_reasoning": event.ai_reasoning,
                "created_at": event.created_at
            })
            
        return Response(data, status=status.HTTP_200_OK)
