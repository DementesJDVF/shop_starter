from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck

class CustomJWTAuthentication(JWTAuthentication):
    def enforce_csrf(self, request):
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
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
            raw_token = request.COOKIES.get('access_token')
            if raw_token is not None:
                # Se envía como string plana, no codificado (dependiendo de JWTAuthentication internals)
                raw_token = raw_token.encode('utf-8')
        else:
            raw_token = self.get_raw_token(header)
            
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        
        # Inyectar Validacion CSRF Estricta (FAANG-001 mitigación)
        self.enforce_csrf(request)

        # Validación de seguridad: El usuario debe estar activo y NO estar bloqueado
        if not user.is_active:
            raise exceptions.AuthenticationFailed('Usuario inactivo', code='user_inactive')
            
        if getattr(user, 'status', 'ACTIVE') == 'BLOCKED':
            raise exceptions.PermissionDenied('Esta cuenta ha sido bloqueada por seguridad.', code='user_blocked')

        return user, validated_token
