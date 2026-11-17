# from django.db import transaction
# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated, IsAdminUser

# from .models import Order, OrderItem
# from .serializers import OrderSerializer
# from cart.models import Cart


# class PlaceOrderAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def post(self, request):

#         try:
#             cart = Cart.objects.get(user=request.user)
#         except Cart.DoesNotExist:
#             return Response(
#                 {"error": "Cart is empty."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         cart_items = list(
#             cart.items.select_related("product").all()
#         )

#         if not cart_items:
#             return Response(
#                 {"error": "Cart is empty."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         total_amount = 0

#         for item in cart_items:
#             if item.quantity > item.product.stock:
#                 return Response(
#                     {"error": f"Insufficient stock for {item.product.name}."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             total_amount += item.product.price * item.quantity

#         order = Order.objects.create(
#             user=request.user,
#             total_amount=total_amount
#         )

#         for item in cart_items:
#             OrderItem.objects.create(
#                 order=order,
#                 product=item.product,
#                 quantity=item.quantity,
#                 price=item.product.price
#             )

#             item.product.stock -= item.quantity
#             item.product.save(update_fields=["stock"])

#         cart.items.all().delete()

#         serializer = OrderSerializer(order)

#         return Response(
#             serializer.data,
#             status=status.HTTP_201_CREATED
#         )


# class MyOrdersAPIView(generics.ListAPIView):
#     serializer_class = OrderSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Order.objects.filter(
#             user=self.request.user
#         ).prefetch_related("items__product").order_by("-created_at")


# class OrderDetailAPIView(generics.RetrieveAPIView):
#     serializer_class = OrderSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Order.objects.filter(
#             user=self.request.user
#         ).prefetch_related("items__product")


# class AdminAllOrdersAPIView(generics.ListAPIView):
#     serializer_class = OrderSerializer
#     permission_classes = [IsAdminUser]

#     queryset = Order.objects.all().select_related(
#         "user"
#     ).prefetch_related("items__product").order_by("-created_at")

from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart


class PlaceOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_items = list(
            cart.items.select_related("product").all()
        )

        if not cart_items:
            return Response(
                {"error": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_amount = 0

        for item in cart_items:
            if item.quantity > item.product.stock:
                return Response(
                    {"error": f"Insufficient stock for {item.product.name}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_amount += item.product.price * item.quantity

        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

            item.product.stock -= item.quantity
            item.product.save(update_fields=["stock"])

        cart.items.all().delete()

        serializer = OrderSerializer(order)

        return Response(
            serializer.data,
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
