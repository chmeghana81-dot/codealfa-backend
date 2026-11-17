from django.contrib import admin
from .models import RazorpayPayment


@admin.register(RazorpayPayment)
class RazorpayPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "razorpay_order_id",
        "razorpay_payment_id", "amount",
        "currency", "status", "order", "created_at"
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "razorpay_order_id",
        "razorpay_payment_id"
    )
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25
