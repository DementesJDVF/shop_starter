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
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'retrieve', 'list']:
            from apps.users.permissions import IsAdmin
            return [IsAdmin()] 
        
        return [IsAuthenticated()]

    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        user = serializer.validated_data.pop('user', None) or self.request.user
        
        # Validar explícitamente que no sea AnonymousUser para evitar errores de UUID
        if not user or not user.is_authenticated:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Debe autenticarse para realizar esta acción.")

        # El método update_or_create es perfecto para relaciones OneToOne
        location, created = Location.objects.update_or_create(
            user=user,
            defaults=serializer.validated_data)
        # Sincronizamos el objeto con el serializador
        serializer.instance = location

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