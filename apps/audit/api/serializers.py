from rest_framework import serializers

from apps.audit.infrastructure.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "action_type",
            "source",
            "content_type",
            "object_id",
            "object_repr",
            "previous_data",
            "new_data",
            "ip_address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
