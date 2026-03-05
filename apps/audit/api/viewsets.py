from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from apps.audit.infrastructure.models import AuditLog
from .serializers import AuditLogSerializer
from .permissions import IsAdminUserRole


class AuditLogViewSet(ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("user", "content_type")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUserRole]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["user", "action_type", "content_type"]
    ordering_fields = ["created_at"]
    pagination_class = StandardResultsSetPagination
