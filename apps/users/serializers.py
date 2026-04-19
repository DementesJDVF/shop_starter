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
    password_confirm = serializers.CharField(write_only=True, min_length=8, required=False)
    role = serializers.ChoiceField(choices=UserRoles.CHOICES, required=False, default=UserRoles.CUSTOMER)
    is_human = serializers.BooleanField(required=False, default=True)
    honeypot = serializers.CharField(required=False, allow_blank=True)
    birth_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "username", "email", "password", "password_confirm", "role",
            "full_name", "phone_number", "document_type", "document_number", "birth_date",
            "is_human", "honeypot"
        )

    def validate(self, attrs):
        # Soporte para alias 'nombre' -> 'full_name'
        if "nombre" in self.initial_data and not attrs.get("full_name"):
            attrs["full_name"] = self.initial_data["nombre"]

        # Si no viene username, usar el email (o parte de él) + random para evitar duplicados
        if not attrs.get("username") and attrs.get("email"):
            import random
            email = attrs["email"].lower().strip()
            attrs["email"] = email
            base_user = email.split("@")[0]
            attrs["username"] = f"{base_user}_{random.randint(100, 999)}"


        import re
        password = attrs.get("password", "")
        # Validación simplificada temporalmente para diagnóstico
        if not password or len(password) < 8:
            raise serializers.ValidationError({"password": "La contraseña debe tener al menos 8 caracteres."})

        if not attrs.get("is_human"):
            raise serializers.ValidationError({"is_human": "Debes marcar la casilla 'No soy un robot' (is_human: true)."})
            
        if attrs.get("honeypot"):
            # Si el campo trampa tiene datos, es probablemente un bot.
            raise serializers.ValidationError({"error": "Detección de actividad sospechosa (Honeypot)."})

            
        if attrs.get("password_confirm") and password != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})

        attrs.pop("password_confirm", None)

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
            
            # Intentar convertir el texto de birth_date a una fecha real para el modelo
            from django.utils.dateparse import parse_date
            import datetime
            date_str = attrs.get("birth_date")
            if date_str:
                parsed_date = None
                # Intentar varios formatos conocidos
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
            # Para clientes, simplemente ignoramos el birth_date o lo ponemos en None
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
        fields = '__all__'
    # Sobrescribimos el constructor para marcar todo como read_only dinámicamente
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].read_only = True
class ChangeUserRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRoles.CHOICES)