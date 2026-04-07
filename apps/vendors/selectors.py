"""Read-model selectors for vendors."""

from django.shortcuts import get_object_or_404

from apps.users.constants import UserRoles

from .models import Vendor


class VendorSelectors:
    @staticmethod
    def get_vendor_profile_by_user(user):
        """Get vendor profile constrained by vendor role as source of truth."""
        return Vendor.objects.filter(user=user, user__role=UserRoles.VENDOR).first()

    @staticmethod
    def get_public_vendor_profile(vendor_id):
        """Get active public vendor profile for vendor-role users only."""
        return get_object_or_404(
            Vendor,
            id=vendor_id,
            status=Vendor.Status.ACTIVE,
            is_deleted=False,
            user__role=UserRoles.VENDOR,
        )