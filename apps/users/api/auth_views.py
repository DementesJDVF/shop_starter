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
from rest_framework_simplejwt.exceptions import InvalidToken
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
        
        is_secure = request.is_secure()
        samesite = 'None' if is_secure else 'Lax'

        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=is_secure,
            samesite=samesite,
            max_age=3600*24 # 1 día
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=is_secure,
            samesite=samesite,
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

        return Response(serializer_data, status=status.HTTP_200_OK)

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Intentar obtener el refresh token prioritariamente de la cookie httponly
        refresh_token = request.COOKIES.get('refresh_token')
        
        # Inyectar el token en el cuerpo de la solicitud para que el serializer de SimpleJWT lo procese
        if refresh_token:
            # Creamos un diccionario mutable con los datos actuales
            from django.http import QueryDict
            if isinstance(request.data, QueryDict):
                data = request.data.copy()
            else:
                data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            
            data['refresh'] = refresh_token
            # Sobrescribimos el atributo interno de DRF que alimenta a request.data
            request._full_data = data

        try:
            # Llamamos al comportamiento base (que usará el token inyectado)
            response = super().post(request, *args, **kwargs)
        except InvalidToken as e:
            # Si el token en la cookie es inválido (ej: expiró o fue manipulado)
            return Response({"detail": "Token de refresco inválido o expirado."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # DRF SimpleJWT responde con nuevo access_token (y opcional refresh).
        if response.status_code == 200:
            is_secure = request.is_secure()
            samesite = 'None' if is_secure else 'Lax'
            
            access_token = response.data.get('access')
            if access_token:
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    secure=is_secure,
                    samesite=samesite,
                    max_age=3600*24
                )
            
            new_refresh = response.data.get('refresh')
            if new_refresh:
                response.set_cookie(
                    key='refresh_token',
                    value=new_refresh,
                    httponly=True,
                    secure=is_secure,
                    samesite=samesite,
                    max_age=3600*24*7
                )
                
            # Limpiar payload por seguridad antes de devolver (Axios no necesita ver los tokens)
            response.data = {"message": "Sesión refrescada"}
            
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
        response = Response({"message": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
        # Limpiar cookies de autenticación y CSRF
        is_secure = request.is_secure()
        samesite = 'None' if is_secure else 'Lax'
        
        response.delete_cookie('access_token', samesite=samesite)
        response.delete_cookie('refresh_token', samesite=samesite)
        response.delete_cookie('csrftoken', samesite=samesite)
        return response
