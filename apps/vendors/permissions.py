from rest_framework.permissions import BasePermission

from apps.users.constants import UserRoles


class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRoles.VENDEDOR
        )