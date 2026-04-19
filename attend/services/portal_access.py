# services/portal_access.py
from django.utils import timezone
from rest_framework.exceptions import ValidationError


def portal_cliente_vigente(portal_cliente):
    hoje = timezone.localdate()

    if not portal_cliente.acesso_ativo:
        return False

    if portal_cliente.contrato_inicio and portal_cliente.contrato_inicio > hoje:
        return False

    if portal_cliente.contrato_fim and portal_cliente.contrato_fim < hoje:
        return False

    return True

def validar_acesso_portal_cliente(portal_cliente):
    hoje = timezone.localdate()

    if not portal_cliente.acesso_ativo:
        raise ValidationError({"detail": "Acesso ao portal desativado."})

    if portal_cliente.contrato_inicio and portal_cliente.contrato_inicio > hoje:
        raise ValidationError({"detail": "O acesso ainda não foi liberado para este cliente."})

    if portal_cliente.contrato_fim and portal_cliente.contrato_fim < hoje:
        raise ValidationError({"detail": "O contrato expirou e o acesso ao portal foi encerrado."})