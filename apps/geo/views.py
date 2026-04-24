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
        # 'list' (GET /locations/) expone coordenadas de todos: solo para Admins
        # 'my_location' y 'vendors-locations' son acciones especiales con sus propios permisos
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'retrieve']:
            from apps.users.permissions import IsVendorOrAdmin
            return [IsVendorOrAdmin()] 
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

    qs = Location.objects.select_related(
        "user"
    ).filter(
        latitude__isnull=False,
        longitude__isnull=False,
        # Filtramos para que traiga solo locaciones de cuentas "Activas"
        user__status='ACTIVE'
    )

    results = []

    for loc in qs:
        dist = haversine(lat, lng, float(loc.latitude), float(loc.longitude))
        if dist <= radius:
            results.append({
                "instance": loc,
                "distance": round(dist, 2),
            })

    results.sort(key=lambda x: x["distance"])

    data = []
    for r in results:
        instance = r["instance"]
        instance.distance = r["distance"]  # Asignamos el valor dinámico para que el serializador lo lea
        serializer = NearbyVendorSerializer(instance, context={"request": request})
        data.append(serializer.data)

    return Response(data)