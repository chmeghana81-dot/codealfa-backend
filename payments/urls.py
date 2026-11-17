from django.urls import path
from .views import (
    CreateRazorpayOrderAPIView,
    VerifyRazorpayPaymentAPIView,
    AdminPaymentsAPIView,
)

urlpatterns = [
    path("create-order/", CreateRazorpayOrderAPIView.as_view(), name="create-razorpay-order"),
    path("verify-payment/", VerifyRazorpayPaymentAPIView.as_view(), name="verify-razorpay-payment"),
    path("admin/", AdminPaymentsAPIView.as_view(), name="admin-payments"),
]
