from django.urls import path
from .views import *

urlpatterns = [
    path('balanceamento', BalanceamentoView, name='balanceamento'),
    path('retencao', RetencaoView, name='retencao'),
    path('ranking', RankingView, name='ranking'),
]