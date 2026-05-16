from django.contrib import admin
from apps.products.models import Category, Product


def categories_list(obj):
    return ", ".join([c.name for c in obj.categories.all()])
categories_list.short_description = "Categories"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "is_deleted", "created_at")
    list_filter = ("is_active", "is_deleted", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "vendor", "categories_list", "status", "price", "stock", "is_deleted")
    list_filter = ("status", "is_deleted", "created_at")
    search_fields = ("name", "description")

    def categories_list(self, obj):
        return categories_list(obj)
    categories_list.short_description = "Categories"