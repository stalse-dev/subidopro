from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('alunos/', alunos, name='alunos'),
    path('aluno/<int:aluno_id>/', aluno, name='aluno'),
    path('balanceamento/', balanceamento, name='balanceamento'),
    path('retencao/', retencao, name='retencao'),
    path('ranking/', ranking, name='ranking'),
    path('clas/', clas, name='clas'),
    path('cla/<int:cla_id>/', cla, name='cla'),
    path('clientes/', clientes, name='clientes'),
    path('cliente/<int:cliente_id>/', cliente, name='cliente'),
]