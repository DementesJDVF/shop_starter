from django.contrib import admin
from apps.products.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "is_deleted", "created_at")
    list_filter = ("is_active", "is_deleted", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "vendor", "category", "status", "price", "stock", "is_deleted")
    list_filter = ("status", "is_deleted", "category", "created_at")
    search_fields = ("name", "description")