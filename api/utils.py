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
