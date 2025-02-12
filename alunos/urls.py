from django.urls import path, include
from .views import *

urlpatterns = [
    path('alunos/', alunos, name='alunos'),
    path('aluno/<int:aluno_id>/', aluno, name='aluno'),
    path('ranking/', ranking, name='ranking'),
    path('clas/', clas, name='clas'),
    path('cla/<int:cla_id>/', cla, name='cla'),
]