from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.middleware import get_client_ip_from_request
from .application.services import UserService
from .models import User
from .permissions import IsAdmin, IsClient, IsVendor
from .serializers import ChangeUserRoleSerializer, RegisterSerializer, UserSerializer
from .throttles import RegisterRateThrottle

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from apps.users.models import User
from apps.users.serializers import UserAdminSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (RegisterRateThrottle,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserService.register_user(
            validated_data=serializer.validated_data,
            ip_address=get_client_ip_from_request(request),
        )

        return Response(
            {
                "message": "Usuario registrado exitosamente",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AdminOnlyView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({"message": "Acceso permitido solo para ADMIN"})


class VendorOnlyView(APIView):
    permission_classes = [IsVendor]

    def get(self, request):
        return Response({"message": "Acceso permitido solo para VENDEDOR"})


class CustomerOnlyView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        return Response({"message": "Acceso permitido solo para CLIENTE"})


class ChangeUserRoleView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, user_id):
        serializer = ChangeUserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_user = get_object_or_404(User, id=user_id)

        updated_user = UserService.change_role(
            admin_user=request.user,
            target_user=target_user,
            new_role=serializer.validated_data["role"],
            ip_address=get_client_ip_from_request(request),
        )

        return Response(
            {
                "message": "Rol actualizado",
                "user": UserSerializer(updated_user).data,
            },
            status=status.HTTP_200_OK,
        )

class AdminUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer

    def get_permissions(self):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("No autenticado")

        if self.request.user.role != "ADMIN":
            raise PermissionDenied("No tienes permisos")

        return [IsAuthenticated()]