from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse, Http404
from django.contrib.auth.models import AnonymousUser

from attend.models import Tenant, Profissional, ProfissionalTenant


class TenantMiddleware(MiddlewareMixin):
    #HEADER_NAME = 'HTTP_X_TENANT_ID'

    def process_request(self, request):
        request.tenant = None

        user = getattr(request, 'user', None)
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            return None

        if hasattr(user, 'tenant') and user.tenant:
            request.tenant = user.tenant
            return None

        return None

        
#OBS: quando for incluir o multi tenant verificar as últimas alterções do dia 25/04/2026 as 14:28