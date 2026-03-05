from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.application.services import AuditService
from apps.users.models import User


class UserService:

    @staticmethod
    @transaction.atomic
    def register_user(*, validated_data, ip_address=None):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data.get("role", "CLIENTE"),
        )
        AuditService.log_create(user=user, instance=user, ip_address=ip_address)
        return user

    @staticmethod
    def login_user(*, user, ip_address=None):
        refresh = RefreshToken.for_user(user)
        AuditService.log_login(user=user, ip_address=ip_address)
        return refresh

    @staticmethod
    @transaction.atomic
    def change_role(*, admin_user, target_user: User, new_role, ip_address=None):
        previous_role = target_user.role

        if previous_role == new_role:
            return target_user

        target_user.role = new_role
        target_user.save(update_fields=["role"])

        AuditService.log_role_change(
            user=admin_user,
            instance=target_user,
            previous_role=previous_role,
            ip_address=ip_address,
        )

        return target_user
