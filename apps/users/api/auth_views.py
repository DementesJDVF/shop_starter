from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.middleware import get_client_ip_from_request
from apps.users.application.services import UserService
from apps.users.serializers import LoginSerializer, UserSerializer, UserSerializerAll
from apps.users.throttles import LoginRateThrottle
from apps.users.models import User
class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (LoginRateThrottle,)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = UserService.login_user(
            user=user,
            ip_address=get_client_ip_from_request(request),
        )
        return Response(
            {
                "message": "Login exitoso",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
class UserView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, recuest):
        users = User.objects.all()
        return Response(
            UserSerializerAll(users, many=True) .data,
            status=status.HTTP_200_OK)
