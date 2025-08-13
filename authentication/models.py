from django.contrib.auth.models import AbstractUser
from django.db import models
from authentication.managers import UserManager
import uuid
from authentication.utils import generate_code

VerificationTypes = (
    (1, "REGISTER"),
    (2, "RESEND"),
    (3, "PASSWORD_RESET"),
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        abstract = True


class UserModel(AbstractUser, TimeStampedModel):
    username = None
    email = models.EmailField(unique=True, verbose_name="Email address")
    is_verified = models.BooleanField(default=False, verbose_name="Is verified")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class EmailVerificationModel(TimeStampedModel):
    user = models.ForeignKey(UserModel, models.SET_NULL, null=True, related_name="email_verifications")
    key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    code = models.PositiveIntegerField(default=generate_code)
    type = models.IntegerField(choices=VerificationTypes, default=1)
    attempts = models.IntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    block_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email if self.user else 'Unknown'} - {self.code}"

    class Meta:
        db_table = 'email_verification'
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'


class BlacklistedAccessTokenModel(models.Model):
    token = models.CharField(max_length=1000, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'blacklisted_access_token'
        verbose_name = 'Blacklisted Access Token'
        verbose_name_plural = 'Blacklisted Access Tokens'
