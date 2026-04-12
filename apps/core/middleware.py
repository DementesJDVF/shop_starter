import threading


class BlockInactiveUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Las rutas de API usan autenticación JWT que DRF procesa DESPUÉS del middleware.
        # Si bloqueamos aquí, el usuario aún no está autenticado y se bloquea incorrectamente.
        # DRF maneja los permisos por sí mismo en las vistas de API.
        if request.path.startswith('/api/'):
            return self.get_response(request)

        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            if not user.is_active or getattr(user, "status", "ACTIVE") != "ACTIVE":
                from django.http import JsonResponse
                return JsonResponse(
                    {"detail": "Usuario inactivo o bloqueado"},
                    status=403,
                )

        return self.get_response(request)


_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, "user", None)


def get_current_ip():
    return getattr(_thread_locals, "ip_address", None)


def get_client_ip_from_request(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class CurrentUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, "user", None)
        _thread_locals.ip_address = get_client_ip_from_request(request)
        response = self.get_response(request)
        return response
