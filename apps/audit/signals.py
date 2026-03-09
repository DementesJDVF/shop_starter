from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.audit.application.services import AuditService
from apps.audit.infrastructure.models import AuditLog
from apps.core.models.base import BaseModel


@receiver(post_save)
def audit_create_update(sender, instance, created, **kwargs):
    if not issubclass(sender, BaseModel):
        return

    if sender is AuditLog:
        return

    if created:
        AuditService.log_create(user=None, instance=instance)
        return

    AuditService.log_update(
        user=None,
        instance=instance,
        previous_data=None,
    )
