from django.urls import path
from .views import *

urlpatterns = [
    path('calcula_balanceamento_func', calcula_balanceamento_func, name='calcula_balanceamento_func'),
    path('calculo_retencao_func', calculo_retencao_func, name='calculo_retencao_func'),
    path('calculo_ranking_func', calculo_ranking_func, name='calculo_ranking_func'),
    path('atualizar_subidometro_func', atualizar_subidometro_func, name='atualizar_subidometro_func'),
]