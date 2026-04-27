from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.users.serializers import LoginSerializer, UserSerializer
from apps.users.services.auth_service import AuthService
from apps.core.middleware import get_client_ip_from_request, get_current_user_agent
from apps.users.throttles import LoginIPRateThrottle, LoginUserRateThrottle

@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):
    """
    VISTA DE LOGIN (ORQUESTADOR):
    Se encarga de recibir la petición, delegar la lógica al AuthService y 
    configurar las cookies seguras en la respuesta.
    """
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (LoginIPRateThrottle, LoginUserRateThrottle)

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data["user"]

            # Delegar al servicio (Lógica de Negocio + Auditoría)
            refresh = AuthService.login_user(
                user=user,
                ip_address=get_client_ip_from_request(request),
                user_agent=get_current_user_agent()
            )

            response = Response({
                "message": "Login exitoso",
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
            self._set_auth_cookies(response, refresh, request)
            return response
            
        except Exception as e:
            # Auditoría de fallo de login
            email = request.data.get('email', 'unknown')
            AuthService.log_failed_login(
                email=email,
                ip_address=get_client_ip_from_request(request),
                user_agent=get_current_user_agent(),
                reason=str(e)
            )
            raise e

    def _set_auth_cookies(self, response, refresh, request):
        from django.conf import settings
        is_prod = not settings.DEBUG
        cookie_secure = True if is_prod else request.is_secure()
        cookie_samesite = 'None' if is_prod or request.is_secure() else 'Lax'

        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            max_age=3600 # 1 hora (Acortado para seguridad)
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            max_age=3600*24*7 # 7 días
        )

class CustomTokenRefreshView(APIView):
    """
    VISTA DE REFRESCO (ORQUESTADOR):
    Permite obtener un nuevo Access Token usando el Refresh Token de la cookie.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        
        # Delegar al servicio
        refresh = AuthService.refresh_session(
            refresh_token_str=refresh_token,
            ip_address=get_client_ip_from_request(request),
            user_agent=get_current_user_agent()
        )

        response = Response({"message": "Sesión refrescada"}, status=status.HTTP_200_OK)
        
        # Actualizar cookies (Rotación de tokens)
        self._set_auth_cookies(response, refresh, request)
        return response

    def _set_auth_cookies(self, response, refresh, request):
        from django.conf import settings
        is_prod = not settings.DEBUG
        cookie_secure = True if is_prod else request.is_secure()
        cookie_samesite = 'None' if is_prod or request.is_secure() else 'Lax'
        
        response.set_cookie(
            key='access_token', value=str(refresh.access_token),
            httponly=True, secure=cookie_secure, samesite=cookie_samesite, max_age=3600
        )
        # Si SimpleJWT está configurado para rotar, habrá un nuevo refresh token
        response.set_cookie(
            key='refresh_token', value=str(refresh),
            httponly=True, secure=cookie_secure, samesite=cookie_samesite, max_age=3600*24*7
        )

class CSRFTokenView(APIView):
    """
    VISTA CSRF:
    Provee el token CSRF necesario para el frontend en peticiones seguras.
    """
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        from django.middleware.csrf import get_token
        return Response({"csrfToken": get_token(request)})

class UserView(APIView):
    """
    VISTA DE USUARIOS:
    Permite obtener la lista de usuarios (protegida para administradores).
    """
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        from apps.users.models import User
        from apps.users.serializers import UserSerializer
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class LogoutView(APIView):
    """
    VISTA DE LOGOUT (ORQUESTADOR):
    Invalida la sesión actual o todas las sesiones según se solicite.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        all_devices = request.data.get('all_devices', False)
        refresh_token = request.COOKIES.get('refresh_token')
        
        if all_devices:
            AuthService.logout_all_sessions(
                user=request.user,
                ip_address=get_client_ip_from_request(request),
                user_agent=get_current_user_agent()
            )
        else:
            AuthService.logout_user(
                refresh_token_str=refresh_token,
                user=request.user,
                ip_address=get_client_ip_from_request(request),
                user_agent=get_current_user_agent()
            )

        response = Response({"message": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
        
        # Limpiar cookies
        from django.conf import settings
        is_prod = not settings.DEBUG
        cookie_samesite = 'None' if is_prod or request.is_secure() else 'Lax'
        
        response.delete_cookie('access_token', samesite=cookie_samesite)
        response.delete_cookie('refresh_token', samesite=cookie_samesite)
        response.delete_cookie('csrftoken', samesite=cookie_samesite)
        
        return response
