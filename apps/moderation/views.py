from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import RejectedImage, ModerationFlag
from .serializers import RejectedImageSerializer, RejectedImageDetailSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permiso para que solo admins puedan revisar/editar imágenes rechazadas."""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class RejectedImageViewSet(viewsets.ModelViewSet):
    """ViewSet para revisar y gestionar imágenes rechazadas."""
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = RejectedImageSerializer
    filterset_fields = ['review_status', 'vendor', 'rejected_at']
    search_fields = ['product__name', 'vendor__username', 'vendor__email']
    ordering_fields = ['rejected_at', 'review_status']
    ordering = ['-rejected_at']

    def get_queryset(self):
        """Solo admins ven las imágenes rechazadas."""
        if self.request.user.is_staff:
            return RejectedImage.objects.select_related(
                'image', 'product', 'vendor', 'reviewed_by'
            )
        return RejectedImage.objects.none()

    def get_serializer_class(self):
        """Usar serializer más detallado en retrieve."""
        if self.action == 'retrieve':
            return RejectedImageDetailSerializer
        return RejectedImageSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Aprobar una imagen rechazada (falso positivo)."""
        rejected = self.get_object()

        if rejected.review_status != RejectedImage.ReviewStatus.PENDING:
            return Response(
                {'error': 'Solo se pueden revisar imágenes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar estado
        rejected.review_status = RejectedImage.ReviewStatus.APPROVED
        rejected.reviewed_by = request.user
        rejected.reviewed_at = timezone.now()
        rejected.admin_notes = request.data.get('notes', '')
        rejected.save()

        # Aprobar imagen en PImages
        from apps.products.models import PImages
        PImages.objects.filter(pk=rejected.image.pk).update(
            moderation_status=PImages.ModerationStatus.APPROVED
        )

        # Verificar si todas las imágenes ahora están aprobadas
        product = rejected.product
        from apps.products.models import Product
        all_approved = all(
            img.moderation_status == PImages.ModerationStatus.APPROVED
            for img in product.images.all()
        )
        if all_approved and product.status == Product.ProductStatus.REJECTED:
            Product.objects.filter(pk=product.pk).update(
                status=Product.ProductStatus.AVAILABLE,
                rejection_reason=""
            )

        return Response(
            RejectedImageDetailSerializer(rejected).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def confirm_rejection(self, request, pk=None):
        """Confirmar el rechazo de una imagen (legítimamente inapropiada)."""
        rejected = self.get_object()

        if rejected.review_status != RejectedImage.ReviewStatus.PENDING:
            return Response(
                {'error': 'Solo se pueden revisar imágenes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        rejected.review_status = RejectedImage.ReviewStatus.CONFIRMED_REJECTED
        rejected.reviewed_by = request.user
        rejected.reviewed_at = timezone.now()
        rejected.admin_notes = request.data.get('notes', '')
        rejected.save()

        # El producto permanece rechazado
        # Opcionalmente, notificar al vendedor con más detalles

        return Response(
            RejectedImageDetailSerializer(rejected).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def pending_count(self, request):
        """Contar imágenes rechazadas pendientes de revisión."""
        count = RejectedImage.objects.filter(
            review_status=RejectedImage.ReviewStatus.PENDING
        ).count()
        return Response({'pending_count': count})

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Estadísticas del panel de moderación."""
        from django.db.models import Count

        stats = {
            'pending': RejectedImage.objects.filter(
                review_status=RejectedImage.ReviewStatus.PENDING
            ).count(),
            'reviewed': RejectedImage.objects.filter(
                review_status=RejectedImage.ReviewStatus.REVIEWED
            ).count(),
            'approved_by_admin': RejectedImage.objects.filter(
                review_status=RejectedImage.ReviewStatus.APPROVED
            ).count(),
            'confirmed_rejected': RejectedImage.objects.filter(
                review_status=RejectedImage.ReviewStatus.CONFIRMED_REJECTED
            ).count(),
            'total_rejected_images': RejectedImage.objects.count(),
            'vendors_with_rejections': RejectedImage.objects.values('vendor').distinct().count(),
        }

        # Top 5 vendors con más rechazos
        top_vendors = RejectedImage.objects.values(
            'vendor__username', 'vendor__email'
        ).annotate(
            rejection_count=Count('id')
        ).order_by('-rejection_count')[:5]

        return Response({
            'stats': stats,
            'top_vendors': top_vendors
        })