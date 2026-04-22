from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        user_auth_tuple = super().authenticate(request)
        if user_auth_tuple is None:
            return None

        user, token = user_auth_tuple
        
        # Validación de seguridad: El usuario debe estar activo y NO estar bloqueado
        if not user.is_active:
            raise exceptions.AuthenticationFailed('Usuario inactivo', code='user_inactive')
            
        if getattr(user, 'status', 'ACTIVE') == 'BLOCKED':
            raise exceptions.PermissionDenied('Esta cuenta ha sido bloqueada por seguridad.', code='user_blocked')

        return user, token
