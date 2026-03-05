from django.db import transaction
from apps.audit.application.services import AuditService
from apps.users.models import User


class UserService:

    @staticmethod
    @transaction.atomic
    def change_role(*, admin_user, target_user: User, new_role, ip_address=None):
        previous_role = target_user.role

        if previous_role == new_role:
            return target_user

        target_user.role = new_role
        target_user.save(update_fields=["role"])

        # 🔎 Auditoría cambio de rol
        AuditService.log_update(
            user=admin_user,
            instance=target_user,
            previous_data={"role": previous_role},
            ip_address=ip_address,
        )

        return target_user
