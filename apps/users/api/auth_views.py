from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.application.services import AuditService
from apps.users.serializers import LoginSerializer, UserSerializer


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)

        AuditService.log_login(
            user=user,
            ip_address=self._get_client_ip(request),
        )

        return Response({
            "message": "Login exitoso",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        return request.META.get("REMOTE_ADDR")
