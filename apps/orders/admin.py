from django.contrib import admin
from .models import Order, OrderItem

# Register your models here.
from .models

















import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "vendor", "status")
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("id", "price_at_purchase")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "vendor", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("client__email", "vendor__user__email")
    inlines = [OrderItemInline]
    readonly_fields = ("id", "created_at", "updated_at")

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "price_at_purchase")
    readonly_fields = ("id",)
