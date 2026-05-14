from django.db.models import Q
from rest_framework import serializers

from .constants import UserRoles
from .models import User, ProfilePicture


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "role", "is_active"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8, required=False)
    role = serializers.ChoiceField(choices=UserRoles.CHOICES, required=False, default=UserRoles.CUSTOMER)
    is_human = serializers.BooleanField(required=False, default=True)
    honeypot = serializers.CharField(required=False, allow_blank=True)
    birth_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    terms_accepted = serializers.BooleanField(default=False)
    class Meta:
        model = User
        fields = (
            "username", "email", "password", "password_confirm", "role",
            "full_name", "phone_number", "document_type", "document_number", "birth_date",
            "is_human", "honeypot", "terms_accepted"
        )

    def validate_email(self, value):
        email = (value or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return email

    def validate_username(self, value):
        username = (value or "").strip()
        if username and User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def validate(self, attrs):
        if "nombre" in self.initial_data and not attrs.get("full_name"):
            attrs["full_name"] = self.initial_data["nombre"]

        if not attrs.get("username") and attrs.get("email"):
            import random
            email = attrs["email"].lower().strip()
            attrs["email"] = email
            base_user = email.split("@")[0]
            attrs["username"] = f"{base_user}_{random.randint(100, 999)}"

        import re
        password = attrs.get("password", "")
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError({"password": "La contraseña debe contener al menos una letra mayúscula."})
        if not re.search(r'[0-9]', password):
            raise serializers.ValidationError({"password": "La contraseña debe contener al menos un número."})
        if not re.search(r'[@#$%^&+=!¡¿?*]', password):
            raise serializers.ValidationError({"password": "La contraseña debe contener al menos un carácter especial (@, $, !, %, *, #, ?, &)."})

        if not attrs.get("is_human"):
            raise serializers.ValidationError({"is_human": "Debes marcar la casilla 'No soy un robot' (is_human: true)."})

        if attrs.get("honeypot"):
            from apps.audit.application.services import AuditService
            from apps.users.models import User
            AuditService._log(
                user=None,
                action_type="SUSPICIOUS_REGISTRATION",
                instance=User(),
                is_suspicious=True,
                new_data={"reason": "Bot detectado via Honeypot trampa", "details": attrs.get("honeypot")}
            )
            raise serializers.ValidationError({"error": "Detección de actividad sospechosa (Honeypot)."})

        if attrs.get("password_confirm") and password != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})

        attrs.pop("password_confirm", None)

        role = attrs.get("role", UserRoles.CUSTOMER)
        if role not in UserRoles.SELF_ASSIGNABLE:
            raise serializers.ValidationError({"role": "No es posible autoprovisionar este rol"})

        if role == UserRoles.VENDOR:
            required_vendor_fields = [
                "full_name", "phone_number", "document_type", "document_number", "birth_date"
            ]
            for field in required_vendor_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: "Este campo es obligatorio para vendedores."})

            from django.utils.dateparse import parse_date
            import datetime
            date_str = attrs.get("birth_date")
            if date_str:
                parsed_date = None
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
                    try:
                        parsed_date = datetime.datetime.strptime(date_str, fmt).date()
                        break
                    except (ValueError, TypeError):
                        continue
                if not parsed_date:
                    raise serializers.ValidationError({"birth_date": "Formato de fecha inválido. Usa AAAA-MM-DD o DD/MM/AAAA."})
                attrs["birth_date"] = parsed_date
        else:
            attrs["birth_date"] = None

        attrs.pop("is_human", None)
        attrs.pop("honeypot", None)
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        users_qs = User.objects.filter(email__iexact=email).order_by("id")
        user_count = users_qs.count()

        if user_count == 0:
            raise serializers.ValidationError("Credenciales inválidas. Verifica el email y contraseña")

        if user_count > 1:
            raise serializers.ValidationError("Credenciales inválidas. Verifica el email y contraseña")

        user = users_qs.first()

        if not user.check_password(password):
            raise serializers.ValidationError({"non_field_errors": ["Contraseña incorrecta."]})

        if user.status == User.Status.PENDING:
            raise serializers.ValidationError({"detail": "SU INFORMACIÓN ESTÁ SIENDO REVISADA, EN UN MOMENTO PODRÁ INICIAR SESIÓN"})

        if user.status == User.Status.BLOCKED:
            raise serializers.ValidationError({"detail": "Su cuenta ha sido bloqueada por un administrador."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Usuario inactivo"})

        data["email"] = email
        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "status", "is_active", "reputation_score"]
        read_only_fields = fields


class UserSerializerAll(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "status"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].read_only = True


class ChangeUserRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRoles.CHOICES)


# ============================================================
# NUEVO: Foto de perfil
# ============================================================
class ProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePicture
        fields = ["id", "image_url", "public_id", "mime_type", "file_size", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


# ============================================================
# NUEVO: Perfil completo del usuario (Mi Perfil)
# Devuelve campos editables según rol.
# ============================================================
class MyProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    editable_fields = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "role", "status", "is_active",
            "reputation_score",
            "full_name", "phone_number", "document_type", "document_number", "birth_date",
            "created_at", "updated_at",
            "profile_picture", "editable_fields",
        ]
        read_only_fields = ["id", "role", "status", "is_active", "reputation_score", "created_at", "updated_at"]

    def get_profile_picture(self, obj):
        pic = getattr(obj, 'profile_picture', None)
        if pic and pic.is_active:
            return ProfilePictureSerializer(pic).data
        return None

    def get_editable_fields(self, obj):
        # Campos que cada rol puede modificar (coinciden con los del registro)
        common = ["username", "email", "full_name", "phone_number"]
        if obj.role == UserRoles.VENDOR:
            return common + ["document_type", "document_number", "birth_date"]
        if obj.role == UserRoles.ADMIN:
            return common + ["document_type", "document_number", "birth_date"]
        # CLIENTE
        return common

    def validate_email(self, value):
        value = (value or "").strip().lower()
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value

    def validate_username(self, value):
        value = (value or "").strip()
        if value and User.objects.filter(username__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value

    def update(self, instance, validated_data):
        # Solo permitir actualizar los campos declarados como editables
        allowed = set(self.get_editable_fields(instance))
        for field, value in validated_data.items():
            if field in allowed:
                setattr(instance, field, value)
        instance.save()
        return instance