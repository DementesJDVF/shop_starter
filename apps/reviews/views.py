from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    
    def get_queryset(self):
        # Permite filtrar por vendedor: GET /api/reviews/?vendor=UUID
        vendor_id = self.request.query_params.get('vendor')
        if vendor_id:
            return Review.objects.filter(vendor__id=vendor_id).order_by('-created_at')
        return Review.objects.all().order_by('-created_at')

    def get_permissions(self):
        # Solo lectura es pública, escritura requiere autenticación
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
