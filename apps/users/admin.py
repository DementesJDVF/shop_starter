from django.contrib import admin
from .models import User

admin.site.register(User)
# Register your models here.
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("email",)