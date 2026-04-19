# attend/middleware.py

from django.http import Http404
from .models import Tenant

class TenantMiddleware:
    """
    Middleware simples para carregar o tenant com base no host.
    Para desenvolvimento local, podemos simplesmente pegar um tenant fixo
    ou ignorar se não existir.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Para desenvolvimento: usa o primeiro tenant como padrão.
        tenant = None
        try:
            tenant = Tenant.objects.first()
        except Tenant.DoesNotExist:
            tenant = None

        request.tenant = tenant
        response = self.get_response(request)
        return response
