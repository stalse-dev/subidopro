from django.urls import path
from .views import *

urlpatterns = [
    path('teste', teste, name='teste'),
    path('balanceamento', calcula_balanceamento, name='balanceamento'),
    path('calculoRetencaoClientes', calculoRetencaoClientes, name='calculoRetencaoClientes'),
    path('calculoRankingSemanaAluno', calculoRankingSemanaAluno, name='calculoRankingSemanaAluno'),
]