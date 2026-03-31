from rest_framework import serializers

from .constants import UserRoles
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    correo_electronico = serializers.EmailField(source="email")
    nombre_completo = serializers.CharField(source="full_name", required=False, allow_blank=True)
    tipo_documento = serializers.ChoiceField(source="document_type", choices=User.DocumentType.choices, required=False)
    numero_documento = serializers.CharField(source="document_number", required=False, allow_blank=True)
    fecha_nacimiento = serializers.DateField(source="birth_date", required=False)
    fecha_expedicion = serializers.DateField(source="document_issue_date", required=False)
    telefono = serializers.CharField(source="phone", required=False, allow_blank=True)
    direccion = serializers.CharField(source="address", required=False, allow_blank=True)
    nombre_negocio = serializers.CharField(source="business_name", required=False, allow_blank=True)
    tipos_producto = serializers.CharField(source="product_types", required=False, allow_blank=True)
    contrasena = serializers.CharField(source="password", write_only=True, min_length=8)
    confirmar_contrasena = serializers.CharField(write_only=True, min_length=8)
    rol = serializers.ChoiceField(
        source="role",
        choices=[(role, label) for role, label in UserRoles.CHOICES if role in UserRoles.SELF_ASSIGNABLE],
        required=False,
        default=UserRoles.CUSTOMER,
    )


    class Meta:
        model = User
        fields = (
            "correo_electronico",
            "nombre_completo",
            "tipo_documento",
            "numero_documento",
            "fecha_nacimiento",
            "fecha_expedicion",
            "telefono",
            "direccion",
            "nombre_negocio",
            "tipos_producto",
            "contrasena",
            "confirmar_contrasena",
            "rol",
        )

    def validate(self, attrs):
        password = attrs.get("password")
        confirmar = self.initial_data.get("confirmar_contrasena")

        if password != confirmar:
            raise serializers.ValidationError({"contrasena": "Las contraseñas no coinciden"})

        role = attrs.get("role", UserRoles.CUSTOMER)
        if role not in UserRoles.SELF_ASSIGNABLE:
            raise serializers.ValidationError({"rol": "No es posible autoprovisionar este rol"})

        vendor_required_fields = [
            "full_name",
            "document_type",
            "document_number",
            "birth_date",
            "document_issue_date",
            "phone",
            "address",
            "business_name",
            "product_types",
        ]

        if role == UserRoles.VENDOR:
            missing = [field for field in vendor_required_fields if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError(
                    {field: "Este campo es obligatorio para registro de vendedor" for field in missing}
                )

        if attrs.get("document_issue_date") and attrs.get("birth_date") and attrs["document_issue_date"] < attrs["birth_date"]:
            raise serializers.ValidationError(
                {"document_issue_date": "La fecha de expedición no puede ser anterior a la fecha de nacimiento"}
            )

        return attrs

class CustomerRegisterSerializer(RegisterSerializer):
    rol = serializers.ChoiceField(
        source="role",
        choices=[(UserRoles.CUSTOMER, "Cliente")],
        required=False,
        default=UserRoles.CUSTOMER,
    )

    class Meta(RegisterSerializer.Meta):
        fields = (
            "correo_electronico",
            "contrasena",
            "confirmar_contrasena",
            "rol",
        )


class VendorRegisterSerializer(RegisterSerializer):
    rol = serializers.ChoiceField(
        source="role",
        choices=[(UserRoles.VENDOR, "Vendedor")],
        required=False,
        default=UserRoles.VENDOR,
    )

    class Meta(RegisterSerializer.Meta):
        fields = RegisterSerializer.Meta.fields


class LoginSerializer(serializers.Serializer):
    correo_electronico = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, required=False, style={"input_type": "password"})

    def to_internal_value(self, data):
        mutable_data = data.copy()

        if "correo_electronico" not in mutable_data and "email" in mutable_data:
            mutable_data["correo_electronico"] = mutable_data.get("email")

        if "password" not in mutable_data and "contrasena" in mutable_data:
            mutable_data["password"] = mutable_data.get("contrasena")

        return super().to_internal_value(mutable_data)


    def validate(self, data):
        email = data.get("correo_electronico")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError("Debes enviar correo y contraseña")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Credenciales inválidas")

        if not user.check_password(password):
            raise serializers.ValidationError("Credenciales inválidas")

        if not user.is_active:
            raise serializers.ValidationError("Usuario inactivo")

        # Staff y superusers pueden ingresar sin importar el status
        if not (user.is_staff or user.is_superuser):
            if user.status == User.Status.PENDING:
                raise serializers.ValidationError(
                    "Tu solicitud está pendiente de aprobación del administrador"
                )

            if user.status == User.Status.REJECTED:
                raise serializers.ValidationError(
                    "Tu solicitud fue negada. Debes volver a registrarte con un nuevo formulario"
                )

            if user.status != User.Status.ACTIVE:
                raise serializers.ValidationError("Usuario inactivo o bloqueado")

        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    correo_electronico = serializers.EmailField(source="email", read_only=True)
    nombre_completo = serializers.CharField(source="full_name", read_only=True)
    tipo_documento = serializers.CharField(source="document_type", read_only=True)
    numero_documento = serializers.CharField(source="document_number", read_only=True)
    fecha_nacimiento = serializers.DateField(source="birth_date", read_only=True)
    fecha_expedicion = serializers.DateField(source="document_issue_date", read_only=True)
    telefono = serializers.CharField(source="phone", read_only=True)
    direccion = serializers.CharField(source="address", read_only=True)
    nombre_negocio = serializers.CharField(source="business_name", read_only=True)
    tipos_producto = serializers.CharField(source="product_types", read_only=True)
    rol = serializers.CharField(source="role", read_only=True)
    estado = serializers.CharField(source="status", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "correo_electronico",
            "nombre_completo",
            "tipo_documento",
            "numero_documento",
            "fecha_nacimiento",
            "fecha_expedicion",
            "telefono",
            "direccion",
            "nombre_negocio",
            "tipos_producto",
            "rol",
            "estado",
            "is_active",
        ]
        read_only_fields = fields


class ChangeUserRoleSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(choices=UserRoles.CHOICES, required=False)
    role = serializers.ChoiceField(choices=UserRoles.CHOICES, required=False)

    def validate(self, attrs):
        role = attrs.get("rol") or attrs.get("role")
        if not role:
            raise serializers.ValidationError({"rol": "Este campo es obligatorio"})
        return {"role": role}


class ChangeUserStatusSerializer(serializers.Serializer):

    STATUS_ALIASES = {
        "ACTIVO": User.Status.ACTIVE,
        "ACTIVE": User.Status.ACTIVE,
        "PENDIENTE": User.Status.PENDING,
        "PENDING": User.Status.PENDING,
        "NEGADO": User.Status.REJECTED,
        "DENEGADO": User.Status.REJECTED,
        "RECHAZADO": User.Status.REJECTED,
        "REJECTED": User.Status.REJECTED,
        "INACTIVO": User.Status.INACTIVE,
        "INACTIVE": User.Status.INACTIVE,
        "BLOQUEADO": User.Status.BLOCKED,
        "BLOCKED": User.Status.BLOCKED,
    }

    estado = serializers.CharField(required=False)
    status = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        status = attrs.get("estado") or attrs.get("status")
        if not status:
            raise serializers.ValidationError({"estado": "Este campo es obligatorio"})

        normalized_status = self.STATUS_ALIASES.get(str(status).strip().upper())
        if not normalized_status:
            allowed = ", ".join(sorted(self.STATUS_ALIASES.keys()))
            raise serializers.ValidationError(
                {"estado": f"Estado inválido. Valores permitidos: {allowed}"}
            )

        return {"status": normalized_status}