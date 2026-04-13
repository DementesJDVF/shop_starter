from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
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

class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProductViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReadProSerializer
        return CreProSerializer
    
    pagination_class = ProductPagination
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'description']

    def get_queryset(self):
        """Filtra los productos para devolver solo los del vendedor autenticado, a menos que sea ADMIN."""
        user = self.request.user
        if not user.is_authenticated:
            return Product.objects.none()
            
        if user.role == 'ADMIN':
            return Product.objects.all().order_by('-created_at')
            
        return Product.objects.filter(vendor=user).order_by('-created_at')
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied
        # Asignamos al usuario actual si es vendedor
        if self.request.user.is_authenticated and self.request.user.role == 'VENDEDOR':
            serializer.save(vendor=self.request.user)
        else:
            raise PermissionDenied("Solo los vendedores pueden crear productos.")

    def perform_update(self, serializer):
        from rest_framework.exceptions import PermissionDenied
        # Obtener el usuario actual
        user = self.request.user
        
        # Obtener la instancia antigua para comparar el cambio de estado
        old_instance = self.get_object()
        old_status = old_instance.status
        new_status = serializer.validated_data.get('status', old_status)
        
        # Seguridad: Solo los Administradores pueden aprobar (PENDIENTE -> ACTIVO) o rechazar (PENDIENTE -> RECHAZADO)
        if old_status == "PENDING" and new_status in ["ACTIVE", "REJECTED"]:
            if user.role != 'ADMIN':
                raise PermissionDenied("Solo los administradores pueden aprobar o rechazar productos.")
        
        # Seguridad adicional: Evitar que los vendedores se auto-aprueben productos
        if user.role == 'VENDEDOR' and old_status != new_status:
             # Un vendedor solo puede desactivar sus productos, no activarlos si están pendientes o rechazados
             if new_status == 'ACTIVE' and old_status in ['PENDING', 'REJECTED']:
                 raise PermissionDenied("No tienes permiso para auto-aprobar productos.")

        # Guardamos los cambios en la base de datos
        instance = serializer.save()
        
        # Si el estado del producto cambió, notificamos al vendedor
        if old_status != instance.status:
            # 1. Notificación vía Correo Electrónico
            if instance.status in ["ACTIVE", "REJECTED"]:
                send_product_status_notification(instance)
            
            # 2. Notificación dentro de la Aplicación (Notification model)
            status_label = "Aprobado" if instance.status == "ACTIVE" else "Rechazado"
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


class ProductViewGet(viewsets.ReadOnlyModelViewSet):
    """
    Esta vista solo permite listar (GET /products/) 
    y ver detalle (GET /products/{id}/).
    """
    queryset = Product.objects.filter(status=Product.ProductStatus.ACTIVE).order_by('-created_at')
    serializer_class = ReadProSerializer
    # Especificamos que busque por el campo 'id'
    lookup_field = 'id'
    authentication_classes = []
    permission_classes = [AllowAny]
    pagination_class = ProductPagination
    filterset_fields = ['category', 'vendor']
    search_fields = ['name', 'description']

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        # Aquí podrías, por ejemplo, validar algo antes de guardar
        serializer.save()

class CategoryViewGet(viewsets.ReadOnlyModelViewSet):
    """
    Vista simple para ver la lista de categorías y el detalle de cada una.
    """
    # Usamos all_objects para saltar cualquier filtro de eliminación suave (soft-delete)
    queryset = Category.all_objects.all()
    serializer_class = CategorySerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    # Especificamos que busque por el campo 'id'
    lookup_field = 'id'

@api_view(["GET"])
@permission_classes([AllowAny])
def nearby_products(request):
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

    # 1. Obtenemos locaciones de vendedores activos
    locations = Location.objects.select_related("user").filter(
        latitude__isnull=False,
        longitude__isnull=False,
        user__status='ACTIVE',
        user__role='VENDEDOR'
    )

    # 2. Filtramos por distancia y recolectamos IDs de usuarios
    nearby_users = []
    user_distances = {} # userId -> distance

    for loc in locations:
        dist = haversine(lat, lng, float(loc.latitude), float(loc.longitude))
        if dist <= radius:
            nearby_users.append(loc.user)
            user_distances[loc.user.id] = round(dist, 2)

    # 3. Obtenemos productos de esos vendedores (solo los activos)
    products = Product.objects.filter(
        vendor__in=nearby_users,
        status='ACTIVE'
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
