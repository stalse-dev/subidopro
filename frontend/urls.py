from django.urls import path, include
from .views import *

urlpatterns = [
    path("alunos-semana/", AlunosPosicoesSemanaListView.as_view(), name="alunos-semana"),
]
