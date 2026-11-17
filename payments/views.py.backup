
from decimal import Decimal
import logging

import razorpay

logger = logging.getLogger(__name__)

from django.conf import settings
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from cart.models import Cart
from products.models import Product
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer

from .models import RazorpayPayment


def get_razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise ValueError("Razorpay credentials are not configured.")

    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )


def validate_shipping_details(data):
    required_fields = [
        "full_name",
        "mobile",
        "address",
        "city",
        "state",
        "pincode",
    ]

    for field in required_fields:
        if not str(data.get(field, "")).strip():
            return False, f"{field} is required."

    mobile = str(data.get("mobile", ""))
    pincode = str(data.get("pincode", ""))

    if not mobile.isdigit() or len(mobile) != 10:
        return False, "Enter a valid 10-digit mobile number."

    if not pincode.isdigit() or len(pincode) != 6:
        return False, "Enter a valid 6-digit pincode."

    return True, None


class CreateRazorpayOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        valid, error = validate_shipping_details(request.data)

        if not valid:
            return Response(
                {"error": error},
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

        total_amount = Decimal("0.00")
        cart_snapshot = []

        for item in cart_items:

            product = item.product

            if item.quantity > product.stock:
                return Response(
                    {
                        "error": (
                            f"Insufficient stock for {product.name}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            price = Decimal(str(product.price))
            subtotal = price * item.quantity

            total_amount += subtotal

            cart_snapshot.append({
                "product_id": product.id,
                "product_name": product.name,
                "quantity": item.quantity,
                "price": str(price),
            })

        amount_paise = int(total_amount * 100)

        if amount_paise <= 0:
            return Response(
                {"error": "Invalid payment amount."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client = get_razorpay_client()

            razorpay_order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"megastore_{request.user.id}_{cart.id}",
            })

            shipping_fields = [
                "full_name",
                "email",
                "mobile",
                "address",
                "city",
                "state",
                "pincode",
            ]

            shipping_details = {
                field: request.data.get(field, "")
                for field in shipping_fields
            }

            payment = RazorpayPayment.objects.create(
                user=request.user,
                razorpay_order_id=razorpay_order["id"],
                amount=amount_paise,
                currency="INR",
                shipping_details=shipping_details,
                cart_snapshot=cart_snapshot,
            )

            return Response(
                {
                    "key_id": settings.RAZORPAY_KEY_ID,
                    "order_id": payment.razorpay_order_id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "payment_record_id": payment.id,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception:
            logger.exception("Razorpay order creation failed")
            return Response(
                {
                    "error": "Razorpay order creation failed. Check Django server logs."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyRazorpayPaymentAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not all([
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature,
        ]):
            return Response(
                {"error": "Payment verification details are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = RazorpayPayment.objects.get(
                user=request.user,
                razorpay_order_id=razorpay_order_id
            )

        except RazorpayPayment.DoesNotExist:
            return Response(
                {"error": "Payment order not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if payment.status == "paid" and payment.order:
            return Response(
                OrderSerializer(payment.order).data,
                status=status.HTTP_200_OK
            )

        if payment.status != "created":
            return Response(
                {"error": "This payment cannot be verified."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client = get_razorpay_client()

            # Verify Razorpay signature
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })

            # Confirm that Razorpay reports this payment as captured
            payment_data = client.payment.fetch(razorpay_payment_id)

            if payment_data.get("order_id") != razorpay_order_id:
                return Response(
                    {"error": "Payment order ID does not match."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if int(payment_data.get("amount", 0)) != payment.amount:
                return Response(
                    {"error": "Payment amount does not match."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if payment_data.get("currency") != payment.currency:
                return Response(
                    {"error": "Payment currency does not match."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if payment_data.get("status") != "captured":
                return Response(
                    {
                        "error": (
                            "Payment has not been captured yet. "
                            "Please try again after payment confirmation."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception:
            return Response(
                {"error": "Payment verification failed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():

                payment = RazorpayPayment.objects.select_for_update().get(
                    pk=payment.pk
                )

                if payment.status == "paid" and payment.order:
                    return Response(
                        OrderSerializer(payment.order).data,
                        status=status.HTTP_200_OK
                    )

                snapshot = payment.cart_snapshot

                product_ids = [
                    item["product_id"] for item in snapshot
                ]

                products = Product.objects.select_for_update().filter(
                    id__in=product_ids
                )

                product_map = {
                    product.id: product for product in products
                }

                if len(product_map) != len(set(product_ids)):
                    return Response(
                        {"error": "One or more products are unavailable."},
                        status=status.HTTP_409_CONFLICT
                    )

                total_amount = Decimal("0.00")

                for item in snapshot:

                    product = product_map[item["product_id"]]
                    quantity = int(item["quantity"])

                    if quantity > product.stock:
                        return Response(
                            {
                                "error": (
                                    f"Insufficient stock for {product.name}. "
                                    "Please contact support regarding payment."
                                )
                            },
                            status=status.HTTP_409_CONFLICT
                        )

                    total_amount += (
                        Decimal(item["price"]) * quantity
                    )

                expected_amount = int(total_amount * 100)

                if expected_amount != payment.amount:
                    return Response(
                        {"error": "Order amount validation failed."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Create Django order only after verified payment
                order = Order.objects.create(
                    user=request.user,
                    total_amount=total_amount,
                    status="confirmed",
                )

                for item in snapshot:

                    product = product_map[item["product_id"]]
                    quantity = int(item["quantity"])
                    price = Decimal(item["price"])

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=price,
                    )

                    product.stock -= quantity
                    product.save(update_fields=["stock"])

                # Remove only the unchanged cart items from this payment
                try:
                    cart = Cart.objects.get(user=request.user)

                    for item in snapshot:
                        cart.items.filter(
                            product_id=item["product_id"],
                            quantity=item["quantity"],
                        ).delete()

                except Cart.DoesNotExist:
                    pass

                payment.status = "paid"
                payment.razorpay_payment_id = razorpay_payment_id
                payment.order = order

                payment.save(
                    update_fields=[
                        "status",
                        "razorpay_payment_id",
                        "order",
                        "updated_at",
                    ]
                )

            return Response(
                {
                    **OrderSerializer(order).data,
                    "payment_method": "razorpay",
                    "payment_id": razorpay_payment_id,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception:
            return Response(
                {
                    "error": (
                        "Payment was received, but order creation "
                        "could not be completed. Please contact support."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )






from rest_framework.permissions import IsAdminUser


class AdminPaymentsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        payments = RazorpayPayment.objects.select_related(
            "user", "order"
        ).order_by("-created_at")

        data = [
            {
                "id": payment.id,
                "username": payment.user.username,
                "email": payment.user.email,
                "razorpay_order_id": payment.razorpay_order_id,
                "razorpay_payment_id": payment.razorpay_payment_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "order_id": payment.order_id,
                "created_at": payment.created_at,
            }
            for payment in payments
        ]

        return Response(data)
