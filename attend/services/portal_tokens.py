from datetime import timedelta
import hashlib

from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError

from attend.models import PortalCliente
from attend.services.portal_access import validar_acesso_portal_cliente

signer = TimestampSigner(salt="portal-cliente-acesso")

def gerar_token_portal_cliente(portal_cliente):
    raw_secret = get_random_string(48)
    payload = f"{portal_cliente.pk}:{portal_cliente.tenant_id}:{portal_cliente.email}:{raw_secret}"
    signed_token = signer.sign(payload)

    # opcional: manter compatibilidade com sua estrutura atual
    portal_cliente.acesso_token = hashlib.sha256(signed_token.encode()).hexdigest()
    portal_cliente.acesso_token_expira_em = timezone.now() + timedelta(days=3)
    portal_cliente.save(update_fields=["acesso_token", "acesso_token_expira_em", "updated_at"])

    return signed_token

def validar_acesso_portal_cliente(portal_cliente):
    hoje = timezone.localdate()

    if not portal_cliente.acesso_ativo:
        raise ValidationError({"detail": "Acesso ao portal desativado."})

    if portal_cliente.contrato_inicio and portal_cliente.contrato_inicio > hoje:
        raise ValidationError({"detail": "O acesso ainda não foi liberado para este cliente."})

    if portal_cliente.contrato_fim and portal_cliente.contrato_fim < hoje:
        raise ValidationError({"detail": "O contrato expirou e o acesso ao portal foi encerrado."})

def validar_token_portal_cliente(token: str, validar_vigencia=True):
    try:
        payload = signer.unsign(token, max_age=timedelta(days=3))
    except SignatureExpired:
        raise ValidationError({"detail": "Token expirado."})
    except BadSignature:
        raise ValidationError({"detail": "Token inválido."})

    try:
        portal_cliente_id, tenant_id, email, _ = payload.split(":", 3)
    except ValueError:
        raise ValidationError({"detail": "Token inválido."})

    try:
        portal_cliente = PortalCliente.objects.select_related("tenant", "user").get(
            pk=portal_cliente_id,
            tenant_id=tenant_id,
            email=email,
        )
    except PortalCliente.DoesNotExist:
        raise ValidationError({"detail": "Token inválido."})

    if portal_cliente.acesso_token_expira_em and portal_cliente.acesso_token_expira_em < timezone.now():
        raise ValidationError({"detail": "Token expirado."})

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if portal_cliente.acesso_token and portal_cliente.acesso_token != token_hash:
        raise ValidationError({"detail": "Token inválido ou substituído por um novo convite."})

    if validar_vigencia:
        validar_acesso_portal_cliente(portal_cliente)

    return portal_cliente