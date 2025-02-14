from django.urls import path
from .views import *

urlpatterns = [
    path('teste', teste, name='teste'),
    path('calcula_balanceamento', calcula_balanceamento, name='calcula_balanceamento'),
    path('calculo_retencao', calculo_retencao, name='calculo_retencao'),
    path('calculoRankingSemanaAluno', calculoRankingSemanaAluno, name='calculoRankingSemanaAluno'),
]