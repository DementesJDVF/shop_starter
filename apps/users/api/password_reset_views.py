from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
import re

from apps.users.models import User
from apps.core.services.email_service import send_password_reset_email

class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "El correo es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Por seguridad, no revelamos si el email existe o no
            return Response({"message": "Si el correo está registrado, recibirás un enlace de recuperación."}, status=status.HTTP_200_OK)

        # Generar Token y UID
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Construir URL del frontend
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        reset_url = f"{frontend_url}/auth/reset-password?uid={uid}&token={token}"
        
        # Enviar correo
        if send_password_reset_email(user, reset_url):
            return Response({"message": "Enlace de recuperación enviado exitosamente."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No se pudo enviar el correo en este momento."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConfirmPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('password')

        if not all([uidb64, token, new_password]):
            return Response({"error": "Faltan datos obligatorios"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            # Validación de fortaleza de contraseña (mismo regex que en RegisterSerializer)
            if len(new_password) < 8:
                return Response({"error": "La contraseña debe tener al menos 8 caracteres."}, status=status.HTTP_400_BAD_REQUEST)
            if not re.search(r'[A-Z]', new_password):
                return Response({"error": "La contraseña debe contener al menos una letra mayúscula."}, status=status.HTTP_400_BAD_REQUEST)
            if not re.search(r'[0-9]', new_password):
                return Response({"error": "La contraseña debe contener al menos un número."}, status=status.HTTP_400_BAD_REQUEST)
            if not re.search(r'[@#$%^&+=!¡¿?*]', new_password):
                return Response({"error": "La contraseña debe contener al menos un carácter especial."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            import uuid
            user.jwt_key = uuid.uuid4()
            user.save()
            
            # Auditoría
            from apps.audit.application.services import AuditService
            AuditService._log(user=user, action_type="PASSWORD_RESET_SUCCESS", instance=user)
            
            return Response({"message": "Tu contraseña ha sido restablecida con éxito."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "El enlace es inválido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)
