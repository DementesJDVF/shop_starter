from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.audit.infrastructure.models import AuditLog
from .permissions import IsAdminUserRole
from .serializers import AuditLogSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class AuditLogViewSet(ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("user", "content_type")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUserRole]
    pagination_class = StandardResultsSetPagination
    ordering = ["-created_at"]
