from rest_framework.exceptions import ValidationError
from attend.models import ProfissionalTenant

def validar_multiplos_profissionais(tenant):
    total_profissionais = ProfissionalTenant.objects.filter(
        tenant=tenant,
        ativo=True
    ).count()

    if tenant.plano != 'premium' and total_profissionais >= 1:
        raise ValidationError(
            'Apenas tenants premium podem ter múltiplos profissionais vinculados.'
        )