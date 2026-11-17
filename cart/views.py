from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from products.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)

    @transaction.atomic
    def post(self, request):
        product_id = request.data.get("product")
        quantity = request.data.get("quantity", 1)
        selected_size = str(request.data.get("selected_size") or "").strip()
        selected_color = str(request.data.get("selected_color") or "").strip()

        try:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {"error": "Quantity must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.select_for_update().get(pk=int(product_id))
        except (Product.DoesNotExist, ValueError, TypeError):
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if product.stock < 1:
            return Response(
                {"error": "This product is out of stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if product.available_sizes:
            if selected_size not in product.available_sizes:
                return Response(
                    {"error": "Please select a valid product size."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif selected_size:
            return Response(
                {"error": "This product does not have size options."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if product.available_colors:
            if selected_color not in product.available_colors:
                return Response(
                    {"error": "Please select a valid product colour."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif selected_color:
            return Response(
                {"error": "This product does not have colour options."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            selected_size=selected_size,
            selected_color=selected_color,
            defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity

        if cart_item.quantity > product.stock:
            return Response(
                {"error": "Requested quantity exceeds available stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.save()
        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK
        )


class CartItemDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return CartItem.objects.select_related(
                "product", "cart"
            ).get(id=pk, cart__user=request.user)
        except CartItem.DoesNotExist:
            return None

    def patch(self, request, pk):
        cart_item = self.get_object(request, pk)

        if cart_item is None:
            return Response(
                {"error": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            quantity = int(request.data.get("quantity"))
            if quantity < 1:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {"error": "Quantity must be at least 1."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity > cart_item.product.stock:
            return Response(
                {"error": "Requested quantity exceeds available stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity"])

        return Response(CartSerializer(cart_item.cart).data)

    def delete(self, request, pk):
        cart_item = self.get_object(request, pk)

        if cart_item is None:
            return Response(
                {"error": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        cart = cart_item.cart
        cart_item.delete()
        return Response(CartSerializer(cart).data)


class AdminAllCartsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        carts = Cart.objects.select_related(
            "user"
        ).prefetch_related("items__product")

        return Response(CartSerializer(carts, many=True).data)
