from django.http import HttpResponse
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from datetime import date, timedelta
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action, parser_classes
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError

from attend.models import Tenant, PacoteSessoes, Sessao, Fatura, Pagamento, Contrato, User, Profissional, Responsavel, Cliente, Profile, PortalCliente, ProfissionalTenant
from attend.serializers import ClienteSerializer, PacoteSessoesSerializer, SessaoSerializer, FaturaSerializer, PagamentoSerializer, ContratoSerializer, ProfissionalSerializer, ResponsavelSerializer, ProfileFotoSerializer, PortalClienteActivateSerializer, PortalClienteSerializer, MeSerializer
from attend.services.portal_tokens import gerar_token_portal_cliente, validar_token_portal_cliente
from attend.permissions import IsAuthenticatedPortalCliente
from attend.views_base import BaseTenantViewSet
from attend.services.tenant_rules import validar_multiplos_profissionais





def home(request):
    return HttpResponse("API Attend funcionando")

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Email e senha são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Autenticar usuário
    user = authenticate(request, username=email, password=password)
    
    if user is None:
        return Response(
            {'error': 'Credenciais inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Usuário inativo'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Gerar tokens JWT
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'email': user.email,
            'nome': user.get_full_name() or user.email.split('@')[0],
            'tipo_usuario': user.tipo_usuario,
            'is_superuser': user.is_superuser,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    from django.utils.text import slugify
    from datetime import date, timedelta

    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')
    nome_fantasia = request.data.get('nome_fantasia', '').strip()
    nome_exibicao = request.data.get('nome_exibicao', nome_fantasia).strip()
    telefone = request.data.get('telefone', '')
    documento = request.data.get('documento', '')
    especialidade = request.data.get('especialidade', '').strip()
    # validações básicas
    if not email or not password:
        return Response(
            {'error': 'Email e senha são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not nome_fantasia:
        return Response(
            {'error': 'Nome do profissional ou clínica é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email já cadastrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # gera slug único a partir do nome
    base_slug = slugify(nome_fantasia)[:45]
    slug = base_slug
    counter = 1
    while Tenant.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # 1) cria Tenant (plano basico por padrão)
    with transaction.atomic():
        tenant = Tenant.objects.create(
            slug=slug,
            nome_fantasia=nome_fantasia,
            documento=documento,
            email=email,
            telefone=telefone,
            plano='basico',
            limite_clientes=10,
            data_inicio_plano=date.today(),
            data_fim_plano=date.today() + timedelta(days=365),
            ativo=True,
        )

        # 2) cria User vinculado ao tenant
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=nome_exibicao or nome_fantasia,   # campo nome do seu User customizado
            tenant=tenant,
            tipo_usuario='Profissional',
        )

        # 3) cria Profissional vinculado ao user e tenant
        profissional = Profissional.objects.create(
            user=user,
            nome_exibicao=nome_exibicao or nome_fantasia,
            especialidade=especialidade,
            telefone=telefone,
            email=email,
            ativo=True,
        )
        profissional.tenants.add(tenant)

        ProfissionalTenant.objects.get_or_create(
            profissional=profissional,
            tenant=tenant,
        )

        # 4) retorna tokens JWT para login automático
    refresh = RefreshToken.for_user(user)

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': str(user.id),
            'email': user.email,
            'nome': profissional.nome_exibicao,
            'especialidade': profissional.especialidade,
            'tenant': str(tenant.id),
            'tenant_slug': tenant.slug,
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def ping_public(request):
    return Response({"message": "pong public"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ping_protected(request):
    user = request.user
    return Response({"message": f"pong protected for {user.username}"})


def healthcheck(request):
    return HttpResponse("OK")


class PortalClientePublicView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = PortalClienteActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        portal_cliente = serializer.save()

        return Response(
            {
                "detail": "Cadastro finalizado com sucesso.",
                "email": portal_cliente.email,
                "cadastro_finalizado": portal_cliente.cadastro_finalizado,
            },
            status=status.HTTP_200_OK
        )

class PortalclienteView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        portal_cliente = validar_token_portal_cliente(
            token=token,
            validar_vigencia=True
        )

        dados = {
            "portal_cliente": {
                "id": portal_cliente.id,
                "nome": portal_cliente.nome,
                "email": portal_cliente.email,
                "telefone": portal_cliente.telefone,
                "cadastro_finalizado": portal_cliente.cadastro_finalizado,
                "contrato_inicio": portal_cliente.contrato_inicio,
                "contrato_fim": portal_cliente.contrato_fim,
                "acesso_ativo": portal_cliente.acesso_ativo,
            },
            "tenant": {
                "id": portal_cliente.tenant.id,
                "nome": getattr(portal_cliente.tenant, "nome_fantasia", None),
            },
            # plugar dados reais do seu domínio:
            # "pacotes": ...,
            # "presencas": ...,
            # "faturas": ...,
        }
        return Response(dados, status=status.HTTP_200_OK)


class PortalClienteActivateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = PortalClienteActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        portal_cliente = serializer.save()

        return Response(
            {
                "detail": "Cadastro finalizado com sucesso.",
                "email": portal_cliente.email,
                "cadastro_finalizado": portal_cliente.cadastro_finalizado,
            },
            status=status.HTTP_200_OK
        )



class PortalClienteViewSet(viewsets.ModelViewSet):
    serializer_class = PortalClienteSerializer

    def get_queryset(self):
        user = self.request.user
        return PortalCliente.objects.filter(tenant__user=user).select_related("tenant", "user")

    def perform_create(self, serializer):
        tenant = getattr(self.request.user, "tenant_owner", None)
        if tenant is None:
            raise ValueError("Usuário não possui tenant associado.")
        serializer.save(tenant=tenant)

    def _enviar_convite(self, request, portal_cliente):
        token = gerar_token_portal_cliente(portal_cliente)

        frontend_url = getattr(
            settings,
            "PORTAL_CLIENTE_FRONTEND_URL",
            "https://seu-frontend.com/cliente/portal"
        )

        link_portal = f"{frontend_url}/{token}"
        link_ativacao = f"{frontend_url}/ativar?token={token}"

        send_mail(
            subject="Acesso ao portal do cliente",
            message=(
                f"Olá, {portal_cliente.nome}!\n\n"
                f"Acesse seu portal pelo link:\n{link_portal}\n\n"
                f"Para ativar seu cadastro e definir senha:\n{link_ativacao}\n\n"
                f"Esse acesso expira em 3 dias."
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[portal_cliente.email],
            fail_silently=False,
        )

        return Response(
            {
                "detail": "Convite enviado com sucesso.",
                "email": portal_cliente.email,
                "cadastro_finalizado": portal_cliente.cadastro_finalizado,
                "link_debug_portal": link_portal,
                "link_debug_ativacao": link_ativacao,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="enviar-convite")
    def enviar_convite(self, request, pk=None):
        portal_cliente = self.get_object()
        return self._enviar_convite(request, portal_cliente)

    @action(detail=True, methods=["post"], url_path="reenviar-convite")
    def reenviar_convite(self, request, pk=None):
        portal_cliente = self.get_object()
        return self._enviar_convite(request, portal_cliente)

    @action(detail=True, methods=["post"], url_path="desativar-acesso")
    def desativar_acesso(self, request, pk=None):
        portal_cliente = self.get_object()
        portal_cliente.acesso_ativo = False
        portal_cliente.save(update_fields=["acesso_ativo", "updated_at"])

        return Response(
            {"detail": "Acesso ao portal desativado com sucesso."},
            status=status.HTTP_200_OK
        )

class MeuPortalAutenticadoView(APIView):
    permission_classes = [IsAuthenticatedPortalCliente]

    def get(self, request):
        portal_cliente = request.portal_cliente

        return Response(
            {
                "portal_cliente": {
                    "id": portal_cliente.id,
                    "nome": portal_cliente.nome,
                    "email": portal_cliente.email,
                },
                "tenant": {
                    "id": portal_cliente.tenant.id,
                    "nome": getattr(portal_cliente.tenant, "nome_fantasia", None),
                }
            },
            status=status.HTTP_200_OK
        )

def validar_limite_profissionais(tenant):
    plano = tenant.plano
    total_ativos = tenant.profissionais.filter(ativo=True).count()

    if total_ativos >= plano.max_profissionais:
        raise ValidationError({
            "detail": f"Seu plano permite até {plano.max_profissionais} profissionais ativos."
        })

class ClienteViewSet(BaseTenantViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            print('--- CLIENTES get_queryset ---')
            print('REQUEST USER:', self.request.user)

            tenant = self.get_tenant()
            print('TENANT RESOLVIDO:', tenant, tenant.id)

            qs = Cliente.objects.filter(tenant=tenant).order_by('nome')
            print('QS OK / TOTAL:', qs.count())

            return qs
        except Exception as e:
            print('ERRO get_queryset CLIENTES:', repr(e))
            raise

    def perform_create(self, serializer):
        try:
            tenant = self.get_tenant()
            print('--- CLIENTES perform_create ---')
            print('TENANT RESOLVIDO:', tenant, tenant.id)
            serializer.save(tenant=tenant)
        except Exception as e:
            print('ERRO perform_create CLIENTES:', repr(e))
            raise

    def perform_update(self, serializer):
        try:
            tenant = self.get_tenant()
            print('--- CLIENTES perform_update ---')
            print('TENANT RESOLVIDO:', tenant, tenant.id)
            serializer.save(tenant=tenant)
        except Exception as e:
            print('ERRO perform_update CLIENTES:', repr(e))
            raise

class MyProfissionalFotoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        profissional = getattr(request.user, 'perfil_profissional', None)
        if not profissional:
            return Response(
                {"detail": "Perfil do profissional não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        foto = request.FILES.get('foto')
        if not foto:
            return Response(
                {"detail": "Arquivo de foto não enviado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        profissional.foto = foto
        profissional.save(update_fields=['foto'])

        foto_url = request.build_absolute_uri(profissional.foto.url) if profissional.foto else None
        return Response({'foto': foto_url, 'foto_url': foto_url}, status=status.HTTP_200_OK)

    def delete(self, request):
        profissional = getattr(request.user, 'perfil_profissional', None)
        if not profissional:
            return Response(
                {"detail": "Perfil do profissional não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        if profissional.foto:
            profissional.foto.delete(save=False)

        profissional.foto = None
        profissional.save(update_fields=['foto'])
        return Response({'foto': None, 'foto_url': None}, status=status.HTTP_200_OK)

class MyFotoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Perfil do usuário não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProfileFotoSerializer(
            profile,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Perfil do usuário não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.foto:
            profile.foto.delete(save=False)
        profile.foto = None
        profile.save(update_fields=['foto'])
        return Response({'foto': None, 'foto_url': None}, status=status.HTTP_200_OK)
    
class PacoteSessoesViewSet(BaseTenantViewSet):
    queryset = PacoteSessoes.objects.all()
    serializer_class = PacoteSessoesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_profissional_no_tenant(self):
        tenant = self.get_tenant()
        user = self.request.user

        profissional = Profissional.objects.filter(user=user).first()
        if not profissional:
            raise ValidationError('Profissional não encontrado para o usuário atual.')

        membership = ProfissionalTenant.objects.filter(
            profissional=profissional,
            tenant=tenant,
            
        ).first()

        if not membership:
            raise ValidationError('O profissional não possui acesso ao tenant selecionado.')

        return profissional
    
    def get_queryset(self):
        tenant = self.get_tenant()
        qs = super().get_queryset().filter(tenant=tenant).select_related('cliente', 'profissional')

        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)

        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        profissional = self.get_profissional_no_tenant()

        plano_tenant = getattr(tenant, 'plano', 'free')
        plano_pacote = 'basico' if plano_tenant == 'free' else plano_tenant

        serializer.save(
            tenant=tenant,
            profissional=profissional,
            plano_tipo=plano_pacote
        )

    def perform_update(self, serializer):
        tenant = self.get_tenant()
        profissional = self.get_profissional_no_tenant()

        serializer.save(
            tenant=tenant,
            profissional=profissional
        )
        
class SessaoViewSet(BaseTenantViewSet):
    queryset = Sessao.objects.all()
    serializer_class = SessaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = self.get_tenant()
        qs = super().get_queryset().filter(tenant=tenant).select_related(
            'cliente', 'profissional', 'pacote'
        )

        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)

        pacote_id = self.request.query_params.get('pacote')
        if pacote_id:
            qs = qs.filter(pacote_id=pacote_id)

        data_inicio = self.request.query_params.get('data_inicio')
        if data_inicio:
            qs = qs.filter(data_hora_inicio__date=data_inicio)

        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs.order_by('data_hora_inicio')

    def perform_create(self, serializer):
        serializer.save(tenant=self.get_tenant())

    def perform_update(self, serializer):
        serializer.save(tenant=self.get_tenant())

class FaturaViewSet(viewsets.ModelViewSet):
    """
    CRUD de Faturas filtrado por tenant.
    """
    serializer_class = FaturaSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'cliente', 'data_vencimento']
    search_fields = ['cliente__nome']

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Fatura.objects.select_related('cliente', 'responsavel', 'pacote')
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)

    @action(detail=True, methods=['post'])
    def marcar_paga(self, request, pk=None):
        """
        Marca a fatura como paga.
        POST /api/v1/faturas/{id}/marcar_paga/
        """
        fatura = self.get_object()
        if fatura.status == 'paga':
            return Response(
                {'detail': 'Fatura já está paga.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        fatura.status = 'paga'
        fatura.valor_pago = fatura.valor_total
        fatura.save()
        return Response(FaturaSerializer(fatura).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancela a fatura.
        POST /api/v1/faturas/{id}/cancelar/
        """
        fatura = self.get_object()
        if fatura.status == 'cancelada':
            return Response(
                {'detail': 'Fatura já está cancelada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        fatura.status = 'cancelada'
        fatura.save()
        return Response(FaturaSerializer(fatura).data, status=status.HTTP_200_OK)


class PagamentoViewSet(viewsets.ModelViewSet):
    """
    CRUD de Pagamentos filtrado por tenant.
    """
    serializer_class = PagamentoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'fatura', 'data_pagamento', 'metodo']
    search_fields = ['fatura__cliente__nome']

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Pagamento.objects.select_related('fatura', 'fatura__cliente')
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)

    @action(detail=True, methods=['post'])
    def confirmar_pagamento(self, request, pk=None):
        """
        Confirma o pagamento e marca a fatura como paga.
        POST /api/v1/pagamentos/{id}/confirmar_pagamento/
        """
        pagamento = self.get_object()
        if pagamento.status == 'confirmado':
            return Response(
                {'detail': 'Pagamento já foi confirmado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pagamento.status = 'confirmado'
        pagamento.save()
        
        # Marca fatura como paga
        fatura = pagamento.fatura
        fatura.status = 'paga'
        fatura.valor_pago = pagamento.valor
        fatura.save()
        
        return Response(PagamentoSerializer(pagamento).data, status=status.HTTP_200_OK)


class ContratoViewSet(viewsets.ModelViewSet):
    """
    CRUD de Contratos filtrado por tenant.
    """
    serializer_class = ContratoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Contrato.objects.select_related('cliente', 'pacote', 'tenant')
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)

class ProfissionalViewSet(viewsets.ModelViewSet):
    """
    CRUD de Profissionales filtrado por tenant.
    """
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Profissional.objects.all()
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = self.request.user.tenant
        profissional = serializer.validated_data.get('profissional')

        if not profissional.tenants.filter(id=tenant.id).exists():
            raise ValidationError('Profissional não pertence a este tenant.')

        serializer.save(tenant=tenant)

class VincularProfissionalTenantView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            raise ValidationError('Tenant ativo não encontrado na requisição.')

        profissional_id = request.data.get('profissional_id')
        if not profissional_id:
            raise ValidationError({'profissional_id': 'Informe o profissional.'})

        validar_multiplos_profissionais(tenant)

        profissional = Profissional.objects.filter(id=profissional_id).first()
        if not profissional:
            raise ValidationError('Profissional não encontrado.')

        vinculo, created = ProfissionalTenant.objects.get_or_create(
            profissional=profissional,
            tenant=tenant,
            defaults={'ativo': True}
        )

        if not created and not vinculo.ativo:
            vinculo.ativo = True
            vinculo.save()

        return Response({
            'detail': 'Profissional vinculado ao tenant com sucesso.'
        })

class ResponsavelViewSet(viewsets.ModelViewSet):
    """
    CRUD de Responsáveis filtrado por tenant.
    """
    serializer_class = ResponsavelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Responsavel.objects.select_related('user')
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs

    def perform_create(self, serializer):
        tenant = self.request.user.tenant
        profissional = serializer.validated_data.get('profissional')

        if not profissional.tenants.filter(id=tenant.id).exists():
            raise ValidationError('Profissional não pertence a este tenant.')

        serializer.save(tenant=tenant)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    profissional = getattr(user, 'perfil_profissional', None)
    tenant = getattr(user, 'tenant', None)

    tenants = []
    if profissional:
        tenants = [
            {
                'id': str(t.id),
                'nome_fantasia': t.nome_fantasia,
                'slug': t.slug,
                'plano': t.plano,
            }
            for t in profissional.tenants.filter(ativo=True)
        ]
    foto_url = None
    if profissional and profissional.foto:
        foto_url = request.build_absolute_uri(profissional.foto.url)
    elif getattr(user, 'profile', None) and user.profile.foto:
        foto_url = request.build_absolute_uri(user.profile.foto.url)


    return Response({
        'id': str(user.id),
        'email': user.email,
        'tipo_usuario': user.tipo_usuario,
        'nome': profissional.nome_exibicao if profissional else user.first_name,
        'especialidade': profissional.especialidade if profissional else '',
        'user_nome': user.first_name,
        'tenant_id': str(tenant.id) if tenant else None,
        'tenant_nome': tenant.nome_fantasia if tenant else None,
        'foto': foto_url,
        'tenants': tenants,
        'profissional': {
            'id': str(profissional.id),
            'nome_exibicao': profissional.nome_exibicao,
            'email': profissional.email,
            'telefone': profissional.telefone,
            'foto': foto_url,
        } if profissional else None,
        
    })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'detail': 'refresh_token é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Logout realizado com sucesso.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'detail': 'Token inválido.'}, status=status.HTTP_400_BAD_REQUEST)