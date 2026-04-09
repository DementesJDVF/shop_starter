from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_list_or_404, get_object_or_404

from apps.geo.models import Location
from apps.geo.serializers import LocationSerializer

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