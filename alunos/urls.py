from django.urls import path, include
from .views import *

urlpatterns = [
    path('', ranking_semana, name='ranking_semana_home'),
    path('alunos/', alunos, name='alunos'),
    path('aluno/<int:aluno_id>/', aluno, name='aluno'),
    path('aluno/<int:aluno_id>/pontos/', aluno_pontos, name='aluno-pontos'),
    path('aluno/<int:aluno_id>/clientes/', aluno_clientes, name='aluno-clientes'),
    path('aluno/<int:aluno_id>/faturamento/', aluno_faturamento, name='aluno-faturamento'),
    path('balanceamento/', balanceamento, name='balanceamento'),
    path('retencao/', retencao, name='retencao'),
    path('ranking/', ranking, name='ranking'),
    path('ranking_semana/', ranking_semana, name='ranking_semana'),
    path('ranking_cla/', ranking_cla, name='ranking_cla'),
    path('clas/', clas, name='clas'),
    path('cla/<int:cla_id>/', cla, name='cla'),
    path('clientes/', clientes, name='clientes'),
    path('cliente/<int:cliente_id>/', cliente, name='cliente'),
    path('exportar-alunos/', exportar_alunos, name='exportar_alunos'),
    path('exportar-clientes/', exportar_clientes, name='exportar_clientes'),
    path('exportar_ranking/', exportar_ranking, name='exportar_ranking'),
    path('exportar_ranking_semana/<int:semana>/', exportar_ranking_semana, name='exportar_ranking_semana'),
    path('exportar_ranking_semana_cla/<int:semana>/', exportar_ranking_semana_cla, name='exportar_ranking_semana_cla'),
    path('extrato/<int:aluno_id>/', exportar_excel_aluno, name='extrato'),
]