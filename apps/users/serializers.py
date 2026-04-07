from django.db.models import Q
from rest_framework import serializers

from .constants import UserRoles
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserRoles.CHOICES, required=False, default=UserRoles.CUSTOMER)

    class Meta:
        model = User
        fields = ("username", "email", "password", "password_confirm", "role")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})

        attrs.pop("password_confirm")

        role = attrs.get("role", UserRoles.CUSTOMER)
        if role not in UserRoles.SELF_ASSIGNABLE:
            raise serializers.ValidationError({"role": "No es posible autoprovisionar este rol"})

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

        if not user.is_active:
            raise serializers.ValidationError("Usuario inactivo")

        data["email"] = email
        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "is_active"]
        read_only_fields = fields


class ChangeUserRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRoles.CHOICES)
    