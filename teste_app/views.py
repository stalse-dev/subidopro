# teste_app/views.py
from urllib import response
from django.http import JsonResponse
from subidometro.models import *
from .models import TestEnvioLog
import requests
from .utils import *
from datetime import date
import decimal

def to_jsonable(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_jsonable(v) for v in obj]
    return obj

def TestViewEnvioAproveFixo(request):
    rota = "aprovacao_envio_valor_fixo"
    teste = "aprovacao_envio_valor_fixo"
    payload = {
        "aluno": 3,
        "cliente": 1,
        "contrato": 54211,
        "campeonato": 14,
        "data": str(date.today()),
        "descricao": "Envio de documento XPTO",
        "valor": "1000.00",
        "arquivo1": 'http://example.com/arquivo1.pdf',
        "data_cadastro": str(date.today()),
        "status": 0,
        "semana": 1
    }

    log_msgs = []
    detalhes = {}
    json_saida = {}
    status_final = "sucesso"

    try:
        # POST envio
        postEnvio, returnPost = TestPostEnvio(payload)
        if not postEnvio:
            status_final = "erro"
            log_msgs.append(f"Erro no POST: {returnPost}")
            json_saida["post"] = returnPost
            raise Exception("Falha ao criar envio")

        log_msgs.append(f"Envio criado com ID: {returnPost}")
        detalhes["envio_id"] = returnPost
        json_saida["post"] = returnPost

        # PATCH envio (aprovar)
        patchEnvio, returnPatch = TestPatchEnvio(returnPost, {"status": 3})
        if not patchEnvio:
            status_final = "erro"
            log_msgs.append(f"Erro no PATCH: {returnPatch}")
            json_saida["patch"] = returnPatch
            raise Exception("Falha ao aprovar envio")

        json_saida["patch"] = returnPatch

        # GET envio
        getEnvio, returnGet = TestGetEnvio(int(returnPost))
        if not getEnvio:
            status_final = "erro"
            log_msgs.append(f"Erro no GET: {returnGet}")
            json_saida["get"] = returnGet
            raise Exception("Falha ao buscar envio")

        json_saida["get"] = returnGet

        valor_calculado = returnGet.get('valor_calculado')
        pontos = returnGet.get('pontos')

        detalhes.update({
            "valor_calculado": valor_calculado,
            "pontos": pontos
        })

        if float(pontos) != 100.0:
            status_final = "erro"
            log_msgs.append(f"Pontos incorretos: {pontos}")
        else:
            log_msgs.append("Pontos corretos: 100")

        if float(valor_calculado) != 1000.0:
            status_final = "erro"
            log_msgs.append(f"Valor calculado incorreto: {valor_calculado}")
        else:
            log_msgs.append("Valor calculado correto: 1000.0")

        # Validação pontos do cliente
        pontos_cliente = Aluno_contrato.objects.filter(cliente__id=1).first()
        if not pontos_cliente:
            status_final = "erro"
            log_msgs.append("Cliente não encontrado para verificação de pontos.")
        else:
            detalhes["pontos_cliente"] = pontos_cliente.pontos
            if pontos_cliente.pontos != 480.0:
                status_final = "erro"
                log_msgs.append(f"Pontos do cliente incorretos: {pontos_cliente.pontos}")
            else:
                log_msgs.append("Pontos do cliente corretos: 480")

    except Exception as e:
        status_final = "erro"
        log_msgs.append(f"Exceção capturada: {str(e)}")

    TestEnvioLog.objects.create(
        rota=rota,
        json_entrada=to_jsonable(payload),
        json_saida=to_jsonable(json_saida),
        teste=teste,
        status=status_final,
        mensagem="\n".join(log_msgs),
        detalhes=to_jsonable(detalhes)
    )


    # Retorno API
    return JsonResponse({
        "status": status_final,
        "mensagem": "\n".join(log_msgs),
        "detalhes": detalhes
    })

def HealthSubidometroView(request):
    """
    Valida a saúde do sistema baseado nos últimos testes executados.
    """
    resultado = {}
    status_geral = "sucesso"

    for test_key, test_label in TestEnvioLog.TEST_CHOICES:
        ultimo_log = (
            TestEnvioLog.objects
            .filter(teste=test_key)
            .order_by('-criado_em')
            .first()
        )

        if ultimo_log:
            resultado[test_key] = {
                "nome_teste": test_label,
                "status": ultimo_log.status,
                "mensagem": ultimo_log.mensagem,
                "detalhes": ultimo_log.detalhes,
                "criado_em": ultimo_log.criado_em.strftime("%Y-%m-%d %H:%M:%S"),
            }
            if ultimo_log.status != "sucesso":
                status_geral = "erro"
        else:
            resultado[test_key] = {
                "nome_teste": test_label,
                "status": "erro",
                "mensagem": "Nenhum log encontrado para este teste.",
                "detalhes": None,
                "criado_em": None,
            }
            status_geral = "erro"

    return JsonResponse({
        "status_geral": status_geral,
        "testes": resultado
    })