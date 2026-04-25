from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.middleware import get_client_ip_from_request
from .application.services import UserService
from .models import User
from .permissions import IsAdmin, IsClient, IsVendor
from .serializers import (
    ChangeUserRoleSerializer,
    RegisterSerializer,
    UserSerializer,
    UserAdminSerializer,
)
from .throttles import RegisterRateThrottle
from apps.core.services.email_service import send_user_status_notification

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    authentication_classes = []  # IMPORTANTE: No validar tokens en registro para evitar errores con sesiones expiradas
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


class ChangeUserStatusView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, user_id):
        VALID_STATUSES = [User.Status.ACTIVE, User.Status.INACTIVE, User.Status.PENDING, User.Status.BLOCKED]
        new_status = request.data.get('status')
        if new_status not in VALID_STATUSES:
            return Response({'error': f'Estado inválido. Opciones: {VALID_STATUSES}'}, status=status.HTTP_400_BAD_REQUEST)

        target_user = get_object_or_404(User, id=user_id)
        old_status = target_user.status
        target_user.status = new_status
        
        # Sincronizar is_active con el status para permitir/bloquear el login
        if new_status == User.Status.ACTIVE:
            target_user.is_active = True
        elif new_status in [User.Status.BLOCKED, User.Status.INACTIVE]:
            target_user.is_active = False
            
        target_user.save()

        # Notificar si el estado cambió a ACTIVE o BLOCKED usando Celery Backend
        if old_status != new_status and new_status in [User.Status.ACTIVE, User.Status.BLOCKED]:
            from apps.users.tasks import send_user_status_notification_task
            send_user_status_notification_task.delay(target_user.id)


        return Response(
            {
                "message": "Estado actualizado correctamente",
                "user": UserSerializer(target_user).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
