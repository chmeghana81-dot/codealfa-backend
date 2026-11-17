
# from django.urls import path

# from .views import (
#     CartAPIView,
#     CartItemDetailAPIView,
#     AdminAllCartsAPIView,
# )

# urlpatterns = [
#     path('', CartAPIView.as_view(), name='cart'),

#     path(
#         'items/<int:pk>/',
#         CartItemDetailAPIView.as_view(),
#         name='cart-item-detail'
#     ),

#     path(
#         'admin/',
#         AdminAllCartsAPIView.as_view(),
#         name='admin-all-carts'
#     ),
# ]

from django.urls import path

from .views import (
    CartAPIView,
    CartItemDetailAPIView,
    AdminAllCartsAPIView,
)

urlpatterns = [
    path('', CartAPIView.as_view(), name='cart'),
    path(
        'items/<int:pk>/',
        CartItemDetailAPIView.as_view(),
        name='cart-item-detail'
    ),
    path(
        'admin/',
        AdminAllCartsAPIView.as_view(),
        name='admin-all-carts'
    ),
]
