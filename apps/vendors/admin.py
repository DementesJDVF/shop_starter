from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import VendorProfile

@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status")
    list_filter = ("status",)