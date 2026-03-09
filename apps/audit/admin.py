from django.contrib import admin
from apps.audit.infrastructure.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "action_type",
        "user",
        "source",
        "object_repr",
        "created_at",
    )

    list_filter = (
        "action_type",
        "source",
        "created_at",
    )

    search_fields = (
        "object_repr",
        "user__email",
    )

    readonly_fields = (
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
    )

    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
