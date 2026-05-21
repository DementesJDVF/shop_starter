from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.core.middleware import get_client_ip_from_request
from .application.services import UserService
from .models import User, ProfilePicture
from .permissions import IsAdmin, IsClient, IsVendor
from .serializers import (
    ChangeUserRoleSerializer,
    RegisterSerializer,
    UserSerializer,
    UserAdminSerializer,
    MyProfileSerializer,
    ProfilePictureSerializer,
)
from .throttles import RegisterRateThrottle
from apps.core.services.email_service import send_welcome_email
from apps.users.constants import UserRoles

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    authentication_classes = []
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (RegisterRateThrottle,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserService.register_user(
            validated_data=serializer.validated_data,
            ip_address=get_client_ip_from_request(request),
        )
        if user.role in [UserRoles.CUSTOMER, UserRoles.VENDOR]:
            send_welcome_email(user)

        return Response(
            {
                "message": "Usuario registrado exitosamente",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    permission_classes = (permissions.AllowAny,)

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"isAuthenticated": False, "user": None}, status=status.HTTP_200_OK)
        
        serializer = UserSerializer(request.user)
        data = serializer.data
        data["isAuthenticated"] = True
        return Response(data)


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
        
        if new_status == User.Status.ACTIVE:
            target_user.is_active = True
        elif new_status in [User.Status.BLOCKED, User.Status.INACTIVE]:
            target_user.is_active = False
            
        target_user.save()

        if old_status != new_status and new_status in [User.Status.ACTIVE, User.Status.BLOCKED]:
            from apps.users.tasks import send_user_status_notification_task
            send_user_status_notification_task.delay(target_user.id)
        # Send welcome email to vendor upon activation
        if target_user.role == UserRoles.VENDOR and new_status == User.Status.ACTIVE:
            send_welcome_email(target_user)

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


# ============================================================
# NUEVO: Mi Perfil (GET y PATCH)
# ============================================================
class MyProfileView(APIView):
    """GET y PATCH del perfil propio. Funciona para ADMIN, VENDEDOR y CLIENTE."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MyProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = MyProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Perfil actualizado", "user": serializer.data})


# ============================================================
# NUEVO: Foto de perfil (GET, POST/PUT, DELETE)
# ============================================================
class MyProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        pic = ProfilePicture.objects.filter(user=request.user, is_active=True).first()
        if not pic:
            return Response({"profile_picture": None})
        return Response(ProfilePictureSerializer(pic).data)

    def post(self, request):
        """Crea o actualiza la foto. Acepta:
        - multipart con campo 'image' (archivo) → sube a Cloudinary si está configurado.
        - JSON con campo 'image_url' (URL directa).
        """
        image_url = request.data.get('image_url')
        public_id = None
        mime_type = None
        file_size = None

        if 'image' in request.FILES:
            image_file = request.FILES['image']
            mime_type = image_file.content_type
            file_size = image_file.size
            try:
                import cloudinary.uploader
                result = cloudinary.uploader.upload(
                    image_file,
                    folder=f"avatars/{request.user.id}",
                    overwrite=True,
                    resource_type="image",
                )
                image_url = result.get('secure_url')
                public_id = result.get('public_id')
            except Exception as e:
                # Fallback: guardar como base64 si Cloudinary no está disponible
                import base64
                content = image_file.read()
                b64 = base64.b64encode(content).decode('utf-8')
                image_url = f"data:{mime_type};base64,{b64}"

        if not image_url:
            return Response({"error": "Debes enviar 'image' (archivo) o 'image_url' (URL)."}, status=status.HTTP_400_BAD_REQUEST)

        pic, _created = ProfilePicture.objects.update_or_create(
            user=request.user,
            defaults={
                'image_url': image_url,
                'public_id': public_id,
                'mime_type': mime_type,
                'file_size': file_size,
                'is_active': True,
            }
        )
        return Response(ProfilePictureSerializer(pic).data, status=status.HTTP_200_OK)

    def delete(self, request):
        pic = ProfilePicture.objects.filter(user=request.user).first()
        if not pic:
            return Response(status=status.HTTP_204_NO_CONTENT)
        pic.is_active = False
        pic.save()
        return Response(status=status.HTTP_204_NO_CONTENT)