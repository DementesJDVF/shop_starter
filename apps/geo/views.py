from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_list_or_404, get_object_or_404
from django.db.models import Q 

from apps.geo.models import Location
from apps.geo.serializers import LocationSerializer
from apps.geo.utils import haversine
from apps.geo.serializers import NearbyVendorSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    
    def get_permissions(self):
        from apps.users.permissions import IsVendor, IsAdmin, IsVendorOrAdmin
        
        # El Administrador solo puede monitorear (list/retrieve). 
        # No puede tener ubicación propia (create/update).
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsVendor()]
            
        if self.action in ['list', 'retrieve']:
            # Permitir acceso público para el mapa de vendedores
            return [AllowAny()]
            
        if self.action == 'my_location':
            return [IsVendor()]

        return [AllowAny()]

    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        # Usamos el serializador para guardar, pasando el usuario de la petición.
        # El método create del serializador se encargará de manejar imágenes y update_or_create.
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_location(self, request):
        """Devuelve la ubicación del vendedor autenticado como lista para evitar errores 404 y que React pueda iterarlo."""
        location = Location.objects.filter(user=request.user).first()
        if not location:
            return Response([])
            
        serializer = self.get_serializer(location)
        return Response([serializer.data])

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def all_locations(self, request):
        """
        Vista de Águila exclusiva para el Administrador.
        Devuelve todas las ubicaciones registradas sin filtros.
        """
        from apps.users.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"error": "No tienes permisos para ver todas las ubicaciones."}, status=403)
            
        locations = Location.objects.all()
        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)
        
@api_view(["GET"])
@permission_classes([AllowAny])
def nearby_vendors(request):
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius", 5)

    try:
        lat = float(lat)
        lng = float(lng)
        radius = float(radius)
    except:
        return Response([], status=400)

    # Fórmula de Haversine en SQL nativo
    query = """
        6371 * acos(
            cos(radians(%s)) * cos(radians(latitude)) *
            cos(radians(longitude) - radians(%s)) +
            sin(radians(%s)) * sin(radians(latitude))
        )
    """

    from django.db.models import Exists, OuterRef
    from apps.products.models import Product

    # Subquery para verificar si el vendedor tiene productos disponibles con stock
    available_products = Product.objects.filter(
        vendor=OuterRef('user'),
        status=Product.ProductStatus.ACTIVE,
        stock__gt=0
    )

    qs = Location.objects.select_related(
        "user"
    ).filter(
        latitude__isnull=False,
        longitude__isnull=False,
        user__status='ACTIVE'
    ).annotate(
        distance=RawSQL(query, (lat, lng, lat)),
        has_stock=Exists(available_products)
    ).filter(
        distance__lte=radius,
        has_stock=True # Solo vendedores con productos reales
    ).order_by('distance')

    data = []
    for loc in qs:
        # La distancia ya viene calculada en la propiedad por el annotate
        loc.distance = round(loc.distance, 2)
        serializer = NearbyVendorSerializer(loc, context={"request": request})
        data.append(serializer.data)

    return Response(data)