from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User  # ← CAMBIAR: CustomUser → User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User  # ← CAMBIAR: CustomUser → User
        fields = ('username', 'email', 'password', 'password_confirm', 'role')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        if len(attrs['password']) < 8:
            raise serializers.ValidationError({"password": "La contraseña debe tener al menos 8 caracteres"})
        attrs.pop('password_confirm')
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(  # ← CAMBIAR: CustomUser → User
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'CUSTOMER')
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        try:
            user = User.objects.get(email=email)  # ← CAMBIAR: CustomUser → User
        except User.DoesNotExist:  # ← CAMBIAR: CustomUser → User
            raise serializers.ValidationError("Credenciales inválidas")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Credenciales inválidas")
        
        if not user.is_active:
            raise serializers.ValidationError("Usuario inactivo")
        
        data['user'] = user
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # ← CAMBIAR: CustomUser → User
        fields = ('id', 'username', 'email', 'role', 'is_active', 'date_joined')