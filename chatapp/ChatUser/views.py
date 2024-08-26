import jwt
from django.conf import settings
from django.contrib.auth import authenticate, login
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from .models import CustomUser
from .serializers import CustomUserSerializer,PasswordResetSerializer,OTPRequestSerializer,OTPVerifySerializer
from django.utils import timezone
from .utils import send_otp_email


class CustomUserList(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Generate a JWT token for the newly registered user
        user = serializer.instance
        refresh = RefreshToken.for_user(user)

        # Create a response with the token data
        response_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

class CustomUserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    data = {
        "email": user.email,
        "country": user.country,
        "age": user.age,
        "Receive mails": user.receive_mails,
    }
    return Response(data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    user = request.user
    user.country = request.data.get("country", user.country)
    user.age = request.data.get("age", user.age)
    user.receive_mails = request.data.get("Receive mails", user.receive_mails)
    user.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes((AllowAny,))
def user_login(request):
    email = request.data.get("email")  # Use 'email' instead of 'username'
    password = request.data.get("password")

    user = authenticate(
        request, email=email, password=password
    )  # Use 'email' for authentication
    if user is not None:
        login(request, user)

        # Include user-related data in the JWT payload
        payload = {
            "user_id": user.id,
            "email": user.email,  # Use 'email' field for the JWT payload
            "country": user.country,
            "age": user.age,
            # Include other user-related data here
        }

        # Create and sign the JWT access token
        access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        return Response({"access_token": access_token})
    else:
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )

class OTPRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.filter(email=email).first()
            if user:
                send_otp_email(user)
                return Response({'message': 'OTP sent successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            user = CustomUser.objects.filter(email=email, otp=otp, otp_expiration__gt=timezone.now()).first()
            if user:
                return Response({'message': 'OTP verified successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']
            otp = serializer.validated_data['otp']
            user = CustomUser.objects.filter(email=email, otp=otp, otp_expiration__gt=timezone.now()).first()
            if user:
                user.set_password(new_password)
                user.otp = None
                user.otp_expiration = None
                user.save()
                return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)