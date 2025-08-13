from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from authentication.models import UserModel, EmailVerificationModel, BlacklistedAccessTokenModel
from authentication.utils import (
    send_verification_email,
    generate_expiry_time
)
from authentication.validators import validate_password_uppercase, validate_tokens
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password, validate_password_uppercase],
        style={"input_type": "password"},
        help_text="Password must be at least 8 characters with at least one uppercase letter",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Must match the password field",
    )

    class Meta:
        model = UserModel
        fields = ["email", "password", "password_confirm"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        validated_data["password"] = make_password(validated_data["password"])
        user = super().create(validated_data)

        verification = EmailVerificationModel.objects.create(
            user=user,
            type=1,
            expires_at=generate_expiry_time()
        )
        send_verification_email(user, verification.code)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise AuthenticationFailed("Invalid email or password.")

        if not user.is_superuser and not user.is_verified:
            raise AuthenticationFailed("Email is not verified.")

        data['user'] = user
        return data


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
    access_token = serializers.CharField(required=True)

    def validate(self, data):
        refresh_token = data.get('refresh_token')
        access_token = data.get('access_token')

        if not validate_tokens(refresh_token, access_token):
            raise serializers.ValidationError(
                'Access token or Refresh token is invalid or expired'
            )

        refresh_blacklisted = BlacklistedToken.objects.filter(token__token=refresh_token).exists()

        access_blacklisted = BlacklistedAccessTokenModel.objects.filter(token=access_token).exists()

        if refresh_blacklisted or access_blacklisted:
            raise serializers.ValidationError('Tokens are already blacklisted')

        return data
