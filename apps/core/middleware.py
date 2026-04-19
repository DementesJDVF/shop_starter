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


# --- MEMORIA VOLÁTIL DEL HILO (Thread Locals) ---
# Usamos esto para que cualquier parte del código (servicios, modelos) pueda saber 
# quién está haciendo una acción sin tener que pasar el objeto 'request' por todos lados.
_thread_locals = threading.local()


def get_current_user():
    """Devuelve el usuario que está navegando actualmente."""
    return getattr(_thread_locals, "user", None)


def get_current_ip():
    """Devuelve la dirección IP desde donde se hace la petición."""
    return getattr(_thread_locals, "ip_address", None)


def get_current_user_agent():
    """Devuelve la firma del navegador (User-Agent) del visitante."""
    return getattr(_thread_locals, "user_agent", None)


def get_client_ip_from_request(request):
    """
    Función inteligente para obtener la IP real. 
    Incluso si el sistema está detrás de un Proxy o Cloudflare (X-Forwarded-For),
    esta función encontrará la IP original del usuario.
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class BlockIPMiddleware:
    """
    EL ESCUDO DE FRONTERA:
    Este middleware es el primero en ejecutarse. Revisa si la IP del visitante
    está en nuestra 'Lista Negra' (BannedIP).
    Si está bloqueado, el sistema le cierra la puerta inmediatamente (403 Forbidden).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip_address = get_client_ip_from_request(request)
        
        # Consultamos si esta IP está en nuestra lista de expulsados
        from apps.core.models.security import BannedIP
        from django.utils import timezone
        from django.http import JsonResponse

        is_banned = BannedIP.objects.filter(
            ip_address=ip_address
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).exists()

        if is_banned:
            # ¡PUERTA CERRADA! Retornamos un error elegante pero firme.
            return JsonResponse(
                {
                    "error": "Acceso Denegado por Seguridad",
                    "detail": "Esta dirección IP ha sido bloqueada automáticamente por actividad sospechosa."
                },
                status=403
            )

        return self.get_response(request)


class CurrentUserMiddleware:

    """
    Middleware Maestro de Contexto:
    Captura la identidad del usuario, su IP y su navegador al inicio de cada petición.
    Esta información es el 'combustible' para nuestro motor de ciberseguridad y auditoría.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Guardamos la info en el hilo actual para que esté disponible globalmente
        _thread_locals.user = getattr(request, "user", None)
        _thread_locals.ip_address = get_client_ip_from_request(request)
        _thread_locals.user_agent = request.META.get("HTTP_USER_AGENT", "")
        
        response = self.get_response(request)
        return response

