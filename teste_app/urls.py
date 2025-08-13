from django.urls import path
from .views import *

urlpatterns = [
    path('aprovacao_envio_valor_fixo/', TestViewEnvioAproveFixo, name='aprovacao_envio_valor_fixo'),
    path('aprovacao_envio_coproducao/', TestViewEnvioAproveCoproducao, name='aprovacao_envio_coproducao'),
    path('health_subidometro/', HealthSubidometroView, name='health_subidometro'),
    path('logs/', cloud_run_logs, name='logs'),
]