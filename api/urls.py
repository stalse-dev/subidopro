from django.urls import path, include
from .views import *

urlpatterns = [
    path('receber-dados/', receber_dados, name='receber_dados'),
    path('recebimentos_alunos/<int:aluno_id>/', recebimentos_alunos, name='recebimentos_alunos'),
    path('painel_inicial_aluno/<int:aluno_id>/', painel_inicial_aluno, name='painel_inicial_aluno'),
    path('meus_clientes/<int:aluno_id>/', meus_clientes, name='meus_clientes'),
    path('logsweb/', listar_logs, name='listar_logs'),
    path('detalhes-log/<int:log_id>/', detalhes_log, name='detalhes_log'),
]