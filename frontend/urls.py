from django.urls import path, include
from .views import *

urlpatterns = [
    path("alunos-semana/", AlunosPosicoesSemanaListView.as_view(), name="alunos-semana"),
    path("alunos-semana-sheet/", AlunosPosicoesSemanaSheetView.as_view(), name="alunos-semana-sheet"),
    path("cla-semana/", ClansPosicoesSemanaListView.as_view(), name="cla-semana"),
    path("cla-semana-sheet/", ClansPosicoesSemanSheetaListView.as_view(), name="ranking-streamer-sheet"),
    path("ranking-streamer/", AlunosPosicoesStremerListView.as_view(), name="ranking-streamer"),
    path("ranking-streamer-sheet/", AlunosRankingStreamerSheetView.as_view(), name="ranking-streamer-detail"),
    path('aluno/<int:id>/', AlunosDetailView.as_view(), name='aluno-detail'),
]
