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
        # Estrategia SRE: Cross-Origin Resource Sharing (CORS) Trust
        # La validación CSRF es OBLIGATORIA para cualquier petición que use Cookies.
        # No usamos bypass de Origin porque con SameSite=None el riesgo es real.

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
            
            # --- BLINDAJE DE SESIÓN ESTRICTO (jwt_key + UserSession) ---
            user_jwt_key = getattr(user, 'jwt_key', None)
            token_jwt_key = validated_token.get('jwt_key')
            session_id = validated_token.get('session_id')
            
            # Principio Fail-Secure: Si falta información crítica, rechazar.
            if not user_jwt_key or not token_jwt_key:
                raise exceptions.AuthenticationFailed(
                    'Token de seguridad incompleto. Inicia sesión de nuevo.',
                    code='invalid_token_integrity'
                )

            # 1. Validar integridad global (jwt_key)
            if str(user_jwt_key) != str(token_jwt_key):
                raise exceptions.AuthenticationFailed(
                    'Esta sesión ha sido invalidada globalmente.',
                    code='session_invalidated'
                )
            
            # 2. Validar estado de la sesión específica (UserSession)
            if not session_id:
                raise exceptions.AuthenticationFailed(
                    'Identificador de sesión no encontrado.',
                    code='missing_session'
                )

            from apps.users.models import UserSession
            if not UserSession.objects.filter(session_id=session_id, is_active=True).exists():
                raise exceptions.AuthenticationFailed(
                    'Tu sesión ha expirado o ha sido cerrada desde otro dispositivo.',
                    code='session_closed'
                )

            # Ejecutar validación CSRF solo para solicitudes autenticadas vía Cookies
            if header is None:
                self.enforce_csrf(request)

            # Validaciones adicionales de estado de cuenta
            if user and not user.is_active:
                raise exceptions.AuthenticationFailed('Usuario inactivo', code='user_inactive')
                
            if user and getattr(user, 'status', 'ACTIVE') == 'BLOCKED':
                raise exceptions.PermissionDenied('Cuenta bloqueada', code='user_blocked')

            return user, validated_token
        except exceptions.AuthenticationFailed as e:
            print(f"DEBUG AUTH: AuthenticationFailed: {str(e)}")
            raise
        except Exception as e:
            if not header:
                print(f"DEBUG AUTH: Cookie Auth failed silently: {type(e)} - {str(e)}")
                return None
            print(f"DEBUG AUTH: Header Auth failed: {type(e)} - {str(e)}")
            raise
