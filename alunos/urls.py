from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('alunos/', alunos, name='alunos'),
    path('aluno/<int:aluno_id>/', aluno, name='aluno'),
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
    path('exportar-aluno-pontuacoes/<int:aluno_id>/', exportar_aluno_pontuacoes, name='exportar_aluno_pontuacoes'),
    path('exportar_ranking/', exportar_ranking, name='exportar_ranking'),
    path('extrato/<int:aluno_id>/', extrato, name='extrato'),
]