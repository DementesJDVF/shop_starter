from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils.text import slugify
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.application.services import AuditService
from apps.users.constants import UserRoles
from apps.users.models import User


class UserService:

    @staticmethod
    def _build_username(email):
        base_username = slugify(email.split("@")[0]).replace("-", "")[:120] or "usuario"
        candidate = base_username
        suffix = 1

        while User.objects.filter(username=candidate).exists():
            candidate = f"{base_username}{suffix}"
            suffix += 1

        return candidate

    @staticmethod
    @transaction.atomic
    def register_user(*, validated_data, ip_address=None):
        user = User.objects.create_user(
            username=UserService._build_username(validated_data["email"]),
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data.get("role", UserRoles.CLIENTE),
            full_name=validated_data.get("full_name", ""),
            document_type=validated_data.get("document_type", ""),
            document_number=validated_data.get("document_number"),
            birth_date=validated_data.get("birth_date"),
            document_issue_date=validated_data.get("document_issue_date"),
            phone=validated_data.get("phone", ""),
            address=validated_data.get("address", ""),
            business_name=validated_data.get("business_name", ""),
            product_types=validated_data.get("product_types", ""),
            status=User.Status.PENDING,
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

    @staticmethod
    @transaction.atomic
    def change_status(*, admin_user, target_user: User, new_status, ip_address=None):
        previous_status = target_user.status

        if previous_status == new_status:
            return target_user

        target_user.status = new_status
        target_user.save(update_fields=["status"])

        AuditService.log_status_change(
            user=admin_user,
            instance=target_user,
            previous_status=previous_status,
            ip_address=ip_address,
        )

        UserService._send_status_update_email(user=target_user)

        return target_user

    @staticmethod
    def _send_status_update_email(*, user: User):
        if user.status == User.Status.ACTIVE:
            subject = "Cuenta aprobada"
            message = (
                f"Hola {user.full_name or ''},\n\n"
                "Tu cuenta ha sido aprobada. Ya puedes iniciar sesión.\n\n"
                "ShopStarter"
            )
        elif user.status == User.Status.REJECTED:
            subject = "Cuenta rechazada"
            message = (
                f"Hola {user.full_name or ''},\n\n"
                "Tu solicitud fue rechazada. Debes registrarte nuevamente.\n\n"
                "ShopStarter"
            )
        else:
            return

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )