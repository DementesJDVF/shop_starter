from rest_framework.decorators import api_view, permission_classes
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
    permission_classes = [AllowAny]
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        # El método update_or_create es perfecto para relaciones OneToOne
        user = serializer.validated_data.get('user')
        Location.objects.update_or_create(
            user=user,
            defaults=serializer.validated_data)
        
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
        "vendor", "vendor__vendorprofile"
    ).filter(
        latitude__isnull=False,
        longitude__isnull=False,
        # activar cuando tengas datos correctos:
        # vendor__vendorprofile__is_active=True
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

    data = [
        NearbyVendorSerializer(
            r["instance"],
            context={"request": request}
        ).data | {"distance": r["distance"]}
        for r in results
    ]

    return Response(data)