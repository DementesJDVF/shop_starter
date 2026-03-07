import threading


class BlockInactiveUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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


class CurrentUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = request.user
        response = self.get_response(request)
        return response
