from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from decimal import Decimal
#from tenants.models import Tenant
import os
import uuid

class UserManager(BaseUserManager):
    """Manager customizado para User sem username"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_usuario', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class Tenant(models.Model):
    """Organização (profissional ou escola/clinica/academia) - cada cliente SaaS"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, max_length=50)  # profissional-joao
    nome_fantasia = models.CharField(max_length=200)
    documento = models.CharField(max_length=20)  # CPF/CNPJ
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    plano = models.CharField(
        max_length=20, 
        choices=[
            ('basico', 'Básico'),
            ('pro', 'Pro'),
            ('premium', 'Premium'),
        ], 
        default='basico'
    )
    limite_clientes = models.PositiveIntegerField(default=10)
    data_inicio_plano = models.DateField()
    data_fim_plano = models.DateField()
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['slug', 'ativo'])]

    def __str__(self):
        return self.nome_fantasia

class User(AbstractUser):
    """Usuário base com tenant"""
    username = None
    email = models.EmailField(unique=True)
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    tipo_usuario = models.CharField(
        max_length=20,
        choices=[
            ('Profissional', 'Profissional'),
            ('responsavel', 'Responsável'),
            ('Cliente', 'Cliente'),
            ('admin', 'Admin Tenant')
        ],
        default='admin'
    )
    telefone = models.CharField(max_length=20, blank=True)
    ativo = models.BooleanField(default=True)
    
    # ADICIONE ESTA LINHA:
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'email']),
            models.Index(fields=['tenant', 'tipo_usuario']),
        ]

    def __str__(self):
        return f"{self.email} ({self.tipo_usuario})"

class Plano(models.Model):
    codigo = models.CharField(max_length=30, unique=True)  # basic, pro, clinic, etc
    nome = models.CharField(max_length=100)
    max_profissionais = models.PositiveIntegerField(default=1)
    permite_multiplos_profissionais = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)

class Profissional(models.Model):
    """Perfil do profissional"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenants = models.ManyToManyField(Tenant, related_name='profissionais')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_profissional')
    nome_exibicao = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    especialidade = models.CharField(max_length=200, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    foto = models.ImageField(upload_to='profissionais/', null=True, blank=True)
    #ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    
    def __str__(self):
        return self.nome_exibicao

class ProfissionalTenant(models.Model):
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    #ativo = models.BooleanField(default=True)
    #papel = models.CharField(max_length=30, default='admin')

    class Meta:
        unique_together = ('profissional', 'tenant')



class Responsavel(models.Model):
    """Responsável pelo Cliente"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_responsavel')
    documento = models.CharField(max_length=20, blank=True)
    relacao_cliente = models.CharField(max_length=50, blank=True)  # pai, mãe, etc.

    class Meta:
        indexes = [models.Index(fields=['tenant'])]

    def __str__(self):
        return self.user.nome


