from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.users.models import User

from .models import Vendor


class VendorService:
    @staticmethod
    def create_vendor_profile(user, data):
        if user.role != User.Role.VENDEDOR:
            raise PermissionDenied("Solo vendedores pueden crear perfil.")

        if hasattr(user, "vendor"):
            raise ValidationError("Ya existe un perfil para este usuario.")

        try:
            with transaction.atomic():
                return Vendor.objects.create(user=user, **data)
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
