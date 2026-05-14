import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import UserRoles
from apps.core.utils.encryption import EncryptedCharField

class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # AQUÍ ESTÁ LA MAGIA: Forzamos el rol de ADMIN de tus constantes
        extra_fields.setdefault("role", UserRoles.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        INACTIVE = "INACTIVE", "Inactivo"
        PENDING = "PENDING", "Pendiente de Aprobación"
        BLOCKED = "BLOCKED", "Bloqueado"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRoles.CHOICES, default=UserRoles.CLIENTE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    reputation_score = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    terms_accepted = models.BooleanField(default=False)
    
    # Datos de contacto y perfil (Encriptados)
    full_name = EncryptedCharField(max_length=512, blank=True, null=True)
    phone_number = EncryptedCharField(max_length=255, blank=True, null=True)
    document_type = models.CharField(max_length=20, blank=True, null=True)
    document_number = EncryptedCharField(max_length=255, blank=True, null=True)
    birth_date = EncryptedCharField(max_length=255, blank=True, null=True)

    # Auditoría y Seguridad de Sesión
    jwt_key = models.UUIDField(default=uuid.uuid4, help_text="Cambiar este valor invalida todos los access tokens del usuario.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users_user"

    def __str__(self):
        return f"{self.username} - {self.role}"

class UserSession(models.Model):
    """
    RASTREADOR DE SESIONES ACTIVAS:
    Permite el control de dispositivos y la invalidación de sesiones específicas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_session"
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.email} - {self.session_id} ({'Activa' if self.is_active else 'Inactiva'})"


# ============================================================
# Foto de perfil del usuario
# ============================================================
class ProfilePicture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile_picture',
        db_column='user_id',
    )
    image_url = models.TextField()
    public_id = models.CharField(max_length=255, blank=True, null=True)
    mime_type = models.CharField(max_length=50, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users_profile_picture"

    def __str__(self):
        return f"Foto de {self.user.email}"