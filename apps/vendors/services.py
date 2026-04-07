"""Service layer for vendor profile workflows."""

from __future__ import annotations

from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.vendors.models import VendorProfile
from apps.vendors.utils import get_vendor_profile as get_vendor_profile_util
from apps.vendors.utils import validate_vendor_role


class VendorService:
    """Encapsulates business logic around vendor role and profile checks."""

    @staticmethod
    def get_vendor_profile(user) -> VendorProfile:
        """Public service shortcut to resolve a vendor profile from user."""
        return get_vendor_profile_util(user)

    @staticmethod
    def validate_vendor(user) -> None:
        """Validate the user has VENDOR role."""
        validate_vendor_role(user)

    @staticmethod
    def ensure_vendor_active(user) -> VendorProfile:
        """Ensure user is vendor and profile is ACTIVE."""
        profile = VendorService.get_vendor_profile(user)
        if profile.status != VendorProfile.Status.ACTIVE:
            raise ValidationError("Vendor profile must be active")
        return profile

    @staticmethod
    def create_vendor_profile(user, data):
        """Create vendor profile for a user with VENDOR role."""
        VendorService.validate_vendor(user)

        if hasattr(user, "vendor_profile"):
            raise ValidationError("A vendor profile already exists for this user")

        try:
            with transaction.atomic():
                return VendorProfile.objects.create(user=user, **data)
        except IntegrityError as exc:
            raise ValidationError("A vendor profile already exists for this user") from exc

    @staticmethod
    def update_vendor_profile(user, profile, data):
        """Update own vendor profile fields."""
        VendorService.validate_vendor(user)

        if profile.user != user:
            raise PermissionDenied("You cannot modify another vendor profile")

        for field, value in data.items():
            setattr(profile, field, value)

        profile.save(update_fields=[*data.keys(), "updated_at"])
        return profile