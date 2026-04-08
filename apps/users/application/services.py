from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.application.services import AuditService
from apps.users.constants import UserRoles
from apps.users.models import User


class UserService:

    @staticmethod
    @transaction.atomic
    def register_user(*, validated_data, ip_address=None):
        role = validated_data.get("role", UserRoles.CUSTOMER)
        
        # El estado inicial es PENDING para vendedores, ACTIVE para clientes
        initial_status = User.Status.PENDING if role == UserRoles.VENDOR else User.Status.ACTIVE
        is_active = False if role == UserRoles.VENDOR else True
        
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=role,
            status=initial_status,
            is_active=is_active,
            # Datos de contacto y perfil
            full_name=validated_data.get("full_name"),
            phone_number=validated_data.get("phone_number"),
            document_type=validated_data.get("document_type"),
            document_number=validated_data.get("document_number"),
            birth_date=validated_data.get("birth_date"),
            expedition_date=validated_data.get("expedition_date"),
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
