import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import BaseModel


class AuditLog(BaseModel):
    class ActionType(models.TextChoices):
        CREATE = "CREATE"
        UPDATE = "UPDATE"
        DELETE = "DELETE"
        SOFT_DELETE = "SOFT_DELETE"
        RESTORE = "RESTORE"
        STATUS_CHANGE = "STATUS_CHANGE"
        ROLE_CHANGE = "ROLE_CHANGE"
        LOGIN = "LOGIN"
        LOGOUT = "LOGOUT"
        UNKNOWN = "UNKNOWN"

    class SourceType(models.TextChoices):
        API = "API"
        ADMIN = "ADMIN"
        SYSTEM = "SYSTEM"
        BACKGROUND = "BACKGROUND"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )



    action_type = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        default=ActionType.UNKNOWN,
    )

    source = models.CharField(
        max_length=30,
        choices=SourceType.choices,
        default=SourceType.API,
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    object_repr = models.CharField(max_length=255, blank=True)

    previous_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)

    is_suspicious = models.BooleanField(default=False, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "audit_log"
        indexes = [
            models.Index(fields=["action_type"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["content_type", "object_id", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action_type} - {self.object_repr}"
