from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('teste', teste, name='teste'),
    path('envios/<int:aluno_id>/<int:ano>/<int:mes>', envios_por_aluno_mes, name='envios'),
    path('atualizaPontosLimitesMesesEnvios', atualizaPontosLimitesMesesEnvios, name='atualizaPontosLimitesMesesEnvios'),
    path('calculoRetencaoClientes', calculoRetencaoClientes, name='calculoRetencaoClientes'),
    path('calculoRankingSemanaAluno', calculoRankingSemanaAluno, name='calculoRankingSemanaAluno'),
]