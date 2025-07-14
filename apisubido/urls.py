from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('home/<int:aluno_id>/', HomeAPIView.as_view(), name='home'),
    path('extrato/<int:aluno_id>/', ExtratoAPIView.as_view(), name='extrato'),
    path('ranking_semanal/', RankingSemanalAPIView.as_view(), name='ranking_semanal'),
    
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
