import json
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict

from apps.audit.infrastructure.models import AuditLog
from apps.core.middleware import get_current_ip, get_current_user


class AuditJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        from django.db.models.fields.files import FieldFile
        if isinstance(o, FieldFile):
            return o.url if o else None
        return super().default(o)


class AuditService:

    @staticmethod
    def _log(
        *,
        user,
        action_type,
        instance,
        previous_data=None,
        new_data=None,
        ip_address=None,
    ):
        if not user:
            user = get_current_user()
        
        # Si el usuario es Anónimo (AnonymousUser), lo tratamos como None para la BD
        if user and not user.is_authenticated:
            user = None

        if not ip_address:
            ip_address = get_current_ip()

        content_type = ContentType.objects.get_for_model(instance.__class__)

        AuditLog.objects.create(
            user=user,
            action_type=action_type,
            content_type=content_type,
            object_id=str(instance.pk),
            object_repr=str(instance),
            previous_data=previous_data,
            new_data=new_data,
            ip_address=ip_address,
        )

    @classmethod
    def log_create(cls, user, instance, ip_address=None):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.CREATE,
            instance=instance,
            new_data=cls._serialize(instance),
            ip_address=ip_address,
        )

    @classmethod
    def log_update(cls, user, instance, previous_data, ip_address=None):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.UPDATE,
            instance=instance,
            previous_data=previous_data,
            new_data=cls._serialize(instance),
            ip_address=ip_address,
        )

    @classmethod
    def log_delete(cls, user, instance, previous_data=None, ip_address=None):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.DELETE,
            instance=instance,
            previous_data=previous_data or cls._serialize(instance),
            ip_address=ip_address,
        )

    @classmethod
    def log_soft_delete(
        cls, user, instance, previous_data=None, new_data=None, ip_address=None
    ):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.SOFT_DELETE,
            instance=instance,
            previous_data=previous_data,
            new_data=new_data,
            ip_address=ip_address,
        )

    @classmethod
    def log_restore(
        cls, user, instance, previous_data=None, new_data=None, ip_address=None
    ):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.RESTORE,
            instance=instance,
            previous_data=previous_data,
            new_data=new_data,
            ip_address=ip_address,
        )

    @classmethod
    def log_role_change(cls, user, instance, previous_role, ip_address=None):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.ROLE_CHANGE,
            instance=instance,
            previous_data={"role": previous_role},
            new_data={"role": instance.role},
            ip_address=ip_address,
        )

    @classmethod
    def log_status_change(cls, user, instance, previous_status, ip_address=None):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.STATUS_CHANGE,
            instance=instance,
            previous_data={"status": previous_status},
            new_data={"status": instance.status},
            ip_address=ip_address,
        )

    @staticmethod
    def _serialize(instance):
        data = model_to_dict(instance)
        return json.loads(json.dumps(data, cls=AuditJSONEncoder))

    @classmethod
    def log_login(cls, user, ip_address=None):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.LOGIN,
            instance=user,
            ip_address=ip_address,
        )
