from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError

from attend.models import Tenant


class BaseTenantViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_tenant(self):
        tenant_id = self.request.headers.get('X-Tenant-Id')
        print('HEADER X-Tenant-Id:', tenant_id)

        if tenant_id:
            tenant = Tenant.objects.filter(id=tenant_id, ativo=True).first()
            print('TENANT VIA HEADER:', tenant)
            if not tenant:
                raise ValidationError('Tenant informado é inválido.')
            return tenant

        user_tenant = getattr(self.request.user, 'tenant', None)
        print('USER:', self.request.user)
        print('USER TENANT:', user_tenant)
        print('USER TENANT ATIVO:', getattr(user_tenant, 'ativo', None))

        if user_tenant and user_tenant.ativo:
            print('RETORNANDO TENANT DO USER')
            return user_tenant

        raise ValidationError('Tenant ativo não definido na requisição.')