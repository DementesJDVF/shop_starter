from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


#Acciones personalizadas
@admin.action(description="Aprobar usuarios seleccionados")
def aprobar_usuarios(modeladmin, request, queryset):
    queryset.update(status=User.Status.ACTIVE)


@admin.action(description="Rechazar usuarios seleccionados")
def rechazar_usuarios(modeladmin, request, queryset):
    queryset.update(status=User.Status.REJECTED)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    # 🔍 Lista principal
    list_display = (
        "id",
        "email",
        "full_name",
        "role",
        "status",
        "is_active",
    )

    list_filter = (
        "role",
        "status",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "email",
        "full_name",
        "document_number",
    )

    ordering = ("email",)

    # 🧾 Edición de usuario (TODO EN ESPAÑOL)
    fieldsets = (
        ("Credenciales", {
            "fields": ("email", "password")
        }),
        ("Información personal", {
            "fields": (
                "full_name",
                "document_type",
                "document_number",
                "birth_date",
                "document_issue_date",
                "phone",
                "address",
            )
        }),
        ("Información del negocio", {
            "fields": (
                "business_name",
                "product_types",
            )
        }),
        ("Permisos", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),
        ("Rol y estado", {
            "fields": (
                "role",
                "status",
            )
        }),
    )

    # ➕ Crear usuario
    add_fieldsets = (
        ("Crear usuario", {
            "classes": ("wide",),
            "fields": (
                "email",
                "username",
                "password1",
                "password2",
                "role",
                "status",
                "is_active",
                "is_staff",
            ),
        }),
    )

    #Acciones rápidas
    actions = [aprobar_usuarios, rechazar_usuarios]
