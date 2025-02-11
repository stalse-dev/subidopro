from django.urls import path, include
from .views import *

urlpatterns = [
    path('receber-dados/', receber_dados, name='receber_dados'),
    path('logsweb/', listar_logs, name='listar_logs'),
    path('logsweb/carregar-mais/', carregar_mais_logs, name='carregar_mais_logs'),
]