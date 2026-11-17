
from django.urls import path

from .views import (
    CategoryListAPIView,
    ProductListAPIView,
    ProductDetailAPIView,
)

urlpatterns = [
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('products/', ProductListAPIView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    
]

from .views import (
    WishlistListCreateAPIView,
    WishlistDeleteAPIView,
)

urlpatterns += [
    path("wishlist/", WishlistListCreateAPIView.as_view(), name="wishlist-list-create"),
    path("wishlist/<int:pk>/", WishlistDeleteAPIView.as_view(), name="wishlist-delete"),
]
