from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )
    product_image = serializers.SerializerMethodField()
    product_stock = serializers.IntegerField(source="product.stock", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id", "product", "product_name", "product_price",
            "product_image", "product_stock", "quantity",
            "selected_size", "selected_color", "subtotal"
        ]

    def get_subtotal(self, obj):
        return obj.product.price * obj.quantity

    def get_product_image(self, obj):
        if not obj.product.image:
            return None
    
        request = self.context.get("request")
    
        if request:
            return request.build_absolute_uri(obj.product.image.url)
    
        return obj.product.image.url


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True,context={"request": request})
    total_price = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id", "user", "username", "items",
            "total_price", "created_at", "updated_at"
        ]

    def get_total_price(self, obj):
        return sum(
            item.product.price * item.quantity
            for item in obj.items.select_related("product").all()
        )
