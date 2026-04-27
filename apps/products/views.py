from rest_framework import status, viewsets
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.decorators import api_view, permission_classes, action, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from apps.users.permissions import IsVendor
from apps.products.models import Product, Category
from apps.products.serializers import (CreProSerializer,
                                       ReadProSerializer,
                                       CategorySerializer,
                                       ProductSerializer)
from apps.core.services.email_service import send_product_status_notification
from apps.core.models import Notification
from apps.ai.services.ai_service import generate_product_description
from apps.products.services import ProductService
from rest_framework import generics
import logging

logger = logging.getLogger(__name__)

class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProductViewSet(viewsets.ModelViewSet):
    throttle_scope = None

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReadProSerializer
        return CreProSerializer
    
    pagination_class = ProductPagination
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'description']

    def get_queryset(self):
        """
        Retrieves products for management dashboard.
        Delegates logic to ProductService.
        """
        return ProductService.get_manageable_products(self.request.user)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        # La lista privada de mis productos requiere estar autenticado
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied, ValidationError
        user = self.request.user
        
        # Si es ADMIN o SUPERUSER, puede especificar el vendor
        if user.role == "ADMIN" or user.is_superuser:
            vendor_id = self.request.data.get('vendor')
            if vendor_id:
                from apps.users.models import User
                try:
                    vendor = User.objects.get(id=vendor_id, role="VENDEDOR")
                    serializer.save(vendor=vendor)
                except User.DoesNotExist:
                    raise ValidationError({"vendor": "El vendedor especificado no existe o no tiene rol VENDEDOR."})
            else:
                # Si no especifica, se le asigna a sí mismo (asumiendo que puede ser admin y tener productos)
                serializer.save(vendor=user)
            return

        # Si es VENDEDOR, se auto-asigna
        if user.role == "VENDEDOR":
            serializer.save(vendor=user)
        else:
            raise PermissionDenied("Solo los vendedores o administradores pueden crear productos.")

    def perform_update(self, serializer):
        from rest_framework.exceptions import PermissionDenied
        # Obtener el usuario actual
        user = self.request.user
        
        # Obtener la instancia antigua para comparar el cambio de estado
        old_instance = self.get_object()
        old_status = old_instance.status
        new_status = serializer.validated_data.get('status', old_status)
        
        # Seguridad: Solo los Administradores pueden aprobar (PENDIENTE -> DISPONIBLE) o rechazar (PENDIENTE -> RECHAZADO)
        if old_status == "PENDING" and new_status in [Product.ProductStatus.AVAILABLE, "REJECTED"]:
            if user.role != 'ADMIN' and not user.is_superuser:
                raise PermissionDenied("Solo los administradores pueden aprobar o rechazar productos.")
        
        # Seguridad adicional: Evitar que los vendedores se auto-aprueben productos
        if user.role == 'VENDEDOR' and old_status != new_status:
             # Un vendedor solo puede desactivar sus productos, no activarlos si están pendientes o rechazados
             if new_status == Product.ProductStatus.AVAILABLE and old_status in ['PENDING', 'REJECTED']:
                 raise PermissionDenied("No tienes permiso para auto-aprobar productos.")

        # Guardamos los cambios en la base de datos
        instance = serializer.save()
        
        # Si el estado del producto cambió, notificamos al vendedor
        if old_status != instance.status:
            # 1. Notificación vía Correo Electrónico
            if instance.status in ["AVAILABLE", "REJECTED"]:
                send_product_status_notification(instance)
            
            # 2. Notificación dentro de la Aplicación (Notification model)
            status_label = "Aprobado" if instance.status == "AVAILABLE" else "Rechazado"
            reason_text = f"\nMotivo: {instance.rejection_reason}" if instance.status == "REJECTED" and instance.rejection_reason else ""
            
            Notification.objects.create(
                user=instance.vendor,
                title=f"Producto {status_label}",
                message=f"Tu producto '{instance.name}' ha sido {status_label.lower()}.{reason_text}",
                type="PRODUCT_STATUS"
            )

    def create(self, request, *args, **kwargs):
        # Usamos el serializador de creación pero respondemos con el de lectura
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Respondemos con el objeto completo para que el front se actualice bien
        read_serializer = ReadProSerializer(serializer.instance, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Soft Delete: En lugar de borrar físicamente, cambiamos el estado a INACTIVE y activamos is_deleted."""
        instance = self.get_object()
        
        # Opcional: Solo dueño o admin
        if request.user.role != 'ADMIN' and not request.user.is_superuser:
            if instance.vendor != request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No tienes permisos para borrar este producto.")

        # Realizar Soft Delete (Doble Capa de Seguridad)
        instance.status = Product.ProductStatus.INACTIVE
        instance.delete() # Esto llama al delete() del BaseModel (is_deleted = True)
        
        import logging
        logging.getLogger(__name__).info(f"[AUDIT] Producto {instance.id} archivado (Soft Delete) por {request.user.username}.")
        
        return Response({"message": "Producto archivado (desactivado) exitosamente."}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def restore(self, request, pk=None):
        """Restaura un producto archivado (Soft Delete -> Active)."""
        instance = Product.all_objects.get(pk=pk)
        
        # Seguridad: Solo dueño o admin
        if request.user.role != 'ADMIN' and not request.user.is_superuser:
            if instance.vendor != request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No tienes permisos para restaurar este producto.")

        instance.restore()
        return Response({"message": "Producto restaurado exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], throttle_classes=[ScopedRateThrottle], throttle_scope='ia_limit')
    def generate_ai_description(self, request, pk=None):
        from rest_framework.exceptions import PermissionDenied
        
        product = self.get_object()
        
        # Seguridad: Solo el dueño vendedor o un ADMIN (o superuser) pueden generarlo
        if (request.user.role not in ['VENDEDOR', 'ADMIN'] and not request.user.is_superuser) or (request.user.role == 'VENDEDOR' and product.vendor != request.user):
            raise PermissionDenied("No tienes permisos para generar una descripción IA para este producto.")
            
        if product.ai_description:
            return Response({"ai_description": product.ai_description, "cached": True})
            
        main_image = product.images.filter(is_main=True).first()
        if not main_image:
            main_image = product.images.first()
            
        if not main_image or not main_image.url_image:
            return Response({"error": "No hay imágenes disponibles para analizar."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Procesamiento ASÍNCRONO vía Celery (Evita bloquear el servidor)
        from apps.products.tasks import generate_ai_description_task
        source_url = main_image.url_image.url if hasattr(main_image.url_image, 'url') else main_image.url_image
        
        try:
            # Aseguramos URL absoluta para imágenes locales (media)
            if not source_url.startswith('http'):
                from django.conf import settings
                backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000').rstrip('/')
                source_url = f"{backend_url}{'' if source_url.startswith('/') else '/'}{source_url}"
            
            # Lanzamos la tarea a Celery y devolvemos estado inicial
            task = generate_ai_description_task.delay(product.id, source_url, is_url=True)
            
            product.ai_status = Product.AIStatus.PROCESSING
            product.save(update_fields=['ai_status'])

            return Response({
                "status": "PROCESSING",
                "task_id": task.id,
                "message": "La IA ha comenzado a analizar el producto en segundo plano.",
                "cached": False
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            product.ai_status = Product.AIStatus.FAILED
            product.save(update_fields=['ai_status'])
            logger.error(f"[SRE] Error en generación directa de IA: {str(e)}")
            return Response({"error": f"Error en el motor de IA: {str(e)}"}, status=500)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], throttle_classes=[ScopedRateThrottle], throttle_scope='ia_limit')
    def suggest_description(self, request):
        """
        Sugiere una descripción basada en una imagen (URL o archivo).
        Modo Directo (Síncrono) para máxima confiabilidad.
        """
        image_url = request.data.get('image_url')
        image_file = request.FILES.get('image_file')
        
        # 1. Validación de entrada
        source = image_file if image_file else image_url
        is_url = bool(image_url and not image_file)

        if not source:
            return Response({"error": "Se requiere una imagen (URL o archivo)."}, status=400)

        try:
            from apps.ai.services.ai_service import generate_product_description
            
            # 2. Procesamiento DIRECTO (Sin conversiones Base64 innecesarias)
            # El motor de IA (Pillow) puede leer el archivo directamente de request.FILES
            suggestion = generate_product_description(source, is_url=is_url)
            
            return Response({
                "status": "DONE",
                "result": suggestion,
                "message": "Sugerencia generada correctamente (Modo Directo)."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[SRE] Error crítico en sugerencia IA síncrona: {str(e)}")
            return Response({"error": f"Error en el motor de IA: {str(e)}"}, status=500)

    @action(detail=False, methods=['get'], url_path='tasks/(?P<task_id>[^/.]+)')
    def get_task_status(self, request, task_id=None):
        """
        Endpoint para consultar el estado de una tarea de Celery por su ID.
        """
        try:
            from celery.result import AsyncResult
            res = AsyncResult(task_id)
            
            state = res.state
            
            if state == 'SUCCESS':
                return Response({
                    "status": "DONE",
                    "result": res.result
                })
            elif state in ['FAILURE', 'REVOKED']:
                return Response({
                    "status": "FAILED",
                    "error": str(res.result) or "La tarea fue cancelada o falló."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif state == 'RETRY':
                return Response({"status": "RETRYING"})
            elif state == 'STARTED':
                return Response({"status": "PROCESSING"})
            
            # PENDING o estados desconocidos
            return Response({"status": "PENDING"})
            
        except Exception as e:
            logger.error(f"[SRE] Error al consultar tarea {task_id}: {str(e)}")
            return Response({"error": "No se pudo consultar el estado de la tarea."}, status=500)


class ProductCatalogView(generics.ListAPIView):
    """
    Public endpoint for listing active products from active vendors.
    Supports filtering by vendor via query parameter.
    """
    serializer_class = ReadProSerializer

    permission_classes = [AllowAny]
    pagination_class = ProductPagination
    filterset_fields = ['category']
    search_fields = ['name', 'description']

    def get_queryset(self):
        vendor_id = self.request.query_params.get('vendor')
        user = self.request.user
        
        # Si un ADMIN o el VENDEDOR dueño está viendo el catálogo (ej. inspección), mostrar todo.
        if user.is_authenticated and (user.role == 'ADMIN' or user.is_superuser):
             return ProductService.get_manageable_products(user, vendor_id=vendor_id)
             
        return ProductService.get_public_catalog(vendor_id=vendor_id)

class ProductDetailPublicView(generics.RetrieveAPIView):
    """
    Public endpoint for retrieving a single active product detail.
    """
    serializer_class = ReadProSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        # The service returns a single product or None, but RetrieveAPIView 
        # expects a queryset. So we filter using the service logic.
        return Product.objects.filter(
            status=Product.ProductStatus.AVAILABLE,
            vendor__status='ACTIVE'
        )

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            from apps.users.permissions import IsAdmin
            return [IsAdmin()]
        return [IsAuthenticated()]
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        # Aquí podrías, por ejemplo, validar algo antes de guardar
        serializer.save()

class CategoryViewGet(viewsets.ReadOnlyModelViewSet):
    """
    Vista simple para ver la lista de categorías y el detalle de cada una.
    """
    # Usamos objects para mostrar solo categorías activas y no eliminadas
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    # Especificamos que busque por el campo 'id'
    lookup_field = 'id'

@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def nearby_products(request):
    request.throttle_scope = 'anon' # Limitamos por IP para evitar abuso de cálculos geométricos
    from apps.geo.models import Location
    from apps.geo.utils import haversine
    
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius", 5)

    try:
        lat = float(lat)
        lng = float(lng)
        radius = float(radius)
    except:
        return Response([], status=400)

    from django.db.models.expressions import RawSQL
    query = """
        6371 * acos(
            cos(radians(%s)) * cos(radians(latitude)) *
            cos(radians(longitude) - radians(%s)) +
            sin(radians(%s)) * sin(radians(latitude))
        )
    """

    # 1 & 2. Filtramos locaciones en SQL puro limitando el dataset en disco
    locations = Location.objects.select_related("user").filter(
        user__status='ACTIVE',
        user__role='VENDEDOR',
        is_active=True
    ).annotate(
        distance=RawSQL(query, (lat, lng, lat))
    ).filter(distance__lte=radius)

    nearby_user_ids = []
    user_distances = {} # userId -> distance

    for loc in locations:
        nearby_user_ids.append(loc.user.id)
        user_distances[loc.user.id] = round(loc.distance, 2)

    # 3. Obtenemos productos de esos vendedores (solo los disponibles)
    products = Product.objects.filter(
        vendor__in=nearby_user_ids,
        status=Product.ProductStatus.AVAILABLE
    ).select_related('category', 'vendor').prefetch_related('images')

    # 4. Serializamos y añadimos la distancia
    data = []
    for product in products:
        prod_data = ReadProSerializer(product, context={'request': request}).data
        prod_data['distance'] = user_distances.get(product.vendor.id)
        data.append(prod_data)

    # Opcional: ordenar por distancia
    data.sort(key=lambda x: x['distance'] if x['distance'] is not None else 999)

    return Response(data)
