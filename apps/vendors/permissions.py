"""DRF permissions for vendor-only endpoints."""

from rest_framework.permissions import BasePermission

from apps.users.constants import UserRoles


class IsVendorRole(BasePermission):
    """Allow access only to authenticated users with VENDOR role."""

    message = "Only vendor users can access this resource"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRoles.VENDOR
        )


# Backward-compatible alias for imports still using IsVendor.
IsVendor = IsVendorRole