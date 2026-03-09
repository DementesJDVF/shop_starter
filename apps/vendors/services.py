from django.core.exceptions import ValidationError, PermissionDenied
from apps.users.models import User
from .models import VendorProfile


class VendorService:

    @staticmethod
    def create_vendor_profile(user, data):

        if user.role != User.Role.VENDOR:
            raise PermissionDenied("Solo vendedores pueden crear perfil.")

        if hasattr(user, "vendor_profile"):
            raise ValidationError("Ya existe un perfil para este usuario.")

        profile = VendorProfile.objects.create(
            user=user,
            **data
        )

        return profile

    @staticmethod
    def update_vendor_profile(user, profile, data):

        if profile.user != user:
            raise PermissionDenied("No puede modificar un perfil ajeno.")

        for field, value in data.items():
            setattr(profile, field, value)

        profile.save()

        return profile