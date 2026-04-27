from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.viewsets import ModelViewSet
from apps.users.models import User

from apps.core.middleware import get_client_ip_from_request
from apps.users.application.services import UserService
from apps.users.serializers import LoginSerializer, UserSerializer, UserSerializerAll
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from apps.users.models import User
from apps.users.permissions import IsAdmin
from apps.users.throttles import LoginRateThrottle

@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):
    serializer_class = LoginSerializer
    authentication_classes = []
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (LoginRateThrottle,)

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def get_throttles(self):
        if self.request.method == "POST":
            return super().get_throttles()
        return []

    def get(self, request):
        saved_logins = request.session.get("saved_logins", [])[:10]
        return Response(
            saved_logins,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        saved_logins = request.session.get("saved_logins", [])
        login_entry = {"email": user.email}

        saved_logins = [entry for entry in saved_logins if entry != login_entry]
        saved_logins.insert(0, login_entry)
        request.session["saved_logins"] = saved_logins[:10]

        refresh = UserService.login_user(
            user=user,
            ip_address=get_client_ip_from_request(request),)

        response_data = {
            "message": "Login exitoso",
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

        response = Response(
            response_data,
            status=status.HTTP_200_OK,
        )
        
        from django.conf import settings
        # En producción (Vercel -> Railway), SameSite=None y Secure=True son OBLIGATORIOS
        # para que las cookies viajen entre dominios diferentes.
        is_prod = not settings.DEBUG
        cookie_secure = True if is_prod else request.is_secure()
        cookie_samesite = 'None' if is_prod or request.is_secure() else 'Lax'

        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            max_age=3600*24 # 1 día
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            max_age=3600*24*7 # 7 días
        )
        
        return response

class UserView(APIView):
    permission_classes =  (permissions.IsAuthenticated, IsAdmin)
    def get(self, request):
        search_query = request.query_params.get('search', '').lower()
        users = User.objects.all()
        
        serializer_data = UserSerializerAll(users, many=True).data
        
        if search_query:
            # Filter in-memory since database searching on encrypted fields is not possible directly
            filtered_data = []
            for user_data in serializer_data:
                # Search in important fields (case-insensitive)
                searchable_text = f"{user_data.get('email', '')} {user_data.get('full_name', '')} {user_data.get('document_number', '')} {user_data.get('phone_number', '')}".lower()
                if search_query in searchable_text:
                    filtered_data.append(user_data)
            serializer_data = filtered_data

        return Response(serializer_data, status=status.HTTP_200_OK)class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # 1. Extraer el refresh token de la cookie HttpOnly prioritariamente
        refresh_token = request.COOKIES.get('refresh_token')
        
        # Inyectar el token en el cuerpo de la solicitud para el serializer
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if refresh_token:
            data['refresh'] = refresh_token

        serializer = self.get_serializer(data=data)

        try:
            # 2. Validar el token. Si está en Blacklist o expirado, lanzará TokenError/InvalidToken
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken):
            return Response(
                {"detail": "La sesión ha expirado o es inválida. Inicia sesión de nuevo."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Generar respuesta y actualizar cookies
        response = Response({"message": "Sesión refrescada"}, status=status.HTTP_200_OK)
        
        from django.conf import settings
        is_prod = not settings.DEBUG
        cookie_secure = True if is_prod else request.is_secure()
        cookie_samesite = 'None' if is_prod or request.is_secure() else 'Lax'
        
        access_token = serializer.validated_data.get('access')
        if access_token:
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=cookie_secure,
                samesite=cookie_samesite,
                max_age=3600*24
            )
        
        new_refresh = serializer.validated_data.get('refresh')
        if new_refresh:
            response.set_cookie(
                key='refresh_token',
                value=new_refresh,
                httponly=True,
                secure=cookie_secure,
                samesite=cookie_samesite,
                max_age=3600*24*7
            )
            
        return response

class CSRFTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        from django.middleware.csrf import get_token
        return Response({"csrfToken": get_token(request)})

class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return self.post(request)

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        
        try:
            # 1. Intentar invalidar el refresh token en el servidor (Blacklist)
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception as e:
            # Si el token ya expiró o es inválido, ignoramos el error y procedemos a borrar cookies
            pass

        response = Response({"message": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
        
        # 2. Limpiar cookies de autenticación y CSRF
        from django.conf import settings
        is_prod = not settings.DEBUG
        cookie_samesite = 'None' if is_prod or request.is_secure() else 'Lax'
        
        response.delete_cookie('access_token', samesite=cookie_samesite)
        response.delete_cookie('refresh_token', samesite=cookie_samesite)
        response.delete_cookie('csrftoken', samesite=cookie_samesite)
        
        return response
