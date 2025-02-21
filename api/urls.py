from django.urls import path, include
from .views import *

urlpatterns = [
    path('receber-dados/', receber_dados, name='receber_dados'),
    path('logsweb/', listar_logs, name='listar_logs'),
    path('detalhes-log/<int:log_id>/', detalhes_log, name='detalhes_log'),
]