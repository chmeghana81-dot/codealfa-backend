from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "full_name", "mobile",
        "total_amount", "payment_method",
        "payment_status", "status", "created_at"
    )
    list_filter = ("status", "payment_status", "payment_method", "created_at")
    search_fields = ("id", "user__username", "user__email", "full_name", "mobile")
    readonly_fields = ("created_at",)
    inlines = [OrderItemInline]
    list_per_page = 25


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "price")
    search_fields = ("order__id", "product__name")
    list_per_page = 25
