from django.contrib.auth.models import AbstractUser
from django.db import models
from authentication.managers import UserManager
import uuid
from django.utils import timezone

VerificationTypes = (
    (1, "REGISTER"),
    (2, "RESEND"),
    (3, "PASSWORD_RESET"),
)


class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()

    class Meta:
        abstract = True


class UserModel(AbstractUser, BaseModel):
    username = None
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class BlacklistedAccessTokenModel(models.Model):
    token = models.CharField(max_length=1000, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'blacklisted_access_token'
        verbose_name = 'Blacklisted Access Token'
        verbose_name_plural = 'Blacklisted Access Tokens'
