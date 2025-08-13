from datetime import timedelta
from tokenize import TokenError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.timezone import now
from authentication.models import UserModel, EmailVerificationModel, BlacklistedAccessTokenModel
from authentication.serializers import RegisterSerializer, LoginSerializer, LogoutSerializer
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterViewSet(ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Register new user",
        operation_description="Registers a new user and sends a verification code to their email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password', 'password_confirm'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="User email address"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Password (must be at least 8 characters and contain an uppercase letter)"
                ),
                'password_confirm': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Confirm password"
                ),
            },
            example={
                "email": "user@example.com",
                "password": "Qwerty456",
                "password_confirm": "Qwerty456"
            }
        ),
        responses={
            201: openapi.Response("User registered successfully", RegisterSerializer),
            400: "Validation error"
        },
        tags=["Authentication"]
    )
    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully. A verification code has been sent to your email.",
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Verify email with code",
        operation_description="Verifies the user's email using the verification code sent to their email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'code'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="User email address"
                ),
                'code': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Verification code"
                ),
            },
            example={
                "email": "user@example.com",
                "code": 123456
            }
        ),
        responses={
            200: "Email verified successfully",
            400: "Invalid or expired code"
        },
        tags=["Authentication"]
    )
    @action(detail=False, methods=["post"])
    def verify_register(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        user = UserModel.objects.filter(email=email).first()
        if not user:
            return Response(data={"message": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

        verification = EmailVerificationModel.objects.filter(user=user).order_by("-created_at").first()
        if not verification:
            return Response(data={"message": "Verification code not found."}, status=status.HTTP_400_BAD_REQUEST)

        if verification.block_until and verification.block_until > now():
            remaining_minutes = int((verification.block_until - now()).total_seconds() // 60)
            return Response(
                data={
                    "message": f"You have exceeded the maximum attempts. Try again after {remaining_minutes} minutes."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if verification.expires_at and verification.expires_at < now():
            return Response(data={"message": "The verification code has expired."}, status=status.HTTP_400_BAD_REQUEST)

        if verification.code != int(code):
            verification.attempts += 1
            if verification.attempts >= 3:
                verification.block_until = now() + timedelta(minutes=30)
                verification.attempts = 0
            verification.save(update_fields=["attempts", "block_until"])
            return Response({"message": "The verification code is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_verified = True
        user.save(update_fields=["is_verified"])
        verification.delete()

        return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)


class LoginViewSet(ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="User login",
        operation_description="Authenticate a user using email and password and return JWT tokens.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="User email address"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User account password"
                ),
            },
            example={
                "email": "user@example.com",
                "password": "Qwerty123"
            }
        ),
        responses={
            200: "Login successful. JWT tokens are returned.",
            401: "Invalid email or password.",
        },
        tags=["Authentication"]
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "email": user.email,
                "is_verified": user.is_verified
            }
        }, status=status.HTTP_200_OK)


class LogoutViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="User logout",
        operation_description="Logout the user by blacklisting both refresh and access tokens.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh_token', 'access_token'],
            properties={
                'refresh_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The refresh token to be blacklisted"
                ),
                'access_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The access token to be blacklisted"
                ),
            },
            example={
                "refresh_token": "your_refresh_token",
                "access_token": "your_access_token"
            }
        ),
        responses={
            205: "Successfully logged out.",
            400: "Invalid or expired token."
        },
        tags=["Authentication"]
    )
    @action(detail=False, methods=["post"])
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": serializer.errors, "ok": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh_token = serializer.validated_data["refresh_token"]
        access_token = serializer.validated_data["access_token"]

        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()

            BlacklistedAccessTokenModel.objects.create(token=access_token)

            return Response(
                data={"message": "Logged out successfully", "ok": True},
                status=status.HTTP_205_RESET_CONTENT,
            )

        except TokenError:
            return Response(
                data={"error": "Invalid or expired token", "ok": False},
                status=status.HTTP_400_BAD_REQUEST,
            )
