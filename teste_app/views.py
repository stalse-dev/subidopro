from multiprocessing import context
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from subidometro.models import *
from .models import TestEnvioLog
from google.cloud import logging
from .utils import *
import decimal
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from auditlog.models import LogEntry
from subidometro.models import *

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

        # # Validação pontos do cliente
        # pontos_cliente = Aluno_contrato.objects.filter(cliente__id=1).first()
        # if not pontos_cliente:
        #     status_final = "erro"
        #     log_msgs.append("Cliente não encontrado para verificação de pontos.")
        # else:
        #     detalhes["pontos_cliente"] = pontos_cliente.pontos
        #     if pontos_cliente.pontos != 480.0:
        #         status_final = "erro"
        #         log_msgs.append(f"Pontos do cliente incorretos: {pontos_cliente.pontos}")
        #     else:
        #         log_msgs.append("Pontos do cliente corretos: 480")

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

def TestViewEnvioAproveCoproducao(request):
    rota = "aprovacao_envio_coproducao"
    teste = "aprovacao_envio_coproducao"
    payload = {
        "aluno": 3,
        "cliente": 1,
        "contrato": 54212,
        "campeonato": 14,
        "data": str(date.today()),
        "descricao": "Envio de documento XPTO",
        "valor": "20000.00",
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

        if float(pontos) != 200.0:
            status_final = "erro"
            log_msgs.append(f"Pontos incorretos: {pontos}")
        else:
            log_msgs.append("Pontos corretos: 200")

        if float(valor_calculado) != 2000.0:
            status_final = "erro"
            log_msgs.append(f"Valor calculado incorreto: {valor_calculado}")
        else:
            log_msgs.append("Valor calculado correto: 2000.0")

        # # Validação pontos do cliente
        # pontos_cliente = Aluno_contrato.objects.filter(cliente__id=1).first()
        # if not pontos_cliente:
        #     status_final = "erro"
        #     log_msgs.append("Cliente não encontrado para verificação de pontos.")
        # else:
        #     detalhes["pontos_cliente"] = pontos_cliente.pontos
        #     if pontos_cliente.pontos != 480.0:
        #         status_final = "erro"
        #         log_msgs.append(f"Pontos do cliente incorretos: {pontos_cliente.pontos}")
        #     else:
        #         log_msgs.append("Pontos do cliente corretos: 480")

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

@login_required
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
                "rota": ultimo_log.rota,
                "dados_inseridos": ultimo_log.json_entrada,
                "dados_saida": ultimo_log.json_saida,
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
                "dados_inseridos": None,
                "rota": resultado[test_key],
                "dados_saida": None,
                "status": "erro",
                "mensagem": "Nenhum log encontrado para este teste.",
                "detalhes": None,
                "criado_em": None,
            }
            status_geral = "erro"
    context = {
        "status_geral": status_geral,
        "testes": resultado
    }
    return render(request, "Health/health_subdimetro.html", context)
    # return JsonResponse({
    #     "status": status_geral,
    #     "resultado": resultado
    # })

@login_required
def log_list(request):
    logs = LogEntry.objects.select_related("content_type", "actor").order_by("-timestamp")

    # filtros básicos (opcionais)
    q = request.GET.get("q")
    if q:
        logs = logs.filter(
            Q(object_repr__icontains=q) |
            Q(changes__icontains=q)
        )

    paginator = Paginator(logs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    return render(request, "logs/logs.html", {
        "logs": page_obj,
        "page_obj": page_obj,
    })

def _resolve_related(obj):
    """
    Extrai IDs relacionados (aluno/cliente/contrato/envio) a partir do objeto logado.
    Retorna também os próprios objetos (para exibir nome/título no front).
    """
    data = {
        "aluno_id": None, "cliente_id": None, "contrato_id": None, "envio_id": None,
        "aluno_obj": None, "cliente_obj": None, "contrato_obj": None, "envio_obj": None,
    }

    if obj is None:
        return data

    # Aluno
    if isinstance(obj, Alunos):
        data["aluno_id"] = obj.id
        data["aluno_obj"] = obj

    # Cliente
    if isinstance(obj, Aluno_clientes):
        data["cliente_id"] = obj.id
        data["cliente_obj"] = obj
        if obj.aluno_id:
            data["aluno_id"] = obj.aluno_id
            data["aluno_obj"] = getattr(obj, "aluno", None)

    # Contrato
    if isinstance(obj, Aluno_clientes_contratos):
        data["contrato_id"] = obj.id
        data["contrato_obj"] = obj
        if obj.cliente_id:
            data["cliente_id"] = obj.cliente_id
            data["cliente_obj"] = getattr(obj, "cliente", None)
            # pega aluno via cliente
            if data["cliente_obj"] and data["cliente_obj"].aluno_id:
                data["aluno_id"] = data["cliente_obj"].aluno_id
                data["aluno_obj"] = getattr(data["cliente_obj"], "aluno", None)

    # Envio
    if isinstance(obj, Aluno_envios):
        data["envio_id"] = obj.id
        data["envio_obj"] = obj
        if obj.contrato_id:
            data["contrato_id"] = obj.contrato_id
            data["contrato_obj"] = getattr(obj, "contrato", None)
        if obj.cliente_id:
            data["cliente_id"] = obj.cliente_id
            data["cliente_obj"] = getattr(obj, "cliente", None)
        if obj.aluno_id:
            data["aluno_id"] = obj.aluno_id
            data["aluno_obj"] = getattr(obj, "aluno", None)

    return data

@login_required
def log_detail(request, pk):
    log = get_object_or_404(LogEntry, pk=pk)

    # tenta resolver o objeto logado
    alvo_obj = None
    if log.content_type and log.object_pk:
        try:
            model_class = log.content_type.model_class()
            alvo_obj = model_class.objects.filter(pk=log.object_pk).first()
        except Exception:
            alvo_obj = None

    # IDs/objetos relacionados
    related = _resolve_related(alvo_obj)

    # transforma changes em lista amigável
    changes = []
    if isinstance(log.changes_dict, dict):
        for field, values in log.changes_dict.items():
            old_val, new_val = None, None
            if isinstance(values, (list, tuple)) and len(values) == 2:
                old_val, new_val = values
            else:
                new_val = values
            changes.append({
                "field": field,
                "old": old_val,
                "new": new_val,
                "changed": (old_val != new_val),
            })

    return render(request, "logs/detalhes_log.html", {
        "log": log,
        "changes": changes,
        "related_ids": {
            "aluno_id": related["aluno_id"],
            "cliente_id": related["cliente_id"],
            "contrato_id": related["contrato_id"],
            "envio_id": related["envio_id"],
        },
        "alvo_obj": alvo_obj,
        "aluno_obj": related["aluno_obj"],
        "cliente_obj": related["cliente_obj"],
        "contrato_obj": related["contrato_obj"],
        "envio_obj": related["envio_obj"],
    })