from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from attend.models import Sessao, Fatura, Pagamento, Contrato
from attend.serializers import SessaoSerializer, FaturaSerializer, PagamentoSerializer, ContratoSerializer
from attend.views import (home, healthcheck, ping_public, ping_protected, register_view, ClienteViewSet, PacoteSessoesViewSet, 
    SessaoViewSet,
    FaturaViewSet,
    PagamentoViewSet,
    ContratoViewSet,
    ProfissionalViewSet,
    ResponsavelViewSet,
    PortalClientePublicView,
    PortalClienteViewSet,
    PortalclienteView,
    PortalClienteActivateView,
    MeuPortalAutenticadoView,
    MyFotoUploadView,
    MyProfissionalFotoUploadView,
    VincularProfissionalTenantView,
    LogoutView,
    me_view,
)
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import action
from rest_framework import status

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r"portal-clientes", PortalClienteViewSet, basename="portal-clientes")
router.register(r'responsaveis', ResponsavelViewSet, basename='responsavel')
router.register(r'pacotes-sessoes', PacoteSessoesViewSet, basename='pacotesessoes')
router.register(r'sessoes', SessaoViewSet, basename='sessao')
router.register(r'faturas', FaturaViewSet, basename='fatura')
router.register(r'pagamentos', PagamentoViewSet, basename='pagamento')
router.register(r'contratos', ContratoViewSet, basename='contrato')
router.register(r'profissionais', ProfissionalViewSet, basename='profissional')


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('health/', healthcheck),
    path('api/ping-public/', ping_public),
    path('api/ping-protected/', ping_protected),

    # JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Perfil do usuário logado
    path('api/v1/me/', me_view, name='me'),
    path('api/v1/me/foto/', MyFotoUploadView.as_view(), name='me-foto'),
    path('api/v1/me/profissional/foto/', MyProfissionalFotoUploadView.as_view(), name='me-profissional-foto'),
    
    # API v1
    path('api/v1/', include(router.urls)),
    
    # Cadastro público (sem autenticação)
    path('api/v1/registro-profissional/', register_view, name='registro-profissional'),
    
    # Portal do cliente
    path('portal/cliente/<str:token>/', PortalClientePublicView.as_view(), name='portal-cliente-publico'),
    path("portal/cliente/ativar/", PortalClienteActivateView.as_view(), name="portal-cliente-ativar"),
    path("portal/cliente/me/", MeuPortalAutenticadoView.as_view(), name="portal-cliente-me"),
   
    #Tenant
    path('api/v1/tenant/vincular-profissional/', VincularProfissionalTenantView.as_view(), name='tenant-vincular-profissional'),
    
    #Logout
    path('api/v1/logout/', LogoutView.as_view(), name='logout'),
]
    


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




