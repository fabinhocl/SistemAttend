from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Cliente, PacoteSessoes, Profissional, Tenant, Sessao, Contrato, Fatura, Pagamento, Responsavel, User, Profile, PortalCliente, ProfissionalTenant
from attend.services.portal_tokens import validar_token_portal_cliente

User = get_user_model()

class TenantOptionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()
    plano = serializers.CharField()


class MeSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='id')
    email = serializers.EmailField(source='user.email')
    nome_exibicao = serializers.CharField()
    tenants = serializers.SerializerMethodField()

    def get_tenants(self, obj):
        memberships = ProfissionalTenant.objects.filter(
            profissional=obj,
            ativo=True
        ).select_related('tenant')

        return [
            {
                'id': item.tenant.id,
                'nome': item.tenant.nome,
                'plano': item.tenant.plano,
            }
            for item in memberships
        ]

class PortalClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalCliente
        fields = [
            "id",
            "tenant",
            "nome",
            "cpf",
            "data_nascimento",
            "email",
            "telefone",
            "contrato_inicio",
            "contrato_fim",
            "acesso_ativo",
            "cadastro_finalizado",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["tenant", "cadastro_finalizado", "created_at", "updated_at"]

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        contrato_inicio = attrs.get("contrato_inicio", getattr(self.instance, "contrato_inicio", None))
        contrato_fim = attrs.get("contrato_fim", getattr(self.instance, "contrato_fim", None))

        if contrato_inicio and contrato_fim and contrato_fim < contrato_inicio:
            raise serializers.ValidationError({
                "contrato_fim": "A data final do contrato não pode ser menor que a data inicial."
            })

        return attrs



class PortalClienteActivateSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        portal_cliente = validar_token_portal_cliente(
            attrs["token"],
            validar_vigencia=True
        )
        attrs["portal_cliente"] = portal_cliente
        return attrs

    def save(self, **kwargs):
        portal_cliente = self.validated_data["portal_cliente"]
        password = self.validated_data["password"]

        user = portal_cliente.user
        if user is None:
            user = User.objects.create_user(
                username=portal_cliente.email,
                email=portal_cliente.email,
                password=password,
            )
        else:
            user.set_password(password)
            user.save(update_fields=["password"])

        portal_cliente.user = user
        portal_cliente.cadastro_finalizado = True
        portal_cliente.save(update_fields=["user", "cadastro_finalizado", "updated_at"])

        return portal_cliente

class ClienteSerializer(serializers.ModelSerializer):
    responsavel = serializers.CharField(
        source='responsavel.user.username', read_only=True
    )

    class Meta:
        model = Cliente
        fields = [
            'id', 'tenant', 'nome', 'data_nascimento', 'cpf', 'email', 'telefone',
            'responsavel', 'observacoes', 'user', 'created_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at']



class ProfissionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profissional
        fields = '__all__'
        read_only_fields = ['id', 'tenant']



class ProfileFotoSerializer(serializers.ModelSerializer):
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['foto', 'foto_url']

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        return None

    def validate_foto(self, value):
        max_size = 5 * 1024 * 1024

        if value.size > max_size:
            raise serializers.ValidationError('Imagem deve ter no máximo 5 MB.')
        
        valid_types = ['image/jpeg', 'image/png', 'image/webp']

        if getattr(value, 'content_type', None) not in valid_types:
            raise serializers.ValidationError('Formato inválido. Use JPG, PNG ou WEBP.')
        return value


class SessaoPreviewSerializer(serializers.Serializer):
    numero = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=['pendente', 'realizada', 'falta'])

class ParcelaPreviewSerializer(serializers.Serializer):
    numero = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=['pendente', 'pago', 'atrasado'])
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)


class PacoteSessoesSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome_exibicao', read_only=True)
    sessoes_restantes = serializers.ReadOnlyField()
    plano_tipo = serializers.CharField(read_only=True)

    sessoes_preview = SessaoPreviewSerializer(many=True, required=False)
    parcelas_preview = ParcelaPreviewSerializer(many=True, required=False)

    class Meta:
        model = PacoteSessoes
        fields = [
            'id',
            'tenant',
            'cliente', 'cliente_nome',
            'profissional', 'profissional_nome',
            'plano_tipo',
            'descricao',
            'qtd_sessoes',
            'qtd_sessoes_usadas',
            'sessoes_restantes',
            'data_inicio',
            'data_fim',
            'valor_por_sessao',
            'valor_total',
            'qtd_parcelas',
            'valor_parcela',
            'dia_pagamento',
            'status',
            'sessoes_preview',
            'parcelas_preview',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'tenant',
            'profissional',
            'plano_tipo',
            'qtd_sessoes_usadas',
            'sessoes_restantes',
            'valor_total',
            'valor_parcela',
            'status',
            'created_at',
        ]

    def validate_dia_pagamento(self, value):
        if value < 1 or value > 31:
            raise serializers.ValidationError('O dia de pagamento deve estar entre 1 e 31.')
        return value

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)

        plano_tipo = getattr(instance, 'plano_tipo', None)
        if plano_tipo is None:
            request = self.context.get('request')
            tenant = getattr(request, 'tenant', None) if request else None
            user = getattr(request, 'user', None) if request else None
            if tenant is None and user is not None:
                tenant = getattr(user, 'tenant', None)
            plano_tipo = getattr(tenant, 'plano', 'free')

        qtd_sessoes = attrs.get('qtd_sessoes', getattr(instance, 'qtd_sessoes', 0))
        qtd_parcelas = attrs.get('qtd_parcelas', getattr(instance, 'qtd_parcelas', 0))
        valor_por_sessao = attrs.get('valor_por_sessao', getattr(instance, 'valor_por_sessao', 0))
        data_inicio = attrs.get('data_inicio', getattr(instance, 'data_inicio', None))
        data_fim = attrs.get('data_fim', getattr(instance, 'data_fim', None))
        sessoes_preview = attrs.get('sessoes_preview', getattr(instance, 'sessoes_preview', []))
        parcelas_preview = attrs.get('parcelas_preview', getattr(instance, 'parcelas_preview', []))

        if qtd_sessoes < 1:
            raise serializers.ValidationError({
                'qtd_sessoes': 'Informe pelo menos 1 sessão.'
            })

        if qtd_parcelas < 1:
            raise serializers.ValidationError({
                'qtd_parcelas': 'Informe pelo menos 1 parcela.'
            })

        if valor_por_sessao is None or valor_por_sessao < 0:
            raise serializers.ValidationError({
                'valor_por_sessao': 'Informe um valor por sessão válido.'
            })

        if data_inicio and data_fim and data_fim < data_inicio:
            raise serializers.ValidationError({
                'data_fim': 'A data final não pode ser menor que a data inicial.'
            })

        if plano_tipo in ['free', 'basico']:
            if len(sessoes_preview) != qtd_sessoes:
                raise serializers.ValidationError({
                    'sessoes_preview': 'A quantidade de sessões no preview deve corresponder à quantidade de sessões.'
                })

            if len(parcelas_preview) != qtd_parcelas:
                raise serializers.ValidationError({
                    'parcelas_preview': 'A quantidade de parcelas no preview deve corresponder à quantidade de parcelas.'
                })

        return attrs

    def _normalize_sessoes_preview(self, sessoes_preview):
        normalized = []

        for item in sessoes_preview:
            normalized.append({
                'numero': int(item.get('numero')),
                'status': item.get('status'),
            })

        return normalized

    def _normalize_parcelas_preview(self, parcelas_preview):
        normalized = []

        for item in parcelas_preview:
            valor = item.get('valor', 0)

            normalized.append({
                'numero': int(item.get('numero')),
                'status': item.get('status'),
                'valor': float(valor) if valor is not None else 0.0,
            })

        return normalized

    def create(self, validated_data):
        sessoes_preview = validated_data.pop('sessoes_preview', [])
        parcelas_preview = validated_data.pop('parcelas_preview', [])

        instance = PacoteSessoes.objects.create(**validated_data)
        instance.sessoes_preview = self._normalize_sessoes_preview(sessoes_preview)
        instance.parcelas_preview = self._normalize_parcelas_preview(parcelas_preview)
        instance.save()

        return instance

    def update(self, instance, validated_data):
        sessoes_preview = validated_data.pop('sessoes_preview', None)
        parcelas_preview = validated_data.pop('parcelas_preview', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if sessoes_preview is not None:
            instance.sessoes_preview = self._normalize_sessoes_preview(sessoes_preview)
            instance.qtd_sessoes_usadas = sum(
                1 for s in instance.sessoes_preview if s.get('status') == 'realizada'
            )
        
        if parcelas_preview is not None:
            instance.parcelas_preview = self._normalize_parcelas_preview(parcelas_preview)

        instance.save()
        return instance
    

class ContratoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    pacote_descricao = serializers.CharField(source='pacote.descricao', read_only=True)

    class Meta:
        model = Contrato
        fields = '__all__'
        read_only_fields = ['id', 'tenant']


class SessaoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome_exibicao', read_only=True)
    pacote_descricao = serializers.CharField(source='pacote.descricao', read_only=True)
    origem_remarcacao_id = serializers.PrimaryKeyRelatedField(
        source='origem_remarcacao',
        read_only=True,
    )

    class Meta:
        model = Sessao
        fields = [
            'id',
            'tenant',
            'pacote', 'pacote_descricao',
            'cliente', 'cliente_nome',
            'profissional', 'profissional_nome',
            'data_hora_inicio',
            'data_hora_fim',
            'status',
            'observacoes',
            'motivo_cancelamento',
            'origem_remarcacao_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'tenant',
            'profissional',
            'origem_remarcacao_id',
            'created_at',
            'updated_at',
        ]


class FaturaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    responsavel = serializers.CharField(source='responsavel.user.username', read_only=True)
    pacote_descricao = serializers.CharField(source='pacote.descricao', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Fatura
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at']
    
    def get_status_display(self, obj):
        return obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status


class PagamentoSerializer(serializers.ModelSerializer):
    fatura_cliente = serializers.CharField(source='fatura.cliente.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fatura_valor = serializers.CharField(source='fatura.valor_total', read_only=True)

    class Meta:
        model = Pagamento
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at']
    
    def get_status_display(self, obj):
        return obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status


class ResponsavelSerializer(serializers.ModelSerializer):
    user_nome = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Responsavel
        fields = '__all__'
        read_only_fields = ['id', 'tenant']