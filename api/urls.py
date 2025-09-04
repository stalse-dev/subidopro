from django.urls import path, include
from .views import *

urlpatterns = [
    path('receber-dados/', receber_dados, name='receber_dados'),
    path('dados-subdometro/', dados_subdometro, name='dados_subdometro'),
    path('dados-alunos/', dados_alunos, name='dados_alunos'),
    path('recebimentos_alunos/<int:aluno_id>/', recebimentos_alunos, name='recebimentos_alunos'),
    path('painel_inicial_aluno/<int:aluno_id>/', painel_inicial_aluno, name='painel_inicial_aluno'),
    path('meus_clientes/<int:aluno_id>/', meus_clientes, name='meus_clientes'),
    path('meus_envios/<int:aluno_id>/', meus_envios, name='meus_envios'),
    path('subdometro_aluno/<int:aluno_id>/', subdometro_aluno, name='subdometro_aluno'),
    path('detalhes_cliente/<int:aluno_id>/<str:cliente_md5>/', detalhes_cliente, name='detalhes_cliente'),
    path('cartilha_aluno/<int:aluno_id>/', cartilha_aluno, name='cartilha_aluno'),
    path('ranking/', rankingAPI, name='ranking'),
    path('ranking_semanal/', ranking_semanalAPI, name='ranking_semanal'),
    path('ranking_semanal_cla/', ranking_semanal_claAPI, name='ranking_semanal_cla'),
    path('meu_cla/<int:aluno_id>/', meu_cla, name='meu_cla'),
    path('logsweb/', listar_logs, name='listar_logs'),
    path('detalhes-log/<int:log_id>/', detalhes_log, name='detalhes_log'),
]