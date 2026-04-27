from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer
import uuid
from django.db.models import Avg

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    
    def get_queryset(self):
        # Soporta filtrar por vendedor vía URL (kwargs) o vía Query Param
        vendor_id = self.kwargs.get('vendor_id') or self.request.query_params.get('vendor')
        
        # Filtro base: Solo reseñas no borradas
        qs = Review.objects.all().order_by('-created_at')

        if vendor_id:
            try:
                uuid.UUID(str(vendor_id))
                qs = qs.filter(vendor__id=vendor_id)
            except (ValueError, TypeError):
                return Review.objects.none()
            
        return qs

    def list(self, request, *args, **kwargs):
        vendor_id = self.kwargs.get('vendor_id') or request.query_params.get('vendor')
        queryset = self.get_queryset()
        
        # Si estamos filtrando por un vendedor específico, devolvemos el formato enriquecido
        if vendor_id:
            try:
                uuid.UUID(str(vendor_id))
                avg_rating = queryset.aggregate(Avg('rating'))['rating__avg'] or 0
                total_reviews = queryset.count()
                
                # Serializamos los resultados (puedes usar paginación si quieres, pero aquí es simple)
                serializer = self.get_serializer(queryset, many=True)
                
                return Response({
                    "average": round(float(avg_rating), 1),
                    "total": total_reviews,
                    "reviews": serializer.data
                })
            except (ValueError, TypeError):
                return Response({
                    "average": 0,
                    "total": 0,
                    "reviews": []
                })

        # Comportamiento estándar de lista si no hay vendor_id
        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        # Solo lectura es pública, escritura requiere autenticación.
        # Restricción: Los administradores NO pueden colocar reseñas (son solo monitores).
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            from apps.users.constants import UserRoles
            from rest_framework import exceptions
            
            # Política de Neutralidad: Los administradores NO pueden colocar reseñas ni comentarios.
            if self.request.user.is_authenticated and self.request.user.role == UserRoles.ADMIN:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Como Administrador debes mantener la neutralidad. No puedes publicar reseñas.")

            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        # 1. Obtener el vendedor del contexto de la URL o del body
        vendor_id = self.kwargs.get('vendor_id') or self.request.data.get('vendor')
        
        if not vendor_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"vendor": "Es necesario especificar el vendedor para la reseña."})
            
        # 2. ANTI-FRAUDE: Validar que el usuario haya COMPRADO algo de este vendedor
        from apps.orders.models import Order
        has_purchased = Order.objects.filter(
            client=self.request.user,
            vendor_id=vendor_id,
            status=Order.Status.PAID
        ).exists()

        if not has_purchased:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Solo puedes reseñar a vendedores a los que les hayas comprado (y pagado).")

        # 3. Guardar con los datos automáticos
        serializer.save(
            user=self.request.user, 
            vendor_id=vendor_id
        )

    def perform_update(self, serializer):
        # SEGURIDAD: Solo el autor puede editar su reseña
        if serializer.instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permiso para editar esta reseña.")
        serializer.save()

    def perform_destroy(self, instance):
        # SEGURIDAD: Solo el autor o un ADMIN pueden borrar
        user = self.request.user
        if instance.user != user and user.role != 'ADMIN' and not user.is_superuser:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permiso para eliminar esta reseña.")
        instance.delete()
