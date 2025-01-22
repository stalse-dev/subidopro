from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('atualizaPontosLimitesMesesEnvios', atualizaPontosLimitesMesesEnvios, name='atualizaPontosLimitesMesesEnvios'),
    path('calculoRetencaoClientes', calculoRetencaoClientes, name='calculoRetencaoClientes'),
    path('calculoRankingSemanaAluno', calculoRankingSemanaAluno, name='calculoRankingSemanaAluno'),
]