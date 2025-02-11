import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Adicionar ao grupo "logs"
        await self.channel_layer.group_add("logs", self.channel_name)
        await self.accept()
        await self.send(json.dumps({"message": "WebSocket conectado!"}))

    async def disconnect(self, close_code):
        # Remover do grupo ao desconectar
        await self.channel_layer.group_discard("logs", self.channel_name)

    async def receive(self, text_data):
        print(f"Mensagem recebida: {text_data}")
        await self.send(json.dumps({"message": f"Recebido: {text_data}"}))

    async def log_message(self, event):
        """Função chamada quando um log é enviado para o grupo."""
        await self.send(text_data=json.dumps(event["message"]))
