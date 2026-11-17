
# from django.db import transaction
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated, IsAdminUser

# from products.models import Product
# from .models import Cart, CartItem
# from .serializers import CartSerializer


# class CartAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         cart, created = Cart.objects.get_or_create(
#             user=request.user
#         )

#         serializer = CartSerializer(cart)
#         return Response(serializer.data)

#     @transaction.atomic
#     def post(self, request):
#         product_id = request.data.get("product")
#         quantity = request.data.get("quantity", 1)

#         try:
#             quantity = int(quantity)
#             if quantity < 1:
#                 raise ValueError
#         except (ValueError, TypeError):
#             return Response(
#                 {"error": "Quantity must be a positive integer."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             product = Product.objects.select_for_update().get(
#                 id=product_id
#             )
#         except (Product.DoesNotExist, ValueError, TypeError):
#             return Response(
#                 {"error": "Product not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         cart, created = Cart.objects.get_or_create(
#             user=request.user
#         )

#         cart_item, item_created = CartItem.objects.get_or_create(
#             cart=cart,
#             product=product,
#             defaults={"quantity": quantity}
#         )

#         if not item_created:
#             cart_item.quantity += quantity

#         if cart_item.quantity > product.stock:
#             return Response(
#                 {"error": "Requested quantity exceeds available stock."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         cart_item.save()

#         return Response(
#             CartSerializer(cart).data,
#             status=status.HTTP_200_OK
#         )


# class CartItemDetailAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get_object(self, request, pk):
#         try:
#             return CartItem.objects.select_related(
#                 "product", "cart"
#             ).get(
#                 id=pk,
#                 cart__user=request.user
#             )
#         except CartItem.DoesNotExist:
#             return None

#     def patch(self, request, pk):
#         cart_item = self.get_object(request, pk)

#         if cart_item is None:
#             return Response(
#                 {"error": "Cart item not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         try:
#             quantity = int(request.data.get("quantity"))
#             if quantity < 1:
#                 raise ValueError
#         except (ValueError, TypeError):
#             return Response(
#                 {"error": "Quantity must be at least 1."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         if quantity > cart_item.product.stock:
#             return Response(
#                 {"error": "Requested quantity exceeds available stock."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         cart_item.quantity = quantity
#         cart_item.save()

#         return Response(CartSerializer(cart_item.cart).data)

#     def delete(self, request, pk):
#         cart_item = self.get_object(request, pk)

#         if cart_item is None:
#             return Response(
#                 {"error": "Cart item not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         cart = cart_item.cart
#         cart_item.delete()

#         return Response(
#             CartSerializer(cart).data,
#             status=status.HTTP_200_OK
#         )


# class AdminAllCartsAPIView(APIView):
#     permission_classes = [IsAdminUser]

#     def get(self, request):
#         carts = Cart.objects.select_related(
#             "user"
#         ).prefetch_related(
#             "items__product"
#         )

#         serializer = CartSerializer(carts, many=True)
#         return Response(serializer.data)


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

    # Get logged-in user's cart
    def get(self, request):
        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    # Add product to cart
    @transaction.atomic
    def post(self, request):
        product_id = request.data.get("product")

        print("Received product ID:", repr(product_id))

        quantity = request.data.get("quantity", 1)

        if not product_id:
            return Response(
                {"error": "Product ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            product = Product.objects.get(
                pk=int(product_id)
            )

        except (Product.DoesNotExist, ValueError, TypeError):
            return Response(
                {
                    "error": "Product not found.",
                    "received_product_id": product_id
                },
                status=status.HTTP_404_NOT_FOUND
            )

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity}
        )

        if not item_created:
            cart_item.quantity += quantity

        if cart_item.quantity > product.stock:
            return Response(
                {
                    "error": "Requested quantity exceeds available stock."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.save()

        serializer = CartSerializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class CartItemDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Get cart item belonging to logged-in user
    def get_object(self, request, pk):
        try:
            return CartItem.objects.select_related(
                "product", "cart"
            ).get(
                id=pk,
                cart__user=request.user
            )

        except CartItem.DoesNotExist:
            return None

    # Update cart item quantity
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
                {
                    "error": "Requested quantity exceeds available stock."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        serializer = CartSerializer(cart_item.cart)

        return Response(serializer.data)

    # Remove product from cart
    def delete(self, request, pk):
        cart_item = self.get_object(request, pk)

        if cart_item is None:
            return Response(
                {"error": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        cart = cart_item.cart
        cart_item.delete()

        serializer = CartSerializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AdminAllCartsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        carts = Cart.objects.select_related(
            "user"
        ).prefetch_related(
            "items__product"
        )

        serializer = CartSerializer(
            carts,
            many=True
        )

        return Response(serializer.data)
