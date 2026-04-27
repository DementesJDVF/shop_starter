from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck

class CustomJWTAuthentication(JWTAuthentication):
    def enforce_csrf(self, request):
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return
            
        # Estrategia SRE: Cross-Origin Resource Sharing (CORS) Trust
        # Si el Origen de la petición está en nuestra lista blanca de confianza (Vercel/Dominio),
        # podemos permitir la acción JWT sin el token CSRF manual, ya que el navegador
        # bloquea peticiones de orígenes no autorizados antes de llegar aquí.
        origin = request.META.get('HTTP_ORIGIN')
        from django.conf import settings
        if origin in settings.CORS_ALLOWED_ORIGINS or settings.DEBUG:
            return

        def dummy_get_response(request):
            return None
        check = CSRFCheck(dummy_get_response)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            # Error detallado para depuración en producción (SRE)
            raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            # Intentar obtener el token de la cookie HttpOnly
            raw_token = request.COOKIES.get('access_token')
            if raw_token is None:
                return None
        else:
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None

        try:
            # Validar el token usando la lógica base de SimpleJWT
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            
            # Ejecutar validación CSRF solo para solicitudes autenticadas vía Cookies
            if header is None:
                self.enforce_csrf(request)

            # Validaciones adicionales de estado de cuenta
            if user and not user.is_active:
                raise exceptions.AuthenticationFailed('Usuario inactivo', code='user_inactive')
                
            if user and getattr(user, 'status', 'ACTIVE') == 'BLOCKED':
                raise exceptions.PermissionDenied('Cuenta bloqueada', code='user_blocked')

            return user, validated_token
        except exceptions.AuthenticationFailed:
            # Re-lanzar errores de autenticación (usuario inactivo, bloqueado, etc)
            raise
        except Exception as e:
            # Para otros errores (token expirado, inválido), retornamos None 
            # solo si no hay un header presente (basado en cookies).
            # Si hay un header y falla, es mejor dejar que DRF falle.
            if header:
                raise
            return None
