from decimal import Decimal
from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart
from products.models import Product


class PlaceOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        required_fields = [
            "full_name", "mobile", "address",
            "city", "state", "pincode"
        ]

        data = {}
        for field in required_fields:
            value = request.data.get(field)
            if not isinstance(value, str) or not value.strip():
                return Response(
                    {"error": f"{field.replace('_', ' ').title()} is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data[field] = value.strip()

        if not data["mobile"].isdigit() or len(data["mobile"]) != 10:
            return Response(
                {"error": "Enter a valid 10-digit mobile number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not data["pincode"].isdigit() or len(data["pincode"]) != 6:
            return Response(
                {"error": "Enter a valid 6-digit PIN code."},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment_method = request.data.get("payment_method", "cod")
        if payment_method != "cod":
            return Response(
                {"error": "Currently only Cash on Delivery is available."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_items = list(
            cart.items.select_related("product").all()
        )

        if not cart_items:
            return Response(
                {"error": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        product_ids = [item.product_id for item in cart_items]
        locked_products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(
                pk__in=product_ids
            )
        }

        total_amount = Decimal("0.00")

        for item in cart_items:
            product = locked_products.get(item.product_id)

            if product is None:
                return Response(
                    {"error": "A product in your cart is no longer available."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if item.quantity > product.stock:
                return Response(
                    {"error": f"Insufficient stock for {product.name}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if product.available_sizes and item.selected_size not in product.available_sizes:
                return Response(
                    {"error": f"Invalid size selection for {product.name}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if product.available_colors and item.selected_color not in product.available_colors:
                return Response(
                    {"error": f"Invalid colour selection for {product.name}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_amount += product.price * item.quantity

        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            payment_method="cod",
            **data
        )

        for item in cart_items:
            product = locked_products[item.product_id]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price=product.price,
                selected_size=item.selected_size,
                selected_color=item.selected_color
            )

            product.stock -= item.quantity
            product.save(update_fields=["stock"])

        cart.items.all().delete()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class MyOrdersAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items__product").order_by("-created_at")


class OrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items__product")


class AdminAllOrdersAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    queryset = Order.objects.all().select_related(
        "user"
    ).prefetch_related("items__product").order_by("-created_at")

class AdminUpdateOrderStatusAPIView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status")
        allowed_statuses = [choice[0] for choice in Order.STATUS_CHOICES]

        if new_status not in allowed_statuses:
            return Response(
                {"error": "Invalid order status."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save(update_fields=["status"])

        return Response(OrderSerializer(order).data)
