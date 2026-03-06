from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.middleware import get_client_ip_from_request
from .serializers import RegisterSerializer, UserSerializer
from .permissions import IsAdmin
from .application.services import UserService


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserService.register_user(
            validated_data=serializer.validated_data,
            ip_address=get_client_ip_from_request(request),
        )

        return Response({
            "message": "Usuario registrado exitosamente",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AdminOnlyView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({"message": "Acceso permitido solo para ADMIN"})
