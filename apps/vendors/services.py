from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.users.constants import UserRoles
from apps.users.models import User
from .models import VendorProfile


class VendorService:

    @staticmethod
    def create_vendor_profile(user, data):
        if user.role != UserRoles.VENDEDOR:
            raise PermissionDenied("Solo vendedores pueden crear perfil.")

        if VendorProfile.objects.filter(user=user).exists():
            raise ValidationError("Ya existe un perfil para este usuario.")

        try:
            with transaction.atomic():
                return VendorProfile.objects.create(
                    user=user,
                    location_type=data.get("location_type", VendorProfile.LocationType.FIXED),
                )
        except IntegrityError as exc:
            raise ValidationError("Ya existe un perfil para este usuario.") from exc

    @staticmethod
    def update_vendor_profile(user, profile, data):
        if profile.user != user:
            raise PermissionDenied("No puede modificar un perfil ajeno.")

        allowed_fields = {"location_type"}
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}

        for field, value in filtered_data.items():
            setattr(profile, field, value)

        if filtered_data:
            profile.save(update_fields=[*filtered_data.keys(), "updated_at"])
        return profile

    @staticmethod
    def update_vendor_moderation(*, admin_user, profile, status, verified):
        if admin_user.role != UserRoles.ADMIN:
            raise PermissionDenied("Solo administradores pueden moderar vendedores.")

        if verified and status != VendorProfile.Status.ACTIVE:
            raise ValidationError("Solo un vendedor ACTIVO puede ser verificado.")

        if status == VendorProfile.Status.BLOCKED and verified:
            raise ValidationError("Un vendedor bloqueado no puede estar verificado.")

        profile.status = status
        profile.verified = verified
        profile.save(update_fields=["status", "verified", "updated_at"])

        return profile