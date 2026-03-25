from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.geo.models import Location
from apps.users.serializers import LocationSerializer
from decimal import Decimal, InvalidOperation

@api_view(['GET', 'POST'])
def vendors_locations(request):
    
    if request.method == 'GET':
        locations = Location.objects.all()
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)
    
    if request.method ==  'POST':
        serializer = LocationSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def location_detail(request, pk):
    try:
        location = Location.objects.get(id=pk)
    except Location.DoesNotExist:
        return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)

   
    serializer = LocationSerializer(location)
    data = serializer.data
    for field in ['latitude', 'longitude']:
        try:
            data[field] = Decimal(data[field])
        except (InvalidOperation, TypeError, ValueError):
            data[field] = None  
    return Response(data)