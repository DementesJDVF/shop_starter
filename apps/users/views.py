from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserSerializer
from .permissions import IsAdmin
from apps.audit.application.services import AuditService


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 🔎 Auditoría CREATE
        AuditService.log_create(
            user=user,  # él mismo se crea
            instance=user,
            ip_address=self._get_client_ip(request),
        )

        return Response({
            "message": "Usuario registrado exitosamente",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    def _get_client_ip(self, request):
        return request.META.get("REMOTE_ADDR")


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AdminOnlyView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({"message": "Acceso permitido solo para ADMIN"})
