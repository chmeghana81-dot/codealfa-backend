
# from rest_framework import generics
# from rest_framework.permissions import AllowAny, IsAuthenticated

# from .serializers import (
#     RegisterSerializer,
#     UserProfileSerializer,
# )


# class RegisterAPIView(generics.CreateAPIView):
#     serializer_class = RegisterSerializer
#     permission_classes = [AllowAny]


# class ProfileAPIView(generics.RetrieveAPIView):
#     serializer_class = UserProfileSerializer
#     permission_classes = [IsAuthenticated]

#     def get_object(self):
#         return self.request.user

# from rest_framework import generics
# from rest_framework.permissions import AllowAny, IsAuthenticated

# from .serializers import RegisterSerializer, UserProfileSerializer


# class RegisterAPIView(generics.CreateAPIView):
#     serializer_class = RegisterSerializer
#     permission_classes = [AllowAny]


# class ProfileAPIView(generics.RetrieveAPIView):
#     serializer_class = UserProfileSerializer
#     permission_classes = [IsAuthenticated]

#     def get_object(self):
#         return self.request.user
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import (
    RegisterSerializer,
    UserProfileSerializer
)


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ProfileAPIView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAdminUser


class AdminUsersAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        User = get_user_model()
        return User.objects.all().order_by("-date_joined")
