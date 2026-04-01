from django.http import HttpResponseForbidden


class RoleRequiredMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith("/admin-panel/"):
            if not request.user.is_authenticated or request.user.role != "ADMIN":
                return HttpResponseForbidden("No autorizado")

        return self.get_response(request)
