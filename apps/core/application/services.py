from django.db import transaction
from apps.audit.application.services import AuditService
from apps.core.middleware import get_current_user, get_current_ip


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

    @staticmethod
    @transaction.atomic
    def restore(*, user=None, instance, ip_address=None):
        if not instance.is_deleted:
            return instance

        old_data = AuditService._serialize(instance)
        instance.is_deleted = False
        instance.save(update_fields=["is_deleted"])

        AuditService.log_restore(
            user=user,
            instance=instance,
            previous_data=old_data,
            new_data=AuditService._serialize(instance),
            ip_address=ip_address,
        )
        return instance

    @staticmethod
    @transaction.atomic
    def hard_delete(*, user=None, instance, ip_address=None):
        previous_data = AuditService._serialize(instance)
        AuditService.log_delete(
            user=user,
            instance=instance,
            previous_data=previous_data,
            ip_address=ip_address,
        )
        instance.hard_delete()

    @classmethod
    def _log(cls, user, action_type, instance, previous_data=None, new_data=None, ip_address=None):
        if not user:
            user = get_current_user()
        if not ip_address:
            ip_address = get_current_ip()
        AuditService._log(
            user=user,
            action_type=action_type,
            instance=instance,
            previous_data=previous_data,
            new_data=new_data,
            ip_address=ip_address,
        )
