from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.audit.application.services import AuditService
from apps.audit.infrastructure.models import AuditLog
from apps.core.models.base import BaseModel


# Lista de modelos que ya manejan auditoría manualmente
# para evitar registros duplicados
_MANUALLY_AUDITED_MODELS = set()


def register_manually_audited(model_class):
    """Registra un modelo que ya se audita manualmente en su service."""
    _MANUALLY_AUDITED_MODELS.add(model_class)


# Registrar modelos que ya llaman AuditService manualmente
from apps.users.models import User  # noqa: E402
register_manually_audited(User)


@receiver(post_save)
def audit_create_update(sender, instance, created, **kwargs):
    if not issubclass(sender, BaseModel):
        return

    if sender is AuditLog:
        return

    # Evitar duplicados para modelos que ya se auditan manualmente
    if sender in _MANUALLY_AUDITED_MODELS:
        return

    if created:
        AuditService.log_create(user=None, instance=instance)
        return

    AuditService.log_update(
        user=None,
        instance=instance,
        previous_data=None,
    )
