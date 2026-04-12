from django.db.models import Q
from rest_framework import serializers

from .constants import UserRoles
from .models import User


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "role", "is_active"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserRoles.CHOICES, required=False, default=UserRoles.CUSTOMER)
    is_human = serializers.BooleanField(required=True)
    honeypot = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "username", "email", "password", "password_confirm", "role",
            "full_name", "phone_number", "document_type", "document_number", "birth_date",
            "is_human", "honeypot"
        )

    def validate(self, attrs):
        import re
        password = attrs.get("password", "")
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError({"password": "La contraseña debe contener al menos una letra mayúscula."})
        if not re.search(r'[0-9]', password):
            raise serializers.ValidationError({"password": "La contraseña debe contener al menos un número."})
        if not re.search(r'[@#$%^&+=!¡¿?*]', password):
            raise serializers.ValidationError({"password": "La contraseña debe contener al menos un carácter especial (@, $, !, %, *, #, ?, &)."})
            
        if not attrs.get("is_human"):
            raise serializers.ValidationError({"is_human": "Debes confirmar que no eres un robot."})
            
        if attrs.get("honeypot"):
            # Si el campo trampa tiene datos, es probablemente un bot.
            raise serializers.ValidationError({"error": "Detección de actividad sospechosa (Bot detectado)."})
            
        if password != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})

        attrs.pop("password_confirm")

        role = attrs.get("role", UserRoles.CUSTOMER)
        if role not in UserRoles.SELF_ASSIGNABLE:
            raise serializers.ValidationError({"role": "No es posible autoprovisionar este rol"})

        # Validación condicional para Vendedores
        if role == UserRoles.VENDOR:
            required_vendor_fields = [
                "full_name", "phone_number", "document_type", "document_number", "birth_date"
            ]
            for field in required_vendor_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: "Este campo es obligatorio para vendedores."})

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
            raise serializers.ValidationError("Credenciales inválidas. Verifica el email y contraseña")

        if user.status == User.Status.PENDING:
            raise serializers.ValidationError("SU INFORMACIÓN ESTÁ SIENDO REVISADA, EN UN MOMENTO PODRÁ INICIAR SESIÓN")

        if user.status == User.Status.BLOCKED:
            raise serializers.ValidationError("Su cuenta ha sido bloqueada por un administrador.")

        if not user.is_active:
            raise serializers.ValidationError("Usuario inactivo")

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
        fields = '__all__'
    # Sobrescribimos el constructor para marcar todo como read_only dinámicamente
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].read_only = True
class ChangeUserRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRoles.CHOICES)