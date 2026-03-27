"""Utility helpers for vendor role/profile resolution."""

from __future__ import annotations

from rest_framework.exceptions import NotFound, PermissionDenied

from apps.users.constants import UserRoles
from apps.vendors.models import VendorProfile


def validate_vendor_role(user) -> None:
    """Ensure the current user has vendor role.

    We intentionally validate against ``User.role`` so role checks do not depend on
    the existence of ``VendorProfile`` records.
    """
    if not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Authentication required")

    if user.role != UserRoles.VENDOR:
        raise PermissionDenied("Only vendor users can perform this action")


def get_vendor_profile(user) -> VendorProfile:
    """Return vendor profile for a role-validated vendor user.

    Raises:
        PermissionDenied: If the user does not have vendor role.
        NotFound: If vendor profile does not exist.
    """
    validate_vendor_role(user)

    try:
        return user.vendor_profile
    except VendorProfile.DoesNotExist as exc:
        raise NotFound("Vendor profile not found") from exc