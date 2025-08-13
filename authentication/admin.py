from django.contrib import admin
from .models import UserModel, BlacklistedAccessTokenModel

admin.site.register(UserModel)
admin.site.register(BlacklistedAccessTokenModel)
