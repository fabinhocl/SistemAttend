# portal/permissions.py
from rest_framework.permissions import BasePermission

from attend.models import PortalCliente
from attend.services.portal_access import portal_cliente_vigente


class IsAuthenticatedPortalCliente(BasePermission):
    message = "Você não tem acesso ao portal do cliente."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        try:
            portal_cliente = PortalCliente.objects.select_related("tenant").get(user=user)
        except PortalCliente.DoesNotExist:
            return False

        if not portal_cliente.cadastro_finalizado:
            return False

        if not portal_cliente_vigente(portal_cliente):
            return False

        request.portal_cliente = portal_cliente
        return True