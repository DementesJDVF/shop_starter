from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.viewsets import ModelViewSet
from apps.users.models import User

from apps.core.middleware import get_client_ip_from_request
from apps.users.application.services import UserService
from apps.users.serializers import LoginSerializer, UserSerializer, UserSerializerAll
from apps.users.throttles import LoginRateThrottle
from apps.users.models import User
class LoginView(APIView):
    serializer_class = LoginSerializer
    parser_classes = (JSONParser, FormParser, MultiPartParser)
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
