from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tenant, Cliente, Profissional, PacoteSessoes, Sessao, Fatura, Pagamento, Contrato, Responsavel, User

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['nome_fantasia', 'slug', 'plano', 'ativo']
    list_filter = ['plano', 'ativo']
    search_fields = ['nome_fantasia', 'slug']
    fields = ['slug', 'nome_fantasia', 'documento', 'email', 'telefone', 'plano', 'limite_clientes', 'data_inicio_plano', 'data_fim_plano', 'ativo']
    readonly_fields = ['created_at']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'tipo_usuario', 'tenant', 'is_staff']
    list_filter = ['tipo_usuario', 'is_staff', 'is_superuser', 'ativo']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'telefone')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Organização', {'fields': ('tenant', 'tipo_usuario', 'ativo')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'tipo_usuario', 'tenant'),
        }),
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tenant', 'data_nascimento']
    search_fields = ['nome']
    list_filter = ['tenant']


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome_exibicao', 'email')
    search_fields = ['nome_exibicao']
    list_filter = ['user']


@admin.register(PacoteSessoes)
class PacoteSessoesAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'profissional', 'tenant', 'status']
    search_fields = ['cliente__nome']
    list_filter = ['tenant', 'status']


@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    list_display = ['pacote', 'data_hora_inicio', 'status', 'tenant']
    list_filter = ['tenant', 'status']
    search_fields = ['pacote__cliente__nome']


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'valor_total', 'status', 'data_vencimento']
    list_filter = ['tenant', 'status']
    search_fields = ['cliente__nome']


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'tenant', 'status']
    list_filter = ['tenant', 'status']


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'pacote', 'tenant', 'status']
    list_filter = ['tenant', 'status']
    search_fields = ['cliente__nome']
