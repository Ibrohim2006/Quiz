from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _
from .models import BlacklistedAccessTokenModel


class BlacklistAccessTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
            if BlacklistedAccessTokenModel.objects.filter(token=access_token).exists():
                return JsonResponse(
                    data={'detail': _('Access token in blacklist, re-login')},
                    status=401
                )
        else:
            access_token = None
