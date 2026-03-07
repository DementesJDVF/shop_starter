from rest_framework import serializers
from .models import User
from .constants import UserRoles


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        if len(attrs['password']) < 8:
            raise serializers.ValidationError({"password": "La contraseña debe tener al menos 8 caracteres"})
        attrs.pop('password_confirm')
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role='CLIENTE'
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Credenciales inválidas")

        if not user.check_password(password):
            raise serializers.ValidationError("Credenciales inválidas")

        if not user.is_active:
            raise serializers.ValidationError("Usuario inactivo")

        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "role",
            "is_active",
        ]
        read_only_fields = fields


class ChangeUserRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRoles.CHOICES)
