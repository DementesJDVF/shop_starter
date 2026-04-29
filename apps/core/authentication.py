from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
import logging


logger = logging.getLogger(__name__)

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
        auth_via = "header" if header is not None else "cookie"

        logger.debug("JWT auth started via=%s path=%s method=%s", auth_via, request.path, request.method)

        if header is None:
            # Intentar obtener el token de la cookie HttpOnly
            raw_token = request.COOKIES.get('access_token')
            if raw_token is None:
                logger.debug("JWT auth skipped: no Authorization header and no access_token cookie")
                return None
        else:
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                logger.warning("JWT auth failed: malformed Authorization header path=%s", request.path)
                return None

        try:
            # Validar el token usando la lógica base de SimpleJWT
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            logger.info("JWT token validated for user_id=%s path=%s", getattr(user, 'id', None), request.path)
            
            # --- BLINDAJE DE SESIÓN ESTRICTO (jwt_key + UserSession) ---
            user_jwt_key = getattr(user, 'jwt_key', None)
            token_jwt_key = validated_token.get('jwt_key')
            session_id = validated_token.get('session_id')
            
            # 1. Validar integridad de claims
            if not user_jwt_key or not token_jwt_key or not session_id:
                logger.warning("JWT integrity claims missing user_id=%s session_id=%s", getattr(user, 'id', None), session_id)
                raise exceptions.AuthenticationFailed('Token de seguridad incompleto.', code='invalid_token_integrity')

            # 2. Validar integridad global (jwt_key)
            if str(user_jwt_key) != str(token_jwt_key):
                logger.warning("JWT key mismatch for user_id=%s", getattr(user, 'id', None))
                raise exceptions.AuthenticationFailed('Esta sesión ha sido invalidada globalmente.', code='session_invalidated')
            
            # 3. Validar estado de la sesión específica (UserSession)
            from apps.users.models import UserSession
            if not UserSession.objects.filter(session_id=session_id, is_active=True).exists():
                logger.warning("JWT inactive session user_id=%s session_id=%s", getattr(user, 'id', None), session_id)
                raise exceptions.AuthenticationFailed('Tu sesión ha expirado o ha sido cerrada.', code='session_closed')

            # Ejecutar validación CSRF solo para solicitudes autenticadas vía Cookies
            if header is None:
                self.enforce_csrf(request)

            # Validaciones adicionales de estado de cuenta
            if user and not user.is_active:
                logger.warning("JWT inactive user_id=%s", getattr(user, 'id', None))
                raise exceptions.AuthenticationFailed('Usuario inactivo', code='user_inactive')
                
            if user and getattr(user, 'status', 'ACTIVE') == 'BLOCKED':
                logger.warning("JWT blocked user_id=%s", getattr(user, 'id', None))
                raise exceptions.PermissionDenied('Cuenta bloqueada', code='user_blocked')

            logger.info("JWT auth success user_id=%s via=%s", getattr(user, 'id', None), auth_via)
            return user, validated_token

        except (exceptions.AuthenticationFailed, exceptions.PermissionDenied) as e:
            # SRE STRATEGY: Si la autenticación por COOKIE falla en un endpoint público,
            # no debemos lanzar 401, sino retornar None para que DRF lo trate como Anonymous.
            # Esto soluciona los bloqueos en el catálogo para usuarios con cookies viejas.
            if header is None:
                logger.info("JWT cookie soft-fail path=%s reason=%s", request.path, str(e))
                return None
            logger.warning("JWT header auth rejected path=%s reason=%s", request.path, str(e))
            raise
        except Exception as e:
            logger.exception("JWT unexpected auth error path=%s via=%s", request.path, auth_via)
            if header is None:
                return None
            raise exceptions.AuthenticationFailed('Error interno validando token.', code='token_validation_error')
