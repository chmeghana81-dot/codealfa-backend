
from decimal import Decimal, InvalidOperation

import razorpay

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from products.models import Product

from .models import RazorpayPayment


def get_razorpay_client():
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")

    if not key_id or not key_secret:
        raise ValueError("Razorpay credentials are not configured.")

    return razorpay.Client(auth=(key_id, key_secret))


def validate_shipping_details(data):
    fields = [
        "full_name", "mobile", "address",
        "city", "state", "pincode"
    ]

    shipping = {}

    for field in fields:
        value = data.get(field)

        if not isinstance(value, str) or not value.strip():
            return None, f"{field.replace('_', ' ').title()} is required."

        shipping[field] = value.strip()

    if not shipping["mobile"].isdigit() or len(shipping["mobile"]) != 10:
        return None, "Enter a valid 10-digit mobile number."

    if not shipping["pincode"].isdigit() or len(shipping["pincode"]) != 6:
        return None, "Enter a valid 6-digit PIN code."

    return shipping, None


class CreateRazorpayOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        shipping, error = validate_shipping_details(request.data)

        if error:
            return Response(
                {"error": error},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client = get_razorpay_client()
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
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

        with transaction.atomic():
            locked_products = {
                product.pk: product
                for product in Product.objects.select_for_update().filter(
                    pk__in=product_ids
                )
            }

            total_amount = Decimal("0.00")
            snapshot = []

            for item in cart_items:
                product = locked_products.get(item.product_id)

                if product is None:
                    return Response(
                        {"error": "A product in your cart is unavailable."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if item.quantity > product.stock:
                    return Response(
                        {"error": f"Insufficient stock for {product.name}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if (
                    product.available_sizes
                    and item.selected_size not in product.available_sizes
                ):
                    return Response(
                        {"error": f"Invalid size for {product.name}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if (
                    product.available_colors
                    and item.selected_color not in product.available_colors
                ):
                    return Response(
                        {"error": f"Invalid colour for {product.name}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                line_total = product.price * item.quantity
                total_amount += line_total

                snapshot.append({
                    "cart_item_id": item.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "price": str(product.price),
                    "selected_size": item.selected_size,
                    "selected_color": item.selected_color,
                })

            if total_amount <= 0:
                return Response(
                    {"error": "Invalid cart amount."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            amount_paise = int(total_amount * 100)

            try:
                razorpay_order = client.order.create({
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": f"user_{request.user.id}_{cart.id}",
                })
            except Exception:
                return Response(
                    {"error": "Unable to create Razorpay order. Please try again."},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            payment = RazorpayPayment.objects.create(
                user=request.user,
                razorpay_order_id=razorpay_order["id"],
                amount=amount_paise,
                currency="INR",
                shipping_details=shipping,
                cart_snapshot=snapshot,
            )

        return Response(
            {
                "key_id": settings.RAZORPAY_KEY_ID,
                "order_id": razorpay_order["id"],
                "amount": amount_paise,
                "currency": "INR",
                "payment_record_id": payment.id,
            },
            status=status.HTTP_201_CREATED
        )


class VerifyRazorpayPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not all([
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        ]):
            return Response(
                {"error": "Payment verification details are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment = get_object_or_404(
            RazorpayPayment.objects.select_for_update(),
            user=request.user,
            razorpay_order_id=razorpay_order_id
        )

        # Make verification requests safe to retry.
        if payment.status == "paid" and payment.order_id:
            return Response(
                OrderSerializer(payment.order).data,
                status=status.HTTP_200_OK
            )

        try:
            client = get_razorpay_client()
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
        except Exception:
            return Response(
                {"error": "Invalid payment signature."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            razorpay_payment = client.payment.fetch(razorpay_payment_id)
        except Exception:
            return Response(
                {"error": "Unable to verify payment with Razorpay."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        if (
            razorpay_payment.get("order_id") != payment.razorpay_order_id
            or int(razorpay_payment.get("amount", 0)) != payment.amount
            or razorpay_payment.get("currency") != payment.currency
            or razorpay_payment.get("status") != "captured"
        ):
            return Response(
                {"error": "Payment is not captured or payment details do not match."},
                status=status.HTTP_400_BAD_REQUEST
            )

        snapshot = payment.cart_snapshot
        shipping = payment.shipping_details

        if not snapshot:
            return Response(
                {"error": "The saved cart details are missing. Contact support."},
                status=status.HTTP_409_CONFLICT
            )

        product_ids = [item["product_id"] for item in snapshot]

        locked_products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(
                pk__in=product_ids
            )
        }

        total_amount = Decimal("0.00")

        for item in snapshot:
            product = locked_products.get(item["product_id"])

            if product is None:
                return Response(
                    {"error": "A purchased product is no longer available. Contact support."},
                    status=status.HTTP_409_CONFLICT
                )

            quantity = int(item["quantity"])

            if quantity > product.stock:
                return Response(
                    {"error": f"Insufficient stock for {product.name}. Payment was captured; contact support."},
                    status=status.HTTP_409_CONFLICT
                )

            if (
                product.available_sizes
                and item["selected_size"] not in product.available_sizes
            ):
                return Response(
                    {"error": f"The selected size for {product.name} is no longer available. Contact support."},
                    status=status.HTTP_409_CONFLICT
                )

            if (
                product.available_colors
                and item["selected_color"] not in product.available_colors
            ):
                return Response(
                    {"error": f"The selected colour for {product.name} is no longer available. Contact support."},
                    status=status.HTTP_409_CONFLICT
                )

            total_amount += Decimal(item["price"]) * quantity

        if int(total_amount * 100) != payment.amount:
            return Response(
                {"error": "The saved order amount does not match the payment. Contact support."},
                status=status.HTTP_409_CONFLICT
            )

        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            payment_method="razorpay",
            payment_status="paid",
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            **shipping
        )

        for item in snapshot:
            product = locked_products[item["product_id"]]
            quantity = int(item["quantity"])

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=Decimal(item["price"]),
                selected_size=item["selected_size"],
                selected_color=item["selected_color"],
            )

            product.stock -= quantity
            product.save(update_fields=["stock"])

        # Remove only the original cart rows, and only if unchanged.
        for item in snapshot:
            CartItem.objects.filter(
                id=item["cart_item_id"],
                cart__user=request.user,
                product_id=item["product_id"],
                quantity=item["quantity"],
                selected_size=item["selected_size"],
                selected_color=item["selected_color"],
            ).delete()

        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = "paid"
        payment.order = order
        payment.save(
            update_fields=[
                "razorpay_payment_id",
                "status",
                "order",
                "updated_at",
            ]
        )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )
