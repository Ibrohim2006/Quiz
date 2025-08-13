from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken


def validate_password_uppercase(value):
    if not any(char.isupper() for char in value):
        raise ValidationError("Password must contain at least one uppercase letter.")


def validate_tokens(refresh_token, access_token):
    try:
        AccessToken(access_token)
        RefreshToken(refresh_token)
        return True
    except Exception:
        return False
