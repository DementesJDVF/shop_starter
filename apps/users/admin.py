from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Campos que aparecen en la lista principal
    list_display = (
        "id",
        "email",
        "username",
        "role",
        "status",
        "is_staff",
        "is_active",
        "created_at",
    )
    
    # Filtros laterales
    list_filter = ("role", "status", "is_staff", "is_superuser", "is_active")
    
    # Campos por los que se puede buscar
    search_fields = ("email", "username")
    
    # Organización de los formularios de edición
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Información de Perfil", {"fields": ("role", "status")}),
        ("Datos de Verificación (Vendedores)", {"fields": ("phone_number", "document_type", "document_number", "birth_date", "expedition_date")}),
    )
    
    # Organización para el formulario de creación de usuario
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Información de Perfil", {"fields": ("role", "status")}),
    )
    
    actions = ["activate_users", "block_users"]

    @admin.action(description="Activar/Aprobar usuarios seleccionados")
    def activate_users(self, request, queryset):
        queryset.update(status=User.Status.ACTIVE, is_active=True)

    @admin.action(description="Bloquear usuarios seleccionados")
    def block_users(self, request, queryset):
        queryset.update(status=User.Status.BLOCKED, is_active=False)

    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")
# Register your models here.
     
