from django.urls import path
from .views import *

urlpatterns = [
    path('cliente_criar/', AlunoClienteCreateAPIView.as_view(), name='cliente_criar'),
    path('cliente_detalhes/<int:pk>/', AlunoClienteDetailAPIView.as_view(), name='cliente_detalhes'),

    path('contrato_criar/', AlunoClientesContratosAPIView.as_view(), name='contrato_criar'),
    path('contrato_detalhes/<int:pk>/', AlunoClientesContratosDetailAPIView.as_view(), name='contrato_detalhes'),

    path('envio_criar/', AlunoEnvioCreateAPIView.as_view(), name='envio_criar'),
    path('envio_detalhes/<int:pk>/', AlunoEnvioDetailAPIView.as_view(), name='envio_detalhes'),
]
