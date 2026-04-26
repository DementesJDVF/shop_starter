from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    
    def get_queryset(self):
        # Soporta filtrar por vendedor vía URL (kwargs) o vía Query Param
        vendor_id = self.kwargs.get('vendor_id') or self.request.query_params.get('vendor')
        
        if vendor_id:
            return Review.objects.filter(vendor__id=vendor_id).order_by('-created_at')
        return Review.objects.all().order_by('-created_at')

    def get_permissions(self):
        # Solo lectura es pública, escritura requiere autenticación.
        # Restricción: Los administradores NO pueden colocar reseñas (son solo monitores).
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            from apps.users.constants import UserRoles
            from rest_framework import exceptions
            
            # Si el usuario es ADMIN, denegamos permiso para escribir reseñas
            if self.request.user.is_authenticated and self.request.user.role == UserRoles.ADMIN:
                return [] # Denegado (se evaluará como falso el set de permisos)

            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        # 1. Obtener el vendedor del contexto de la URL o del body
        vendor_id = self.kwargs.get('vendor_id') or self.request.data.get('vendor')
        
        if not vendor_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"vendor": "Es necesario especificar el vendedor para la reseña."})
            
        # 2. Guardar con los datos automáticos
        serializer.save(
            user=self.request.user, 
            vendor_id=vendor_id
        )
