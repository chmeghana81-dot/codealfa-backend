from rest_framework import serializers
from .models import Category, Product, WishlistItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )
    image = serializers.ImageField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = Product
        fields = "__all__"


class WishlistSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source="product", read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "product_details", "created_at"]
        read_only_fields = ["id", "created_at"]
