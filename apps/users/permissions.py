from rest_framework.permissions import BasePermission
from .constants import UserRoles


class HasRole(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in self.allowed_roles
        )


class IsAdmin(HasRole):
    allowed_roles = [UserRoles.ADMIN]

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.role == UserRoles.ADMIN or request.user.is_superuser)
        )
class IsVendor(HasRole):
    allowed_roles = [UserRoles.VENDEDOR]
class IsVendorOrAdmin(HasRole):
    allowed_roles = [UserRoles.VENDEDOR, UserRoles.ADMIN]
class IsClient(HasRole):
    allowed_roles = [UserRoles.CLIENTE]


class IsAdminOrVendor(HasRole):
    allowed_roles = [UserRoles.ADMIN, UserRoles.VENDEDOR]
