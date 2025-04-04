from django.urls import path, include
from .views import *

urlpatterns = [
    path("alunos-semana/", AlunosPosicoesSemanaListView.as_view(), name="alunos-semana"),
    path("cla-semana/", ClansPosicoesSemanaListView.as_view(), name="cla-semana"),
    path("ranking-streamer/", AlunosPosicoesStremerListView.as_view(), name="ranking-streamer"),
    path('aluno/<int:id>/', AlunosDetailView.as_view(), name='aluno-detail'),
]
