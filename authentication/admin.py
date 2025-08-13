from django.contrib import admin
from .models import UserModel, EmailVerificationModel, BlacklistedAccessTokenModel

admin.site.register(UserModel)
admin.site.register(EmailVerificationModel)
admin.site.register(BlacklistedAccessTokenModel)
