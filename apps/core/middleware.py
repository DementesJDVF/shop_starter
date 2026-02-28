class BlockInactiveUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            if not user.is_active:
                from django.http import JsonResponse
                return JsonResponse(
                    {"detail": "Usuario inactivo"},
                    status=403
                )

        return self.get_response(request)