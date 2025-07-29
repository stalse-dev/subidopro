from django.urls import path
from .views import *

urlpatterns = [
    path('cliente_criar/', AlunoClienteCreateAPIView.as_view(), name='cliente_criar'),
    path('cliente_detalhes/<int:pk>/', AlunoClienteDetailAPIView.as_view(), name='cliente_detalhes'),

    path('contrato_criar/', AlunoClientesContratosAPIView.as_view(), name='contrato_criar'),
    path('contrato_detalhes/<int:pk>/', AlunoClientesContratosDetailAPIView.as_view(), name='contrato_detalhes'),

    path('envio_criar/', AlunoEnvioCreateAPIView.as_view(), name='envio_criar'),
    path('envio_detalhes/<int:pk>/', AlunoEnvioDetailAPIView.as_view(), name='envio_detalhes'),

    path('desafio_criar/', DesafioCreateAPIView.as_view(), name='desafio_criar'),
    path('desafio_detalhes/<int:pk>/', DesafioDetailAPIView.as_view(), name='desafio_detalhes'),

    path('desafio_aluno_criar/', AlunoDesafioCreateAPIView.as_view(), name='desafio_aluno_criar'),
    path('desafio_aluno_detalhes/<int:pk>/', AlunoDesafioDetailAPIView.as_view(), name='desafio_aluno_detalhes'),

    path('certificacao_criar/', AlunoCertificacaoCreateAPIView.as_view(), name='certificacao_criar'),
    path('certificacao_detalhes/<int:pk>/', AlunoCertificacaoDetailAPIView.as_view(), name='certificacao_detalhes'),

    path('manual_criar/', AlunoManualCreateAPIView.as_view(), name='manual_criar'),
    path('manual_detalhes/<int:pk>/', AlunoManualDetailAPIView.as_view(), name='manual_detalhes'),

    path('aluno_criar/', AlunoCreateAPIView.as_view(), name='aluno_criar'),
    path('aluno_detalhes/<int:pk>/', AlunoDetailAPIView.as_view(), name='aluno_detalhes')
]
''