class Cliente(models.Model):
    """Cliente"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    data_nascimento = models.DateField(blank=True, null=True)
    cpf = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    responsavel = models.ForeignKey(Responsavel, on_delete=models.SET_NULL, null=True, blank=True)
    acesso_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # opcional: data de expiração desse token
    acesso_token_expira_em = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'nome']),
            models.Index(fields=['tenant', 'responsavel']),
        ]

    def __str__(self):
        return self.nome
    
    
def avatar_upload_to(instance, filename):
    ext = filename.split('.')[-1].lower()
    return os.path.join('avatars', str(instance.user_id), f'{uuid.uuid4().hex}.{ext}')


class PortalCliente(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="clientes_portal")
    nome = models.CharField(max_length=150)
    email = models.EmailField()
    telefone = models.CharField(max_length=30, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    contrato_inicio = models.DateField(null=True, blank=True)
    contrato_fim = models.DateField(null=True, blank=True)
    acesso_ativo = models.BooleanField(default=True)
    cadastro_finalizado = models.BooleanField(default=False)
    acesso_token = models.CharField(max_length=255, null=True, blank=True)
    acesso_token_expira_em = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "email"], name="uniq_cliente_email_por_tenant")
        ]

    def __str__(self):
        return f"{self.nome} - {self.tenant_id}"

class CustomerInviteToken(models.Model):
    STATUS_PENDING = "pending"
    STATUS_USED = "used"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendente"),
        (STATUS_USED, "Usado"),
        (STATUS_EXPIRED, "Expirado"),
        (STATUS_CANCELED, "Cancelado"),
    ]

    portal_cliente = models.ForeignKey(PortalCliente, on_delete=models.CASCADE, related_name="invites")
    token_hash = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    foto = models.ImageField(upload_to=avatar_upload_to, null=True, blank=True)

    def __str__(self):
        return f'Perfil de {self.user}'

        
class PacoteSessoes(models.Model):
    """Pacote de sessões do cliente"""

    PLANO_CHOICES = (
        ('basico', 'Básico'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    )
    plano_tipo = models.CharField(max_length=20, choices=PLANO_CHOICES, default='basico')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='pacotes')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pacotes')
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='pacotes')

    # Período
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)

    # Sessões / financeiro
    qtd_sessoes = models.PositiveIntegerField(default=1)  # QUANTAS SESSÕES?
    valor_por_sessao = models.DecimalField(max_digits=10, decimal_places=2)  # VALOR POR SESSÃO
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)       # TOTAL
    qtd_parcelas = models.PositiveIntegerField(default=1)                    # PARCELAS
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)     # VALOR POR PARCELA
    dia_pagamento = models.PositiveSmallIntegerField()                       # DIA DO PAGAMENTO (1–31)

    # Status / controle
    qtd_sessoes_usadas = models.PositiveIntegerField(default=0)
    descricao = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=[
            ('ativo', 'Ativo'),
            ('concluido', 'Concluído'),
            ('cancelado', 'Cancelado'),
            ('vencido', 'Vencido'),
        ],
        default='ativo',
    )
    sessoes_preview = models.JSONField(default=list, blank=True)
    parcelas_preview = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pacote {self.id} - {self.cliente}'

    def save(self, *args, **kwargs):
        # cálculos financeiros
        if self.qtd_sessoes is not None and self.valor_por_sessao is not None:
            self.valor_total = self.qtd_sessoes * self.valor_por_sessao

        if self.qtd_parcelas:  # evita divisão por zero
            self.valor_parcela = self.valor_total / self.qtd_parcelas

        # proteção de controle
        if self.qtd_sessoes_usadas > self.qtd_sessoes:
            self.qtd_sessoes_usadas = self.qtd_sessoes

        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'cliente']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'data_fim']),
        ]

    @property
    def sessoes_restantes(self):
        return max(self.qtd_sessoes - self.qtd_sessoes_usadas, 0)

    def __str__(self):
        return f"{self.cliente.nome} - {self.id}"



class Sessao(models.Model):
    """Sessao individual"""
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('remarcada', 'Remarcada'),
        ('solicitada_remarcacao', 'Solicitada Remarcação'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    pacote = models.ForeignKey(PacoteSessoes, on_delete=models.CASCADE, related_name='sessoes')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True, related_name='sessoes',)
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE)
    data_hora_inicio = models.DateTimeField()
    data_hora_fim = models.DateTimeField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='agendada')
    observacoes = models.TextField(blank=True)
    origem_remarcacao = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    motivo_cancelamento = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def dar_baixa(self):
        """Dar baixa na sessão realizada"""
        self.status = 'realizada'
        self.pacote.qtd_sessoes_usadas += 1
        self.pacote.save()
        self.save()

    def remarcar(self, nova_data_inicio, nova_data_fim):
        """Cria nova sessão e marca esta como remarcada"""
        self.status = 'remarcada'
        self.save()
        Sessao.objects.create(
            tenant=self.tenant,
            pacote=self.pacote,
            cliente=self.cliente,
            profissional=self.profissional,
            data_hora_inicio=nova_data_inicio,
            data_hora_fim=nova_data_fim,
            origem_remarcacao=self
        )

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'data_hora_inicio']),
            models.Index(fields=['tenant', 'cliente', 'status']),
            models.Index(fields=['tenant', 'pacote']),
        ]

    def __str__(self):
        return f"{self.cliente.nome} - {self.data_hora_inicio} ({self.status})"


class Fatura(models.Model):
    """Cobrança / fatura"""
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('parcialmente_paga', 'Parcialmente Paga'),
        ('paga', 'Paga'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='faturas')
    responsavel = models.ForeignKey(Responsavel, on_delete=models.SET_NULL, null=True, blank=True)
    pacote = models.ForeignKey(PacoteSessoes, on_delete=models.SET_NULL, null=True, blank=True)
    descricao = models.CharField(max_length=500)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_emissao = models.DateTimeField(auto_now_add=True)
    data_vencimento = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='aberta')

    def save(self, *args, **kwargs):
        if self.valor_pago >= self.valor_total:
            self.status = 'paga'
        elif timezone.now().date() > self.data_vencimento and self.status != 'paga':
            self.status = 'vencida'
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'cliente']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'data_vencimento']),
        ]

    def __str__(self):
        return f"Fatura {self.cliente.nome} - R$ {self.valor_total}"


class Pagamento(models.Model):
    """Registro de pagamento"""
    METODO_CHOICES = [
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('boleto', 'Boleto'),
        ('dinheiro', 'Dinheiro'),
    ]
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('falhou', 'Falhou'),
        ('expirado', 'Expirado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    fatura = models.ForeignKey(Fatura, on_delete=models.CASCADE, related_name='pagamentos')
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_pagamento = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    gateway = models.CharField(max_length=50, blank=True)  # iopay, pagbrasil, etc.
    gateway_transaction_id = models.CharField(max_length=100, blank=True)
    pix_qr_code = models.TextField(blank=True)  # QR Code PIX
    pix_copia_cola = models.TextField(blank=True)
    webhook_recebido = models.BooleanField(default=False)
    raw_response = models.JSONField(blank=True, null=True)  # Resposta do gateway

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'fatura']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'gateway_transaction_id']),
        ]

    def confirmar_pagamento(self):
        self.status = 'confirmado'
        self.data_pagamento = timezone.now()
        self.fatura.valor_pago += self.valor
        self.fatura.save()
        self.save()

    def __str__(self):
        return f"Pagamento {self.fatura.cliente.nome} - R$ {self.valor}"
    
class Contrato(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancell  ed'),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='contrato')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True, related_name='contratos')
    pacote = models.ForeignKey(PacoteSessoes, on_delete=models.CASCADE)
    date_inicio = models.DateField()
    preferred_instructor = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')

    def __str__(self):
        return f"{self.cliente.nome} - {self.pacote.nome}"
