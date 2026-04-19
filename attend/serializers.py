from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Cliente, PacoteSessoes, Profissional, Tenant, Sessao, Contrato, Fatura, Pagamento, Responsavel, User, Profile
from attend.models import PortalCliente
from attend.services.portal_tokens import validar_token_portal_cliente

User = get_user_model()


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
    responsavel_nome = serializers.CharField(
        source='responsavel.user.username', read_only=True
    )

    class Meta:
        model = Cliente
        fields = [
            'id', 'tenant', 'nome', 'data_nascimento', 'cpf', 'email', 'telefone',
            'responsavel', 'responsavel_nome',
            'observacoes', 'user', 'created_at',
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


class PacoteSessoesSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome_exibicao', read_only=True)
    sessoes_restantes = serializers.ReadOnlyField()

    class Meta:
        model = PacoteSessoes
        fields = [
            'id', 'tenant',
            'cliente', 'cliente_nome',
            'profissional', 'profissional_nome',
            'descricao',
            'qtd_sessoes', 'qtd_sessoes_usadas', 'sessoes_restantes',
            'data_inicio', 'data_fim',
            'valor_por_sessao', 'valor_total',
            'qtd_parcelas', 'valor_parcela', 'dia_pagamento',
            'status',
            'created_at',
        ]
        read_only_fields = [
            'id', 'tenant', 'profissional',
            'qtd_sessoes_usadas', 'sessoes_restantes',
            'valor_total', 'valor_parcela',
            'status', 'created_at',
        ]


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
    responsavel_nome = serializers.CharField(source='responsavel.user.username', read_only=True)
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