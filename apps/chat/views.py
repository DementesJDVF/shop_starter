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
        query = Q(status="ACTIVE")
        if keywords:
            # Separar palabras clave extraídas y buscar ocurrencias
            words = keywords.split()
            word_query = Q()
            for word in words:
                # omit commas and short words
                w = word.replace(',', '').strip()
                if len(w) > 2:
                    word_query |= Q(name__icontains=w) | Q(description__icontains=w) | Q(category__name__icontains=w)
            if word_query:
                query &= word_query

        if max_price is not None:
            query &= Q(price__lte=max_price)

        # Obtenemos los 5 mejores resultados
        found_products = Product.objects.filter(query).distinct()[:5]

        # Serializamos minimalista para enviar a Groq y al FrontEnd
        products_json = []
        for p in found_products:
            # Obtener primera imagen
            main_img = p.images.filter(is_main=True).first() or p.images.first()
            img_url = main_img.url_image.url if main_img and main_img.url_image else None
            
            p_data = {
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "stock": p.stock,
                "vendor_id": str(p.vendor.id),  # UUID → str para serialización JSON
                "image_url": img_url
            }
            products_json.append(p_data)

        # 5. LLM: Generar respuesta conversacional
        reply_text = generate_chat_response(message, products_json, image_keywords)

        # 6. Registrar evento para el historial de ventas del Vendor (si hay usuario autenticado y productos recomendados)
        buyer = request.user if request.user.is_authenticated else None
        for p in found_products:
            AIRecommendationEvent.objects.create(
                buyer=buyer,
                product=p,
                user_query=message,
                ai_reasoning=f"Parámetros extraídos: {search_params}"
            )

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
