from django.urls import path
from api.consumers import LogConsumer

websocket_urlpatterns = [
    path("ws/logs/", LogConsumer.as_asgi()),
]
