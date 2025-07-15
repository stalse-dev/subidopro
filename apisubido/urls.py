from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('home/<int:aluno_id>/', HomeAPIView.as_view(), name='home'),
    path("subidometro/<int:aluno_id>/", SubdometroAPIView.as_view(), name="subidometro"),
    path('extrato/<int:aluno_id>/', ExtratoAPIView.as_view(), name='extrato'),
    path('clientes/<int:aluno_id>/', ClientesAPIView.as_view(), name='clientes'),
    path('detalhes_cliente/<int:cliente_id>/', DetalhesClientesAPIView.as_view(), name='detalhes_cliente'),
    path('meus_envios/<int:aluno_id>/', MeusEnviosAPIView.as_view(), name='meus_envios'),
    path('campeonato/', RankingSemanalAPIView.as_view(), name='campeonato'),
    
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
