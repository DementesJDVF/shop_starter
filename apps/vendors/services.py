from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.users.models import User
from .models import VendorProfile


class VendorService:

    @staticmethod
    def create_vendor_profile(user, data):
        if user.role != User.Role.VENDEDOR:
            raise PermissionDenied("Solo vendedores pueden crear perfil.")

        if hasattr(user, "vendor_profile"):
            raise ValidationError("Ya existe un perfil para este usuario.")

        try:
            with transaction.atomic():
                return VendorProfile.objects.create(user=user, **data)
        except IntegrityError as exc:
            raise ValidationError("Ya existe un perfil para este usuario.") from exc

    @staticmethod
    def update_vendor_profile(user, profile, data):
        if profile.user != user:
            raise PermissionDenied("No puede modificar un perfil ajeno.")

        for field, value in data.items():
            setattr(profile, field, value)

        profile.save(update_fields=[*data.keys(), "updated_at"])
        return profile

    @staticmethod
    def update_vendor_moderation(*, admin_user, profile, status, verified):
        if admin_user.role != User.Role.ADMIN:
            raise PermissionDenied("Solo administradores pueden moderar vendedores.")

        # 🔒 Reglas de negocio (muy importante para el HU)
        if verified and status != VendorProfile.Status.ACTIVE:
            raise ValidationError("Solo un vendedor ACTIVO puede ser verificado.")

        if status == VendorProfile.Status.BLOCKED and verified:
            raise ValidationError("Un vendedor bloqueado no puede estar verificado.")

        profile.status = status
        profile.verified = verified
        profile.save(update_fields=["status", "verified", "updated_at"])

        return profile