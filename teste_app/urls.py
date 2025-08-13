from django.urls import path
from .views import *

urlpatterns = [
    path('aprovacao_envio_valor_fixo/', TestViewEnvioAproveFixo, name='aprovacao_envio_valor_fixo'),
    path('health/', HealthSubidometroView, name='health_subidometro'),
]