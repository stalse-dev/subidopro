from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from api.models import Log

def registrar_log(acao, tabela, dados_anteriores=None, dados_novos=None, status='sucesso', erro=None):
    log = Log.objects.create(
        acao=acao,
        tabela=tabela,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        status=status,
        erro=erro
    )

    # # Enviar para WebSocket
    # channel_layer = get_channel_layer()
    # async_to_sync(channel_layer.group_send)(
    #     "logs",
    #     {
    #         "type": "log_message",  # Esse nome deve ser igual à função do consumer
    #         "message": {
    #             "acao": log.acao,
    #             "tabela": log.tabela,
    #             "status": log.status,
    #             "criado_em": log.criado_em.strftime("%Y-%m-%d %H:%M:%S"),
    #             "erro": log.erro,
    #         }
    #     }
    # )
