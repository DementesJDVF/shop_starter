from django.http import HttpResponseForbidden
from django.http import JsonResponse


class RoleRequiredMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith("/admin-panel/"):
            if not request.user.is_authenticated or request.user.role != "ADMIN":
                return HttpResponseForbidden("No autorizado")

        return self.get_response(request)


class BlockInactiveUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            if not user.is_active:
                return JsonResponse(
                    {"detail": "Usuario inactivo. Contacte al administrador."},
                    status=403
                )

        return self.get_response(request)
