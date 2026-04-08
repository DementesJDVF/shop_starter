from rest_framework import serializers

from .constants import UserRoles
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserRoles.CHOICES, required=False, default=UserRoles.CUSTOMER)

    class Meta:
        model = User
        fields = (
            "username", "email", "password", "password_confirm", "role",
            "full_name", "phone_number", "document_type", "document_number", "birth_date", "expedition_date"
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})

        attrs.pop("password_confirm")

        role = attrs.get("role", UserRoles.CUSTOMER)
        if role not in UserRoles.SELF_ASSIGNABLE:
            raise serializers.ValidationError({"role": "No es posible autoprovisionar este rol"})

        # Validación condicional para Vendedores
        if role == UserRoles.VENDOR:
            required_vendor_fields = [
                "full_name", "phone_number", "document_type", "document_number", "birth_date", "expedition_date"
            ]
            for field in required_vendor_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: "Este campo es obligatorio para vendedores."})

        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Credenciales inválidas")

        if not user.check_password(password):
            raise serializers.ValidationError("Credenciales inválidas")

        if user.status == User.Status.PENDING:
            raise serializers.ValidationError("SU INFORMACIÓN ESTÁ SIENDO REVISADA, EN UN MOMENTO PODRÁ INICIAR SESIÓN")

        if user.status == User.Status.BLOCKED:
            raise serializers.ValidationError("Su cuenta ha sido bloqueada por un administrador.")

        if not user.is_active:
            raise serializers.ValidationError("Usuario inactivo")

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
