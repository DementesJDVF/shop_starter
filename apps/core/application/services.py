from django.db import transaction
from apps.audit.application.services import AuditService
from apps.core.middleware import get_current_user


class SoftDeleteService:

    @staticmethod
    @transaction.atomic
    def soft_delete(*, user=None, instance, ip_address=None):
        if instance.is_deleted:
            return instance

        old_data = AuditService._serialize(instance)

        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])

        AuditService.log_soft_delete(
            user=user,
            instance=instance,
            previous_data=old_data,
            new_data=AuditService._serialize(instance),
            ip_address=ip_address,
        )

        return instance

    @classmethod
    def _log(cls, user, action_type, instance, previous_data=None, new_data=None, ip_address=None):

        # 🔥 Si no se pasa usuario, tomarlo automáticamente del middleware
        if not user:
            user = get_current_user()
