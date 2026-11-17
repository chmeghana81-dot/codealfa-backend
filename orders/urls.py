from django.urls import path
from .views import (
    PlaceOrderAPIView,
    MyOrdersAPIView,
    OrderDetailAPIView,
    AdminAllOrdersAPIView,
    AdminUpdateOrderStatusAPIView,
)

urlpatterns = [
    path("place/", PlaceOrderAPIView.as_view(), name="place-order"),
    path("my-orders/", MyOrdersAPIView.as_view(), name="my-orders"),
    path("admin/", AdminAllOrdersAPIView.as_view(), name="admin-all-orders"),
    path(
        "admin/<int:pk>/status/",
        AdminUpdateOrderStatusAPIView.as_view(),
        name="admin-update-order-status"
    ),
    path("<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),
]
