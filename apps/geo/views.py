from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from apps.geo.serializers import VendorLocationSerializer
from apps.geo.models import Location
from apps.geo.serializers import LocationSerializer
from django.shortcuts import get_list_or_404, get_object_or_404

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [AllowAny]
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = LocationSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
@api_view(['GET', 'POST'])
def vendors_locations(request):
    
    if request.method == 'GET':
        locations =Location.objects.all()
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)
    
    if request.method ==  'POST':
        data = request.data.copy()
        data['vendor'] = request.user.id
        serializer = LocationSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def location_detail(request, pk):
    location = get_object_or_404(Location, id=pk)
    serializer = LocationSerializer(location)
    return Response(serializer.data)

@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_vendor_location(request):

    user = request.user

    if not hasattr(user, "vendorprofile"):
        return Response({"error": "No eres vendedor"}, status=403)

    vendor = user.vendorprofile

    serializer = VendorLocationSerializer(
        vendor,
        data=request.data,
        partial=True,
        context={"request": request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)