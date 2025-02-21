from django.urls import path
from .views import *

urlpatterns = [
    path('calcula_balanceamento', calcula_balanceamento, name='calcula_balanceamento'),
    path('calculo_retencao', calculo_retencao, name='calculo_retencao'),
    path('calculo_ranking', calculo_ranking, name='calculo_ranking'),
    path('atualizar_subidometro', atualizar_subidometro, name='atualizar_subidometro'),
    path('teste', teste, name='teste'),
]