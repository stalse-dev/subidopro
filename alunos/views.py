import json
from multiprocessing import context
from django.db.models import Value, CharField
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseForbidden
from subidometro.models import *
from subidometro.utils import *
from django.db.models.functions import TruncMonth, ExtractMonth, ExtractHour, ExtractDay, ExtractYear
from django.db.models import OuterRef, Subquery, F, Sum, Count, Avg, Exists
from django.contrib.auth.decorators import login_required
from datetime import date
from django.core.paginator import Paginator
import pandas as pd
import xlsxwriter
from django.utils import timezone 
from datetime import timedelta
from datetime import datetime
from django.views.decorators.cache import never_cache
import calendar
from calculadora_pontos.utils import ranking_streamer as ranking_streamer_campeonato
from collections import defaultdict, OrderedDict
from django.utils.dateformat import format as date_format

@never_cache
@login_required
def campeonatos(request):
    campeonatos = Campeonato.objects.order_by('-id')
    context = {
        'campeonatos': campeonatos,
    }
    return render(request, 'Campeonato/Campeonatos.html', context)

@login_required
def dashboard(request, campeonato_id):
    campeonato = Campeonato.objects.get(id=campeonato_id)

    maior_semana_obj = (
        Alunos_posicoes_semana.objects
        .filter(campeonato=campeonato)
        .order_by('-semana')
        .only('semana')
        .first()
    )
    semana = maior_semana_obj.semana if maior_semana_obj else 0

    alunos = ParticipacaoCampeonato.objects.filter(campeonato=campeonato)
    clas = Mentoria_cla.objects.filter(campeonato=campeonato).order_by('id')
    desafios = Desafios.objects.order_by('id')

    hoje = date.today()
    dias_ate_sabado = (5 - hoje.weekday()) % 7

    top_3_alunos = Alunos_posicoes_semana.objects.filter(
        campeonato=campeonato, semana=semana
    ).order_by('posicao')[:3]

    top_3_clas = Mentoria_cla_posicao_semana.objects.filter(
        campeonato=campeonato, semana=semana
    ).order_by('posicao')[:3]

    faturamento_total = (
        Aluno_envios.objects
        .filter(campeonato=campeonato, status=3)
        .aggregate(total=Sum('valor_calculado'))['total'] or 0
    )

    # -------------------------------
    # Dados para o gráfico (top 10 por semana)
    # -------------------------------
    semanas_disponiveis = (
        Alunos_posicoes_semana.objects
        .filter(campeonato=campeonato)
        .values_list('semana', flat=True)
        .distinct()
        .order_by('semana')
    )

    grafico_dados = []
    for sem in semanas_disponiveis:
        top10_semana = (
            Alunos_posicoes_semana.objects
            .filter(campeonato=campeonato, semana=sem)
            .order_by('-pontos_totais')[:3]
            .select_related('aluno')
        )

        grafico_dados.append({
            "semana": sem,
            "alunos": [
                {
                    "aluno_id": aps.aluno.id,
                    "nome": aps.aluno.nome_completo,
                    "pontos": float(aps.pontos_totais or 0)
                }
                for aps in top10_semana
            ]
        })

    context = {
        'campeonato': campeonato,
        'dias_ate_sabado': dias_ate_sabado,
        'alunos': alunos,
        'clas': clas,
        'desafios': desafios,
        'semana': semana,
        'top_3_alunos': top_3_alunos,
        'top_3_clas': top_3_clas,
        'faturamento_total': faturamento_total,
        'grafico_dados': grafico_dados
    }
    #return JsonResponse(grafico_dados, safe=False)
    return render(request, 'Dashboard/Dashboard.html', context)

@login_required
def alunos_campeonato(request, campeonato_id):
    campeonato = Campeonato.objects.get(id=campeonato_id)
    query = request.GET.get('q', '')

    alunos_list = Alunos.objects.filter(participacoes__campeonato=campeonato).order_by('id')

    if query:
        alunos_list = alunos_list.filter(
            Q(nome_completo__icontains=query) | 
            Q(apelido__icontains=query) | 
            Q(email__icontains=query)
        )

    paginator = Paginator(alunos_list, 20)
    page_number = request.GET.get('page')
    alunos_page = paginator.get_page(page_number)

    # Associa os níveis aos alunos
    niveis_dict = {
        nivel.id: nivel for nivel in Mentoria_lista_niveis.objects.all()
    }

    for aluno in alunos_page:
        aluno.nivel_obj = niveis_dict.get(aluno.nivel)

    context = {
        'campeonato': campeonato,
        'alunos': alunos_page,
        'q': query,
        'cont_alunos': alunos_list.count()
    }
    return render(request, 'Alunos/alunos_campeoanto.html', context)

@login_required
def clas_campeonato(request, campeonato_id):
    campeonato = Campeonato.objects.get(id=campeonato_id)
    maior_semana_obj = (
        Alunos_posicoes_semana.objects.filter(campeonato=campeonato)
        .order_by('-semana')
        .only('semana')
        .first()
    )

    semana = maior_semana_obj.semana if maior_semana_obj else 0
    query = request.GET.get('q', '')

    # Filtra todos os clãs relacionados ao campeonato
    clas_list = Mentoria_cla.objects.filter(campeonato=campeonato)

    if query:
        clas_list = clas_list.filter(
            Q(nome__icontains=query) |
            Q(sigla__icontains=query)
        )

    # Recupera as pontuações da semana
    posicoes = Mentoria_cla_posicao_semana.objects.filter(
        campeonato=campeonato,
        semana=semana
    )

    pontos_por_cla = {
        p.cla_id: p.pontos_totais
        for p in posicoes
    }

    ranking = sorted(pontos_por_cla.items(), key=lambda x: x[1], reverse=True)
    posicao_por_cla = {cla_id: idx + 1 for idx, (cla_id, _) in enumerate(ranking)}

    # Adiciona posição e pontos a cada clã da lista
    for cla in clas_list:
        cla.pontos_semana = pontos_por_cla.get(cla.id, 0)
        cla.posicao_semana = posicao_por_cla.get(cla.id, float('inf'))  # clãs sem posição vão para o final

    # Ordena manualmente pela posição
    clas_list = sorted(clas_list, key=lambda c: c.posicao_semana)

    # Pagina a lista já ordenada
    paginator = Paginator(clas_list, 20)
    page_number = request.GET.get('page')
    clas_page = paginator.get_page(page_number)

    context = {
        'campeonato': campeonato,
        'semana': semana,
        'clas': clas_page,
        'query': query
    }

    return render(request, 'Clas/Clas_Campeonato.html', context)

@login_required
def ranking_semana_campeonato(request, campeonato_id):
    campeonato = Campeonato.objects.get(id=campeonato_id)

    # Lista de semanas disponíveis
    semanas_disponiveis = Alunos_posicoes_semana.objects.filter(
        campeonato=campeonato
    ).values_list('semana', flat=True).distinct().order_by('-semana')

    # Semana vinda do filtro (GET)
    semana_param = request.GET.get('semana')
    if semana_param and semana_param.isdigit():
        semana_filtrada = int(semana_param)
    else:
        semana_filtrada = semanas_disponiveis.first()

    # Campo de busca
    q = request.GET.get('q', '').strip()

    # Base da query
    semana_rank_list = Alunos_posicoes_semana.objects.filter(
        semana=semana_filtrada,
        campeonato=campeonato
    )

    # Aplica filtro de busca se houver
    if q:
        semana_rank_list = semana_rank_list.filter(
            Q(aluno__nome_completo__icontains=q) |
            Q(aluno__email__icontains=q) |
            Q(aluno__id__iexact=q)
        )

    # Contagem de todos os alunos
    cont_rank = semana_rank_list.count()

    semana_rank_list = semana_rank_list.order_by('posicao')

    # Paginação
    paginator = Paginator(semana_rank_list, 20)
    page_number = request.GET.get('page')
    semana_rank = paginator.get_page(page_number)

    ultima_att = semana_rank_list.first().data if semana_rank_list.exists() else None
    
    


    context = {
        "campeonato": campeonato,
        "alunos": semana_rank,
        "cont_rank": cont_rank,
        "semana": semana_filtrada,
        "semanas_disponiveis": semanas_disponiveis,
        "q": q,
        "ultima_att": ultima_att,
    }

    return render(request, "Ranking/ranking_semana_campeonato.html", context)

@login_required
def ranking_campeonato(request, campeonato_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Você não tem permissão para acessar esta página.")
    
    campeonato = Campeonato.objects.get(id=campeonato_id)
    
    alunos_list  = ranking_streamer_campeonato(campeonato)

    q = request.GET.get('q', '').strip()

    if q:
        if q.isdigit():
            alunos_list = alunos_list.filter(Q(id=int(q)) | Q(nome_completo__icontains=q))
        else:
            alunos_list = alunos_list.filter(Q(nome_completo__icontains=q))

    # Contagem de todos os alunos
    cont_rank = alunos_list.count()

    paginator = Paginator(alunos_list, 50)
    page_number = request.GET.get('page')
    semana_rank = paginator.get_page(page_number)

    context = {
        "campeonato": campeonato,
        "alunos": semana_rank,
        "q": q,
        "cont_rank": cont_rank,
    }
    return render(request, "Ranking/ranking_campeonato.html", context) 

@login_required
def aluno_dashboard(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    envios = Aluno_envios.objects.filter(aluno_id=aluno_id)
    clientes = Aluno_clientes.objects.filter(aluno_id=aluno_id)
    contratos = Aluno_clientes_contratos.objects.filter(cliente__aluno_id=aluno_id)

    mes_mais_ganhou = (
        Aluno_envios.objects
        .filter(aluno=aluno, status=3, semana__gt=0)
        .annotate(mes=TruncMonth('data'))
        .values('mes')
        .annotate(total_mes=Sum('valor_calculado'))
        .order_by('-total_mes')
        .first()
    )

    total_valores_envios = Aluno_envios.objects.filter(aluno=aluno, status=3).aggregate(total=Sum('valor_calculado'))['total'] or 0
    total_valor_camp = Aluno_camp_faturamento_anterior.objects.filter(aluno=aluno).aggregate(total=Sum('valor'))['total'] or 0
    
    soma_de_todos_valores = float(total_valores_envios) + float(total_valor_camp)

    # Campeonatos atuais
    campeonatos_atuais = Campeonato.objects.filter(
        participacoes__aluno_id=aluno_id
    ).annotate(
        tipo=Value("Atual", output_field=CharField())
    ).values("identificacao", "data_inicio", "data_fim")

    campeonatos_atuais = list(campeonatos_atuais)

    campeonatos_antigos = Aluno_camp_faturamento_anterior.objects.filter(aluno_id=aluno_id).first()

    if campeonatos_antigos:
        aluno_campeonato = {
            "identificacao": "Campeonatos antigos",
            "data_inicio": "N/A",
            "data_fim": "N/A",
        }
        campeonatos_atuais.append(aluno_campeonato)


    # --- ENVIOS ---
    total_envios = envios.count()
    total_aprovados = envios.filter(status=3).count()
    total_reprovados = envios.filter(status=2).count()

    envios_por_mes = (
        envios
        .exclude(data__isnull=True)
        .annotate(
            mes=ExtractMonth("data"),
            ano=ExtractYear("data")
        )
        .values("mes", "ano")
        .annotate(total=Count("id"))
        .order_by("ano", "mes")
    )
    envios_por_mes = [
        {**item, "mes_ano": f"{item['mes']:02d}/{item['ano']}"}
        for item in envios_por_mes
    ]

    dia_mais_comum = (
        envios
        .exclude(data_cadastro__isnull=True)
        .annotate(dia=ExtractDay("data_cadastro"))
        .values("dia")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )
    if dia_mais_comum:
        dia_mais_comum["dia_formatado"] = f"{dia_mais_comum['dia']:02d}"

    horario_mais_comum = (
        envios
        .exclude(data_cadastro__isnull=True)
        .annotate(hora=ExtractHour("data_cadastro"))
        .values("hora")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )
    if horario_mais_comum:
        horario_mais_comum["hora_formatada"] = f"{horario_mais_comum['hora']:02d}:00"

    # --- CLIENTES ---
    total_clientes = clientes.count()
    clientes_reprovados = clientes.filter(status=2).count()

    # --- CONTRATOS ---
    total_contratos = contratos.count()
    contratos_reprovados = contratos.filter(status=2).count()

    contratos_por_tipo = (
        contratos
        .values("tipo_contrato")
        .annotate(total=Count("id"))
        .order_by("tipo_contrato")
    )

    # --- RETENÇÃO ---
    retencao_qs = Alunos_clientes_pontos_meses_retencao.objects.filter(aluno_id=aluno_id)

    # Total de clientes com retenção (distintos)
    total_clientes_retidos = retencao_qs.values("cliente").distinct().count()

    # Clientes retidos por mês/ano
    clientes_retidos_por_mes = (
        retencao_qs
        .annotate(
            mes=ExtractMonth("data"),
            ano=ExtractYear("data")
        )
        .values("mes", "ano")
        .annotate(clientes_retidos=Count("cliente", distinct=True))
        .order_by("ano", "mes")
    )   

    # Formata mes/ano no retorno
    clientes_retidos_por_mes = [
        {
            **item,
            "mes_ano": f"{item['mes']:02d}/{item['ano']}"
        }
        for item in clientes_retidos_por_mes
    ]

    #Clientes Novos Adiquiridos no Cameponato do Alunos
    novos_clientes = Aluno_contrato.objects.filter(aluno_id=aluno_id, campeonato=aluno.campeonato, status=3).count()

    mes_mais_ganhou = (
        Aluno_envios.objects
        .filter(aluno=aluno, status=3, semana__gt=0)
        .annotate(mes=TruncMonth('data'))
        .values('mes')
        .annotate(total_mes=Sum('valor_calculado'))
        .order_by('-total_mes')
        .first()
    )

    total_valores_envios = Aluno_envios.objects.filter(aluno=aluno, status=3).aggregate(total=Sum('valor_calculado'))['total'] or 0
    total_valor_camp = Aluno_camp_faturamento_anterior.objects.filter(aluno=aluno).aggregate(total=Sum('valor'))['total'] or 0

    soma_de_todos_valores = float(total_valores_envios) + float(total_valor_camp)


    context = {
        "aluno": aluno,
        "total_envios": total_envios,
        "total_aprovados": total_aprovados,
        "total_reprovados": total_reprovados,
        "envios_por_mes": list(envios_por_mes),
        "dia_mais_comum": dia_mais_comum,
        "horario_mais_comum": horario_mais_comum,

        "mes_mais_ganhou": {
            "mes": mes_mais_ganhou["mes"].strftime("%Y-%m") if mes_mais_ganhou else None,
            "total_mes": float(mes_mais_ganhou["total_mes"]) if mes_mais_ganhou else 0
        },
        "soma_de_todos_valores": float(soma_de_todos_valores),

        # Campeonatos Atuais
        "campeonatos_participantes": campeonatos_atuais,

        # Clientes
        "total_clientes": total_clientes,
        "clientes_reprovados": clientes_reprovados,
        # Novos Clientes
        "novos_clientes": novos_clientes,

        # Contratos
        "total_contratos": total_contratos,
        "contratos_reprovados": contratos_reprovados,
        "contratos_por_tipo": list(contratos_por_tipo),

        # Retenção
        "total_clientes_retidos": total_clientes_retidos,
        "clientes_retidos_por_mes": list(clientes_retidos_por_mes),
        "mes_mais_ganhou": {
            "mes": mes_mais_ganhou["mes"].strftime("%Y-%m") if mes_mais_ganhou else None,
            "total_mes": float(mes_mais_ganhou["total_mes"]) if mes_mais_ganhou else 0
        },
        "soma_de_todos_valores": float(soma_de_todos_valores)
    }
    return render(request, "Alunos/aluno_dashboard.html", context)

    return JsonResponse({
        # Envios
        "total_envios": total_envios,
        "total_aprovados": total_aprovados,
        "total_reprovados": total_reprovados,
        "envios_por_mes": list(envios_por_mes),
        "dia_mais_comum": dia_mais_comum,
        "horario_mais_comum": horario_mais_comum,

        # Campeonatos Atuais
        "campeonatos_participantes": campeonatos_atuais,

        # Clientes
        "total_clientes": total_clientes,
        "clientes_reprovados": clientes_reprovados,
        # Novos Clientes
        "novos_clientes": novos_clientes,

        # Contratos
        "total_contratos": total_contratos,
        "contratos_reprovados": contratos_reprovados,
        "contratos_por_tipo": list(contratos_por_tipo),

        # Retenção
        "total_clientes_retidos": total_clientes_retidos,
        "clientes_retidos_por_mes": list(clientes_retidos_por_mes),
    }, safe=False)

@login_required
def faturamento_aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    # Filtra apenas envios aprovados com data
    envios = Aluno_envios.objects.filter(
        aluno=aluno,
        data__isnull=False,
        status=3
    )

    if not envios.exists():
        context = {
            "aluno": aluno,
            "faturamento_mensal": [],
            "faturamento_total": 0,
            "ticket_medio_geral": 0,
            "crescimento_percentual": 0,
            "mes_maior_faturamento": "N/D",
            "mes_menor_faturamento": "N/D",
            "ultimo_mes": None,
            "ranking_campeonatos": [],
        }
        return render(request, "Alunos/faturamento_aluno.html", context)

    mensal = envios.annotate(
        mes=TruncMonth('data')
    ).values('mes').annotate(
        faturamento=Sum(Coalesce('valor_calculado', 'valor')),
        total_envios=Count('id'),
        ticket_medio=Avg(Coalesce('valor_calculado', 'valor')),
    ).order_by('mes')

    dados_grafico = []
    faturamento_total = 0
    maior_valor = 0
    menor_valor = None
    ultimo_mes = None
    crescimento_percentual = 0
    faturamentos_mes = []

    for i, item in enumerate(mensal):
        mes_nome = item["mes"].strftime("%b/%Y")
        faturamento = float(item["faturamento"] or 0)
        faturamentos_mes.append(faturamento)
        dados_grafico.append({
            "mes": mes_nome,
            "faturamento": faturamento,
            "envios": item["total_envios"],
            "ticket_medio": float(item["ticket_medio"] or 0),
        })

        faturamento_total += faturamento

        if faturamento > maior_valor:
            maior_valor = faturamento
            mes_maior = mes_nome

        if menor_valor is None or faturamento < menor_valor:
            menor_valor = faturamento
            mes_menor = mes_nome

        ultimo_mes = mes_nome

    if len(faturamentos_mes) >= 2:
        penultimo = faturamentos_mes[-2]
        ultimo = faturamentos_mes[-1]
        if penultimo > 0:
            crescimento_percentual = round(((ultimo - penultimo) / penultimo) * 100, 2)

    ticket_medio_geral = envios.aggregate(
        media=Avg(Coalesce('valor_calculado', 'valor'))
    )['media'] or 0

    # Faturamento por campeonato
    campeonatos = envios.values("campeonato__identificacao").annotate(
        faturamento=Sum(Coalesce('valor_calculado', 'valor'))
    ).order_by("-faturamento")

    total_valor_camp = Aluno_camp_faturamento_anterior.objects.filter(aluno=aluno).aggregate(total=Sum('valor'))['total'] or 0

    ranking_campeonatos = [
        {
            "campeonato": item["campeonato__identificacao"] or "Sem campeonato",
            "faturamento": float(item["faturamento"] or 0)
        }
        for item in campeonatos
    ]

    ranking_campeonatos.append({
        "campeonato": "Campeonatos Anteriores",
        "faturamento": float(total_valor_camp)
    })

    faturamento_total = round(faturamento_total + float(total_valor_camp), 2)

    # Adiciona os novos dados ao context
    context = {
        "aluno": aluno,
        "faturamento_mensal": dados_grafico,
        "faturamento_total": round(faturamento_total, 2),
        "ticket_medio_geral": round(ticket_medio_geral, 2),
        "crescimento_percentual": crescimento_percentual,
        "mes_maior_faturamento": mes_maior,
        "mes_menor_faturamento": mes_menor,
        "ultimo_mes": ultimo_mes,
        "ranking_campeonatos": ranking_campeonatos,
    }

    return render(request, "Alunos/faturamento_aluno.html", context)

def AlunoEnviosPorCampeonatoSerializer(envios):
    agrupado = defaultdict(lambda: defaultdict(lambda: {
        "infos": {"data": "", "valor_total": "R$ 0,00", "pontos_total": "0"},
        "envios": []
    }))
    
    resumo = defaultdict(lambda: defaultdict(lambda: {
        "valor_total": 0.0,
        "pontos_total": 0
    }))

    for envio in envios:
        if not envio.data:
            continue

        campeonato_id = envio.campeonato.id if envio.campeonato else None
        campeonato_nome = envio.campeonato.identificacao if envio.campeonato else "Sem campeonato"

        mes_ano = envio.data.strftime('%Y-%m')
        nome_mes = envio.data.strftime('%B').upper()
        data_formatada = envio.data.strftime('%d/%m/%Y')
        data_cadastro_formatada = envio.data_cadastro.strftime('%d/%m/%Y') if envio.data_cadastro else ""

        item = {
            "id": envio.id,
            "data_criacao": data_cadastro_formatada,
            "data": data_formatada,
            "descricao": (envio.descricao or "")[:147] + "..." if envio.descricao and len(envio.descricao) > 150 else (envio.descricao or ""),
            "cliente": (envio.cliente.titulo or "")[:147] + "..." if envio.cliente and envio.cliente.titulo and len(envio.cliente.titulo) > 150 else (envio.cliente.titulo or ""),
            "valor": f"R$ {float(envio.valor):.2f}",
            "pontos_efetivos": str(int(envio.pontos)),
            "pontos_preenchidos": str(int(envio.pontos_previsto or envio.pontos)),
            "arquivo": str(envio.arquivo1 or ""),
            "status": envio.status,
            "status_motivo": envio.status_motivo or "",
            "semana": envio.semana
        }

        agrupado[campeonato_nome][mes_ano]["envios"].append(item)
        agrupado[campeonato_nome][mes_ano]["infos"]["data"] = f"{nome_mes} {envio.data.year}"

        if envio.status == 3:
            resumo[campeonato_nome][mes_ano]["valor_total"] += float(envio.valor)
            resumo[campeonato_nome][mes_ano]["pontos_total"] += int(envio.pontos)
            resumo[campeonato_nome][mes_ano]["pontos_total"] = min(resumo[campeonato_nome][mes_ano]["pontos_total"], 3000)

    # Formatando os totais para string
    for campeonato, meses in resumo.items():
        for mes_ano, valores in meses.items():
            agrupado[campeonato][mes_ano]["infos"]["valor_total"] = f"R$ {valores['valor_total']:,.2f}".replace(",", ".")
            agrupado[campeonato][mes_ano]["infos"]["pontos_total"] = str(valores["pontos_total"])

    # Ordenar por campeonato e por mês (desc)
    resultado_final = OrderedDict()
    for campeonato in sorted(agrupado.keys(), reverse=True):
        resultado_final[campeonato] = OrderedDict()
        meses_ordenados = sorted(agrupado[campeonato].keys(), reverse=True)
        for mes in meses_ordenados:
            resultado_final[campeonato][mes] = agrupado[campeonato][mes]

    return resultado_final

@login_required
def pontos_recebimento_aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    envios = Aluno_envios.objects.filter(aluno_id=aluno_id).select_related('campeonato')
    resultado = AlunoEnviosPorCampeonatoSerializer(envios)

    context = {
        "aluno": aluno,
        "envios": resultado
    }

    return render(request, "Alunos/pontos_recebimento.html", context)

@login_required
def pontos_cliente_aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    contratos = (
        Aluno_contrato.objects
        .filter(aluno_id=aluno_id, pontos__gt=0, status=3)
        .select_related('cliente', 'campeonato')
        .order_by('-campeonato__data_inicio', '-data_cadastro')
    )

    campeonatos_dict = {}

    for contrato in contratos:
        cliente = contrato.cliente
        campeonato = contrato.campeonato

        # Primeiro envio aprovado
        primeiro_envio = (
            Aluno_envios.objects
            .filter(aluno_id=aluno_id, cliente=cliente, status=3)
            .order_by('data')
            .first()
        )

        key = (
            f"Campeonato {campeonato.id}"
            if campeonato else
            "Sem campeonato"
        )

        if key not in campeonatos_dict:
            campeonatos_dict[key] = {
                "campeonato_id": campeonato.id if campeonato else None,
                "campeonato_identificacao": campeonato.identificacao if campeonato else None,
                "campeonato_data_inicio": campeonato.data_inicio if campeonato else None,
                "total_pontos": 0,
                "clientes": []
            }

        campeonatos_dict[key]["clientes"].append({
            "cliente_id": cliente.id,
            "cliente_titulo": cliente.titulo,
            "cliente_data_criacao": cliente.data_criacao,
            "cliente_documento": cliente.documento,
            "pontos": float(contrato.pontos),
            "contrato_data": contrato.data,
            "primeiro_envio_aprovado": primeiro_envio.data if primeiro_envio else None,
        })

        campeonatos_dict[key]["total_pontos"] += float(contrato.pontos)

    # Ordenar por data_inicio do campeonato (mais recente primeiro)
    campeonatos_ordenados = dict(
        sorted(
            campeonatos_dict.items(),
            key=lambda item: item[1]["campeonato_data_inicio"] or "1900-01-01",
            reverse=True
        )
    )

    #return JsonResponse(campeonatos_ordenados)

    context = {
        "aluno": aluno,
        "clientes": campeonatos_ordenados
    }

    return render(request, "Alunos/pontos_cliente.html", context)

@login_required
def pontos_desafio_aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    desafios = (
        Aluno_desafio.objects
        .filter(aluno_id=aluno_id)
        .select_related('campeonato', 'desafio')
        .order_by('-campeonato__data_inicio', '-data')
    )

    campeonatos_dict = {}

    for desafio in desafios:
        campeonato = desafio.campeonato
        desafio_info = desafio.desafio

        key = (
            f"Campeonato {campeonato.id}"
            if campeonato else
            "Sem campeonato"
        )

        if key not in campeonatos_dict:
            campeonatos_dict[key] = {
                "campeonato_id": campeonato.id if campeonato else None,
                "campeonato_identificacao": campeonato.identificacao if campeonato else None,
                "campeonato_data_inicio": campeonato.data_inicio if campeonato else None,
                "total_pontos": 0,
                "desafios": []
            }

        campeonatos_dict[key]["desafios"].append({
            "desafio_id": desafio_info.id if desafio_info else None,
            "desafio_titulo": desafio_info.titulo if desafio_info else None,
            "desafio_descricao": desafio_info.descricao if desafio_info else None,
            "descricao_execucao": desafio.descricao,
            "texto_execucao": desafio.texto,
            "data": desafio.data,
            "pontos": float(desafio.pontos),
            "pontos_previsto": float(desafio.pontos_previsto or desafio.pontos),
            "status": desafio.status,
            "status_motivo": desafio.status_motivo,
            "status_comentario": desafio.status_comentario,
            "semana": desafio.semana,
            "tipo": desafio.tipo
        })

        campeonatos_dict[key]["total_pontos"] += float(desafio.pontos)

    # Ordenar por data de início do campeonato (mais recente primeiro)
    campeonatos_ordenados = dict(
        sorted(
            campeonatos_dict.items(),
            key=lambda item: item[1]["campeonato_data_inicio"] or "1900-01-01",
            reverse=True
        )
    )

    context = {
        "aluno": aluno,
        "campeonatos": campeonatos_ordenados
    }

    #return JsonResponse(campeonatos_ordenados)
    return render(request, "Alunos/pontos_desafio.html", context)
    
@login_required
def pontos_certificacao_aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    certificacoes = (
        Aluno_certificacao.objects
        .filter(aluno_id=aluno_id, tipo=3)
        .select_related('campeonato')
        .order_by('-campeonato__data_inicio', '-data')
    )

    campeonatos_dict = {}

    for certificacao in certificacoes:
        campeonato = certificacao.campeonato

        key = f"Campeonato {campeonato.id}" if campeonato else "Sem campeonato"

        if key not in campeonatos_dict:
            campeonatos_dict[key] = {
                "campeonato_id": campeonato.id if campeonato else None,
                "campeonato_identificacao": campeonato.identificacao if campeonato else None,
                "campeonato_data_inicio": campeonato.data_inicio if campeonato else None,
                "total_pontos": 0,
                "certificacoes": []
            }

        campeonatos_dict[key]["certificacoes"].append({
            "certificacao_id": certificacao.id,
            "certificacao_titulo": certificacao.descricao,  # ajuste para campo certo
            "descricao_execucao": certificacao.descricao,
            "data": certificacao.data,
            "pontos": float(certificacao.pontos),
            "pontos_previsto": float(certificacao.pontos_previsto or certificacao.pontos),
            "status": certificacao.status,
            "status_motivo": certificacao.status_motivo,
            "status_comentario": certificacao.status_comentario,
            "semana": certificacao.semana,
            "tipo": certificacao.tipo
        })

        campeonatos_dict[key]["total_pontos"] += float(certificacao.pontos)

    campeonatos_ordenados = dict(
        sorted(
            campeonatos_dict.items(),
            key=lambda item: item[1]["campeonato_data_inicio"] or "1900-01-01",
            reverse=True
        )
    )

    context = {"aluno": aluno, "campeonatos": campeonatos_ordenados}

    return render(request, "Alunos/pontos_certificacao.html", context)
@login_required
def pontos_manuais_aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    manuais = (
        Aluno_certificacao.objects
        .filter(aluno_id=aluno_id, tipo=5)
        .select_related('campeonato')
        .order_by('-campeonato__data_inicio', '-data')
    )

    campeonatos_dict = {}

    for certificacao in manuais:
        campeonato = certificacao.campeonato

        key = f"Campeonato {campeonato.id}" if campeonato else "Sem campeonato"

        if key not in campeonatos_dict:
            campeonatos_dict[key] = {
                "campeonato_id": campeonato.id if campeonato else None,
                "campeonato_identificacao": campeonato.identificacao if campeonato else None,
                "campeonato_data_inicio": campeonato.data_inicio if campeonato else None,
                "total_pontos": 0,
                "certificacoes": []
            }

        campeonatos_dict[key]["certificacoes"].append({
            "certificacao_id": certificacao.id,
            "certificacao_titulo": certificacao.descricao,  # ajuste para campo certo
            "descricao_execucao": certificacao.descricao,
            "data": certificacao.data,
            "pontos": float(certificacao.pontos),
            "pontos_previsto": float(certificacao.pontos_previsto or certificacao.pontos),
            "status": certificacao.status,
            "status_motivo": certificacao.status_motivo,
            "status_comentario": certificacao.status_comentario,
            "semana": certificacao.semana,
            "tipo": certificacao.tipo
        })

        campeonatos_dict[key]["total_pontos"] += float(certificacao.pontos)

    campeonatos_ordenados = dict(
        sorted(
            campeonatos_dict.items(),
            key=lambda item: item[1]["campeonato_data_inicio"] or "1900-01-01",
            reverse=True
        )
    )

    #return JsonResponse(campeonatos_ordenados)
    context = {"aluno": aluno, "campeonatos": campeonatos_ordenados}
    return render(request, "Alunos/pontos_manuais.html", context)

@login_required
def pontos_retencao_aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)

    # Busca todas as retenções do aluno com cliente e campeonato
    retencoes = (
        Alunos_clientes_pontos_meses_retencao.objects
        .filter(aluno_id=aluno_id)
        .select_related('campeonato', 'cliente')
        .order_by('campeonato__data_inicio', 'cliente__id', 'data')
    )

    campeonatos_dict = {}
    
    for retencao in retencoes:
        campeonato = retencao.campeonato
        cliente = retencao.cliente
        
        key = f"Campeonato {campeonato.id}" if campeonato else "Sem campeonato"
        
        # Se não existe campeonato no dict, cria
        if key not in campeonatos_dict:
            campeonatos_dict[key] = {
                "campeonato_id": campeonato.id if campeonato else None,
                "campeonato_identificacao": campeonato.identificacao if campeonato else None,
                "campeonato_data_inicio": campeonato.data_inicio if campeonato else None,
                "total_pontos": 0,
                "clientes": []
            }
        
        # Procura cliente no campeonato
        cliente_entry = next((c for c in campeonatos_dict[key]["clientes"] if c["cliente_id"] == cliente.id), None)
        
        if not cliente_entry:
            cliente_entry = {
                "cliente_sequencial": len(campeonatos_dict[key]["clientes"]) + 1,
                "cliente_id": cliente.id,
                "cliente_titulo": cliente.titulo,
                "total_pontos_cliente": 0,
                "retencoes": []
            }
            campeonatos_dict[key]["clientes"].append(cliente_entry)
        
        # Adiciona retenção
        cliente_entry["retencoes"].append({
            "retencao_id": retencao.id,
            "data": retencao.data,
            "pontos": float(retencao.pontos or 0),
            "qtd_envios": retencao.qtd_envios,
            "ids_envios": retencao.ids_envios,
            "semana": retencao.semana
        })

        # Soma pontos
        cliente_entry["total_pontos_cliente"] += float(retencao.pontos or 0)
        campeonatos_dict[key]["total_pontos"] += float(retencao.pontos or 0)

    # Ordena campeonatos por data
    campeonatos_ordenados = dict(
        sorted(
            campeonatos_dict.items(),
            key=lambda item: item[1]["campeonato_data_inicio"] or "1900-01-01",
            reverse=True
        )
    )

    context = {"aluno": aluno, "campeonatos": campeonatos_ordenados}
    #return JsonResponse(campeonatos_ordenados)
    return render(request, "Alunos/pontos_retencao.html", context)

@login_required
def pontos_cliente(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)

    contratos = (
        Aluno_clientes_contratos.objects
        .filter(cliente__aluno_id=aluno_id)
        .select_related('cliente')
        .order_by('-data_criacao')
    )

    print(f"Contratos encontrados: {contratos.count()}")

    clientes_dict = defaultdict(lambda: {
        "cliente_id": None,
        "cliente_titulo": None,
        "cliente_documento": None,
        "cliente_data_criacao": None,
        "contratos": []
    })

    for contrato in contratos:
        cliente = contrato.cliente

        if clientes_dict[cliente.id]["cliente_id"] is None:
            clientes_dict[cliente.id].update({
                "cliente_id": cliente.id,
                "cliente_titulo": cliente.titulo,
                "cliente_documento": cliente.documento,
                "cliente_data_criacao": cliente.data_criacao
            })

        envios = list(
            Aluno_envios.objects
            .filter(aluno_id=aluno_id, cliente=cliente, status=3)
            .order_by('data')
            .values("id", "data", "status", "pontos")
        )
        print(f"Envios para cliente {cliente.id}: {len(envios)}")

        clientes_dict[cliente.id]["contratos"].append({
            "contrato_id": contrato.id,
            "contrato_data": contrato.data_criacao,
            "pontos": float(getattr(contrato, 'pontos', 0)),
            "envios": envios
        })

    resultado = sorted(
        clientes_dict.values(),
        key=lambda x: x["cliente_data_criacao"] or "1900-01-01",
        reverse=True
    )

    context = {"aluno": aluno, "clientes": resultado}
    return render(request, "Alunos/pontos_cliente_aluno.html", context)

@login_required
def alunos(request):
    query = request.GET.get('q', '')

    alunos_list = Alunos.objects.all().order_by('id')

    if query:
        alunos_list = alunos_list.filter(
            Q(nome_completo__icontains=query) | 
            Q(apelido__icontains=query) | 
            Q(email__icontains=query)
        )

    paginator = Paginator(alunos_list, 50)
    page_number = request.GET.get('page')
    alunos_page = paginator.get_page(page_number)

    context = {
        'alunos': alunos_page,
        'q': query,
        'cont_alunos': alunos_list.count()
    }
    return render(request, 'Alunos/alunos.html', context)

@login_required
def clientes(request):
    query = request.GET.get('q', '')

    clientes_list = Aluno_clientes.objects.all().order_by('id')

    if query:
        clientes_list = clientes_list.filter(
            Q(titulo__icontains=query) | 
            Q(documento__icontains=query)
        )

    paginator = Paginator(clientes_list, 50)
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)

    cont_clientes = clientes_list.count()

    context = {
        'clientes': clientes,
        'q': query,
        'cont_clientes': cont_clientes
    }
    return render(request, 'Clientes/clientes.html', context)

@login_required
def cliente(request, cliente_id):
    cliente = Aluno_clientes.objects.get(id=cliente_id)
    ano_atual = timezone.now().year

    # Lista dos meses para exibição no template
    meses = [calendar.month_abbr[i].capitalize() for i in range(1, 13)]
    numeros_meses = list(range(1, 13))

    # Agregando pontos de retenção por mês
    retencao_mensal = (
        Alunos_clientes_pontos_meses_retencao.objects
        .filter(cliente=cliente, envio__data__year=ano_atual)
        .annotate(mes=ExtractMonth('envio__data'))
        .values('mes')
        .annotate(total_pontos=Sum('pontos'))
        .order_by('mes')
    )

    meses_filtrados = range(3, 9)
    retencao_por_mes = {i: 0 for i in meses_filtrados}

    for item in retencao_mensal:
        mes = item['mes']
        if mes in retencao_por_mes:
            retencao_por_mes[mes] = float(item['total_pontos'])

    lista_pontos_mes = [retencao_por_mes[i] for i in meses_filtrados]
    meses = [calendar.month_abbr[i].capitalize() for i in meses_filtrados]
    numeros_meses = list(meses_filtrados)


    cliente_pontos = Aluno_contrato.objects.filter(cliente=cliente).first()
    contratos = Aluno_clientes_contratos.objects.filter(cliente=cliente).order_by('-data_contrato')
    recebimentos = Aluno_envios.objects.filter(cliente=cliente).order_by('-data')
    pontos_retencao = Alunos_clientes_pontos_meses_retencao.objects.filter(cliente=cliente).order_by('-data')

    context = {
        'cliente': cliente,
        'contratos': contratos,
        'recebimentos': recebimentos,
        'cliente_pontos': cliente_pontos,
        'numeros_meses': numeros_meses,
        'meses': meses,
        'lista_pontos_mes': lista_pontos_mes,
        'pontos_retencao': pontos_retencao,
    }
    return render(request, 'Clientes/cliente.html', context)






@login_required
def exportar_excel_aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato, semana = calcular_semana_vigente()

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=aluno_pontuacoes_{aluno.id}_subidopro.xlsx'

    workbook = xlsxwriter.Workbook(response, {'in_memory': True})

    # Função auxiliar para criar aba com dados
    def adicionar_aba(nome_aba, queryset, campos):
        worksheet = workbook.add_worksheet(nome_aba[:31])  # nome da aba com no máximo 31 caracteres
        header_format = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        
        # Cabeçalhos
        for col, campo in enumerate(campos):
            worksheet.write(0, col, campo, header_format)

        # Dados
        for row, item in enumerate(queryset, start=1):
            for col, campo in enumerate(campos):
                valor = getattr(item, campo)
                worksheet.write(row, col, str(valor))

    # Páginas para cada queryset
    adicionar_aba("Recebimentos", 
                  Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_cadastro'),
                  ['id', 'cliente', 'contrato', 'data', 'data_cadastro', 'valor', 'pontos', 'status', 'status_motivo', 'status_comentario', 'semana'])

    adicionar_aba("Desafios", 
                  Aluno_desafio.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_cadastro'),
                  ['id', 'data_cadastro', 'pontos', 'desafio', 'status', 'status_motivo', 'status_comentario', 'semana'])

    adicionar_aba("Certificações", 
                  Aluno_certificacao.objects.filter(aluno=aluno, campeonato=campeonato, tipo=3).order_by('-data_cadastro'),
                  ['id', 'data_cadastro', 'pontos', 'descricao'])

    adicionar_aba("Contratos", 
                  Aluno_contrato.objects.filter(aluno=aluno, pontos__gt=0, campeonato=campeonato, status=3).order_by('-data_cadastro'),
                  ['id', 'cliente', 'contrato', 'envio', 'data_cadastro', 'pontos'])

    adicionar_aba("Retenção", 
                  Alunos_clientes_pontos_meses_retencao.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data'),
                  ['id', 'cliente', 'contrato', 'envio', 'data', 'pontos', 'semana'])

    workbook.close()
    return HttpResponse("Erro ao exportar excel do alunos")
    #return response

@login_required
def aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato, semana = calcular_semana_vigente()
    nivel_aluno = Mentoria_lista_niveis.objects.filter(id=aluno.nivel).first()
    pontos_aluno_semana = Alunos_posicoes_semana.objects.filter(aluno=aluno, semana=semana, campeonato=campeonato).first()
    context = {
        'aluno': aluno,
        'nivel_aluno': nivel_aluno,
        'pontos_aluno_semana': pontos_aluno_semana,
    }
    return render(request, 'Alunos/aluno.html', context) 

@login_required
def aluno_pontos(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato, semana = calcular_semana_vigente()

    campeonatos = Campeonato.objects.order_by('-identificacao')
    
    campeonato_id = request.GET.get('campeonato_id')
    semana_param = request.GET.get('semana')
    semana_filtro = None

    # Atualiza campeonato se vier via GET
    if campeonato_id:
        try:
            campeonato = Campeonato.objects.get(id=campeonato_id)
        except Campeonato.DoesNotExist:
            pass


    semanas_disponiveis = Alunos_posicoes_semana.objects.filter(
        campeonato=campeonato
    ).values_list('semana', flat=True).distinct().order_by('-semana')
 
    pontos_recebimentos = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_cadastro')
    pontos_desafio = Aluno_desafio.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_cadastro')
    pontos_certificacao = Aluno_certificacao.objects.filter(aluno=aluno, campeonato=campeonato, tipo=3).order_by('-data_cadastro')
    pontos_manuais = Aluno_certificacao.objects.filter(aluno=aluno, campeonato=campeonato, tipo=5).order_by('-data_cadastro')
    
    pontos_contratos = Aluno_contrato.objects.filter(aluno=aluno, pontos__gt=0, campeonato=campeonato, status=3).order_by('-data_cadastro')
    pontos_retencao = Alunos_clientes_pontos_meses_retencao.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data')
    pontos_aluno_semana = Alunos_posicoes_semana.objects.filter(aluno=aluno, semana=semana, campeonato=campeonato).first()
    

        
    if semana_param:
        try:
            semana_filtro = int(semana_param)
            pontos_recebimentos = pontos_recebimentos.filter(semana=semana_filtro)

            pontos_desafio = pontos_desafio.filter(semana=semana_filtro)

            pontos_certificacao = pontos_certificacao.filter(semana=semana_filtro)

            pontos_manuais = pontos_manuais.filter(semana=semana_filtro)

            pontos_contratos = pontos_contratos.filter(envio__semana=semana_filtro)

            pontos_retencao = pontos_retencao.filter(semana=semana_filtro)

            pontos_aluno_semana = Alunos_posicoes_semana.objects.filter(aluno=aluno, semana=semana_filtro, campeonato=campeonato).first()
        except ValueError:
            pass

    

    context = {
        'aluno': aluno,
        'campeonatos': campeonatos,
        'semanas_disponiveis': semanas_disponiveis,
        'campeonato': campeonato,
        'pontos_recebimentos': pontos_recebimentos,
        'pontos_desafio': pontos_desafio,
        'pontos_certificacao': pontos_certificacao,
        'pontos_manuais': pontos_manuais,
        'pontos_contratos': pontos_contratos,
        'pontos_retencao': pontos_retencao,
        'pontos_aluno_semana': pontos_aluno_semana,
        'semana': semana_filtro,
    }
    return render(request, 'Alunos/partials/aba_pontos.html', context)

@login_required
def aluno_clientes(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato, semana = calcular_semana_vigente()

    clientes = (
        Aluno_clientes.objects
        .filter(aluno=aluno)
        .annotate(
            qtd_contratos=Count('contratos', distinct=True),
            qtd_envios=Count('envios_cliente_cl', distinct=True)
        )
        .order_by('-data_criacao')
        .prefetch_related('contratos')
    )


    context = {
        'aluno': aluno,
        'clientes': clientes,
    }
    return render(request, 'Alunos/partials/aba_clientes.html', context)

@login_required
def aluno_faturamento(request, aluno_id):
    return render(request, 'Alunos/partials/aba_faturamento.html')

@login_required
def clas(request):
    query = request.GET.get('q', '')

    campeonato = Campeonato.objects.get(id=5)
    clas_list = Mentoria_cla.objects.filter(campeonato=campeonato).order_by('id')
    if query:
        clas_list = clas_list.filter(
            Q(nome__icontains=query) |
            Q(sigla__icontains=query)
        )
    paginator = Paginator(clas_list, 20)
    page_number = request.GET.get('page')
    clas = paginator.get_page(page_number)


    context = {
        'clas': clas,
        'query': query
    }

    return render(request, 'Clas/clas.html', context)

@login_required
def cla(request, cla_id):
    campeonato, semana = calcular_semana_vigente()
    cla = Mentoria_cla.objects.get(id=cla_id)
    alunos = Alunos.objects.filter(cla=cla).order_by('-nivel')
    
    context = {
        'cla': cla,
        'alunos': alunos,
    }

    return render(request, 'Clas/cla.html', context)

@login_required
def exportar_clientes(request):
    clientes = Aluno_clientes.objects.all()
    
    # Preparando a resposta para o arquivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=clientes_subidopro.xlsx'

    # Criando a planilha
    workbook = xlsxwriter.Workbook(response)
    worksheet = workbook.add_worksheet()

    # Estilo para os cabeçalhos
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  # Adiciona borda
    })

    # Estilo para o conteúdo das células
    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  # Adiciona borda
    })

    # Ajustando a largura das colunas
    for col in range(7):  # De A (0) até G (6)
        worksheet.set_column(col, col, 24)

    # Cabeçalhos das colunas
    headers = ['ID', 'Título', 'Documento', 'Data de Criação', 'Aluno', 'Pontos', 'Status']
    
    # Escrevendo os cabeçalhos
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Preenchendo os dados
    row = 1
    for cliente in clientes:
        # Remover o timezone dos datetimes
        data_criacao = cliente.data_criacao.replace(tzinfo=None) if cliente.data_criacao else None
        
        worksheet.write(row, 0, cliente.id, cell_format)  # ID
        worksheet.write(row, 1, cliente.titulo, cell_format)  # Título
        worksheet.write(row, 2, cliente.documento, cell_format)  # Documento
        worksheet.write(row, 3, data_criacao.strftime('%d/%m/%Y %H:%M') if data_criacao else '', cell_format)  # Data de Criação
        worksheet.write(row, 4, cliente.aluno.nome_completo, cell_format)  # Aluno Res.
        worksheet.write(row, 5, cliente.pontos, cell_format)  # Pontos
        worksheet.write(row, 6, 'Ativo' if cliente.status == 1 else 'Inativo', cell_format)  # Status
        row += 1

    # Fechar o workbook e retornar a resposta
    workbook.close()

    return HttpResponse("Erro ao exportar excel do alunos")
    #return response





@login_required
def balanceamento(request):
    campeonato, semana = calcular_semana_vigente()
    limit = 3000
    pontuacoes = (
        Aluno_envios.objects
        .annotate(mes=TruncMonth('data'))
        .values('aluno_id', 'mes')
        .annotate(total_pontos=Sum('pontos'), total_envios=Count('id', distinct=True))
        .filter(total_pontos__gt=limit, tipo=2, status=3, semana__gt=0, data__gte='2025-03-01', campeonato=campeonato)
        .order_by('aluno_id', 'mes')
    )

    pontos_modificados = []  # Lista para armazenar alterações (DE -> PARA)

    for pontos in pontuacoes:
        aluno_id = pontos["aluno_id"]
        aluno_nome = Alunos.objects.get(id=aluno_id).nome_completo
        mes_dt = pontos["mes"]  # Armazena o objeto datetime original
        pontos["mes_dt"] = mes_dt  # Mantém o datetime para operações
        pontos["aluno_nome"] = aluno_nome  # Adiciona o nome do aluno
        pontos["mes"] = mes_dt.strftime("%B")  # Substitui pela versão por extenso

    for pontos in pontuacoes:
        aluno_id = pontos["aluno_id"]
        mes_atual = pontos["mes"]
        mes_dt = pontos["mes_dt"]  # Usa o datetime armazenado
        pontos_detalhados = (
            Aluno_envios.objects
            .filter(aluno_id=aluno_id, tipo=2, status=3, semana__gt=0, data__gte='2025-03-01', data__month=mes_dt.month)
            .order_by('data_cadastro'))


        total_pontos_aluno = 0
        for item in pontos_detalhados:
            if total_pontos_aluno + item.pontos > limit:
                restante = limit - total_pontos_aluno 
                if restante > 0:
                    pontos_fat = restante
                    total_pontos_aluno += restante
                else:
                    pontos_fat = 0

                pontos_modificados.append({
                    "id": item.id,
                    "aluno_id": aluno_id,
                    "nome": pontos["aluno_nome"],
                    "mes": mes_atual,
                    "de": item.pontos,
                    "para": pontos_fat
                })

                # item.pontos = pontos_fat
                # item.save()

            else:
                total_pontos_aluno += item.pontos
                pontos_modificados.append({
                    "id": item.id,
                    "aluno_id": aluno_id,
                    "nome": pontos["aluno_nome"],
                    "mes": mes_atual,
                    "de": item.pontos,
                    "para": item.pontos,
                })
                    
    return render(request, 'Balanceamento/balanceamento.html', {
        'pontuacoes': pontuacoes,
        'pontos_modificados': pontos_modificados,
    })

@login_required
def retencao(request):
    """
        Regras para reter pontos do cliente
        1º O cliente so recebe pontos se ele tiver enviado no mês passado e no mês atual
        2º O cliente não recebe pontos se ele tiver enviado mais de uma vez no mês atual
        3º Os clientes só é considerado apartir da data de criação 01/09/2024
    """
    
    campeonatoVigente, semana = calcular_semana_vigente()
    
    def gera_pontos_retencao(valor):
        if valor >= 0 and valor < 1000:
            return 40
        elif valor >= 1000 and valor < 3000:
            return 320
        elif valor >= 3000 and valor < 5000:
            return 720
        elif valor >= 5000 and valor < 9000:
            return 1280
        elif valor >= 9000:
            return 1640
        else:
            return 0
    
    # Obtém a data de hoje
    hoje = timezone.now().date()
    #hoje = timezone.make_aware(datetime(2025, 3, 31)).date()
    primeiro_dia_mes_atual = hoje.replace(day=1)
    primeiro_dia_mes_passado = (primeiro_dia_mes_atual - timedelta(days=1)).replace(day=1)
    ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)

    # Filtrando os envios aprovados desde 01/09/2024
    envios = Aluno_envios.objects.filter(data__gte='2024-09-01', status=3, campeonato=campeonatoVigente, cliente__data_criacao__gte='2024-09-01') 
    #envios = Aluno_envios.objects.filter(data__gte='2024-09-01', status=3, campeonato=campeonatoVigente, cliente__data_criacao__gte='2024-09-01', data_cadastro__range=[primeiro_dia_mes_atual, hoje]).order_by('-data') 


    # Verifica se o mesmo contrato teve envio no mês passado
    envio_mes_passado_CL_subquery = Aluno_envios.objects.filter(
        cliente=OuterRef('cliente'),  # Agora filtra por contrato
        data__range=[primeiro_dia_mes_passado, ultimo_dia_mes_passado],
        status=3
    ).values('id')[:1]  # Retorna qualquer envio válido

    envio_mes_passado_CT_subquery = Aluno_envios.objects.filter(
        contrato=OuterRef('contrato'),  # Agora filtra por contrato
        data__range=[primeiro_dia_mes_passado, ultimo_dia_mes_passado],
        status=3
    ).values('id')[:1]  # R



    # Primeiro envio do contrato no mês atual
    envio_mes_atual_subquery = Aluno_envios.objects.filter(
        id=OuterRef('pk'),
        data__range=[primeiro_dia_mes_atual, hoje],
        status=3
    ).order_by('data').values('id', 'valor', 'contrato__tipo_contrato', 'contrato__id')[:1]

    # Verifica se já foi registrado na tabela de retenção
    retencao_envios_mes_atual_subquery = Alunos_clientes_pontos_meses_retencao.objects.filter(
        envio=OuterRef('pk'),
        data__range=[primeiro_dia_mes_atual, hoje]
    ).values('id')[:1]

    # Anotando os resultados e filtrando os registros
    envios_nova_retencao = envios.annotate(
        envio_mes_passado_cl=Exists(envio_mes_passado_CL_subquery),
        envio_mes_passado_ct=Exists(envio_mes_passado_CT_subquery),
        envio_mes_atual=Subquery(envio_mes_atual_subquery.values('id')),
        contrato_id_anotado=Subquery(envio_mes_atual_subquery.values('contrato__id')),
        valor_envio=Subquery(envio_mes_atual_subquery.values('valor')),
        tipo_contrato_anotado=Subquery(envio_mes_atual_subquery.values('contrato__tipo_contrato')),
        retencao_envio_mes_atual=Exists(retencao_envios_mes_atual_subquery)
    ).filter(
        envio_mes_passado_cl=True,  # Garante que teve envio no mês passado
        envio_mes_passado_ct=True,  # Garante que teve envio no mês passado
        envio_mes_atual__isnull=False,  # Teve envio neste mês
        retencao_envio_mes_atual=False  # Ainda não recebeu retenção
    )

    clientes_que_vai_ser_retidos = []
    for cli_retencao in envios_nova_retencao:

        if cli_retencao.tipo_contrato_anotado == 2:
            valor_inicial = float(cli_retencao.valor_envio)
            valor_final = valor_inicial * 0.1

        else:
            valor_final = float(cli_retencao.valor_envio)


        pontos_retencao = gera_pontos_retencao(valor_final)

        clientes_que_vai_ser_retidos.append({
                "aluno": cli_retencao.aluno.nome_completo,
                "aluno_id": cli_retencao.aluno.id,
                "cliente_id": cli_retencao.cliente.id,
                "contrato_id": cli_retencao.contrato_id_anotado,
                "envio_id": cli_retencao.id,
                "tipo_contrato": cli_retencao.tipo_contrato_anotado,
                "valor_envio": cli_retencao.valor_envio,
                "pontos_retencao": int(pontos_retencao),
            })
        
        # novo_registro = Alunos_clientes_pontos_meses_retencao.objects.get_or_create(
        #     aluno_id=cli_retencao.aluno.id,
        #     cliente_id=cli_retencao.cliente.id,
        #     envio_id=cli_retencao.id,
        #     contrato_id=cli_retencao.contrato_id_anotado,
        #     campeonato=campeonatoVigente,
        #     data=hoje,
        #     defaults={
        #         "pontos": pontos_retencao,
        #         "qtd_envios": 0,
        #         "ids_envios": "",
        #         "semana": semana
        #     }
        # )


    #Contar quantos clientes tem 
    cont_clientes = envios_nova_retencao.count()


    context = {
        "cont_retencoes": cont_clientes,
        "retencoes": clientes_que_vai_ser_retidos
    }

    return render(request, "Retencao/retencao.html", context)

@login_required
def exportar_ranking(request):
    semana_rank = ranking_streamer()

    # Preparando a resposta para o arquivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Ranking Real Time.xlsx'

    # Criando a planilha
    workbook = xlsxwriter.Workbook(response)
    worksheet = workbook.add_worksheet()

    # Estilo para os cabeçalhos
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  # Adiciona borda
    })

    # Estilo para o conteúdo das células
    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  # Adiciona borda
    })

    # Ajustando a largura das colunas
    for col in range(7):  # De A (0) até G (6)
        worksheet.set_column(col, col, 24)

    # Cabeçalhos das colunas
    headers = ['Posição', 'Aluno ID', 'Nome Aluno', 'Pontuação Total', 'Recebimentos', 'Contratos', 'Retenção', 'Desafios', 'Certificação', 'Manual']
    
    # Escrevendo os cabeçalhos
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Preenchendo os dados
    row = 1
    for rank in semana_rank:
        worksheet.write(row, 0, rank.ranking, cell_format)
        worksheet.write(row, 1, rank.id, cell_format)
        worksheet.write(row, 2, rank.nome_completo, cell_format)
        worksheet.write(row, 3, rank.total_pontos_final, cell_format)
        worksheet.write(row, 4, rank.pontos_recebimento, cell_format)  
        worksheet.write(row, 5, rank.pontos_contrato, cell_format)  
        worksheet.write(row, 6, rank.pontos_retencao, cell_format)
        worksheet.write(row, 7, rank.pontos_desafio, cell_format)
        worksheet.write(row, 8, rank.pontos_certificacao, cell_format)
        worksheet.write(row, 9, rank.pontos_manual, cell_format)
        
        row += 1

    workbook.close()

    #return HttpResponse("Erro ao exportar excel")
    return response
    
@login_required
def ranking(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Você não tem permissão para acessar esta página.")
    
    alunos_list  = ranking_streamer()

    q = request.GET.get('q', '').strip()

    if q:
        if q.isdigit():
            alunos_list = alunos_list.filter(Q(id=int(q)) | Q(nome_completo__icontains=q))
        else:
            alunos_list = alunos_list.filter(Q(nome_completo__icontains=q))

    # Contagem de todos os alunos
    cont_rank = alunos_list.count()

    paginator = Paginator(alunos_list, 50)
    page_number = request.GET.get('page')
    semana_rank = paginator.get_page(page_number)

    context = {
        "alunos": semana_rank,
        "q": q,
        "cont_rank": cont_rank,
    }
    return render(request, "Ranking/ranking.html", context)

@login_required
def exportar_ranking_semana(request, semana):
    campeonato, _ = calcular_semana_vigente()
    # Base da query
    semana_rank = Alunos_posicoes_semana.objects.filter(
        semana=semana,
        campeonato=campeonato
    )

    # Preparando a resposta para o arquivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Ranking Semanal - Semana {semana}.xlsx'

    # Criando a planilha
    workbook = xlsxwriter.Workbook(response)
    worksheet = workbook.add_worksheet()

    # Estilo para os cabeçalhos
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  # Adiciona borda
    })

    # Estilo para o conteúdo das células
    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  # Adiciona borda
    })

    # Ajustando a largura das colunas
    for col in range(7):  # De A (0) até G (6)
        worksheet.set_column(col, col, 24)

    # Cabeçalhos das colunas
    headers = ['Posição', 'Aluno ID', 'Nome Aluno', 'Clã', 'Pontuação Total', 'Recebimentos', 'Contratos', 'Retenção', 'Desafios', 'Certificação', 'Manual']
    
    # Escrevendo os cabeçalhos
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Preenchendo os dados
    row = 1
    for rank in semana_rank:
        worksheet.write(row, 0, rank.posicao, cell_format)
        worksheet.write(row, 1, rank.aluno.id, cell_format)
        worksheet.write(row, 2, rank.aluno.nome_completo, cell_format)
        worksheet.write(row, 3, rank.aluno.cla.nome, cell_format)
        worksheet.write(row, 4, rank.pontos_totais, cell_format)
        worksheet.write(row, 5, rank.pontos_recebimento, cell_format)  
        worksheet.write(row, 6, rank.pontos_contrato, cell_format)  
        worksheet.write(row, 7, rank.pontos_retencao, cell_format)
        worksheet.write(row, 8, rank.pontos_desafio, cell_format)
        worksheet.write(row, 9, rank.pontos_certificacao, cell_format)
        worksheet.write(row, 10, rank.pontos_manual, cell_format)
        
        row += 1

    workbook.close()
    # Fechar o workbook e retornar a resposta
    #return HttpResponse("Erro ao exportar excel")
    return response

@login_required
def ranking_semana(request):
    campeonato, _ = calcular_semana_vigente()

    # Lista de semanas disponíveis
    semanas_disponiveis = Alunos_posicoes_semana.objects.filter(
        campeonato=campeonato
    ).values_list('semana', flat=True).distinct().order_by('-semana')

    # Semana vinda do filtro (GET)
    semana_param = request.GET.get('semana')
    if semana_param and semana_param.isdigit():
        semana_filtrada = int(semana_param)
    else:
        semana_filtrada = semanas_disponiveis.first()

    # Campo de busca
    q = request.GET.get('q', '').strip()

    # Base da query
    semana_rank_list = Alunos_posicoes_semana.objects.filter(
        semana=semana_filtrada,
        campeonato=campeonato
    )

    # Aplica filtro de busca se houver
    if q:
        semana_rank_list = semana_rank_list.filter(
            Q(aluno__nome_completo__icontains=q) |
            Q(aluno__email__icontains=q) |
            Q(aluno__id__iexact=q)
        )

    # Contagem de todos os alunos
    cont_rank = semana_rank_list.count()

    semana_rank_list = semana_rank_list.order_by('posicao')

    # Paginação
    paginator = Paginator(semana_rank_list, 20)
    page_number = request.GET.get('page')
    semana_rank = paginator.get_page(page_number)

    ultima_att = semana_rank_list.first().data if semana_rank_list.exists() else None
    
    


    context = {
        "alunos": semana_rank,
        "cont_rank": cont_rank,
        "semana": semana_filtrada,
        "semanas_disponiveis": semanas_disponiveis,
        "q": q,
        "ultima_att": ultima_att,
    }

    return render(request, "Ranking/ranking_semana.html", context)

@login_required
def exportar_ranking_semana_cla(request, semana):
    campeonato, _ = calcular_semana_vigente()
    # Base da query
    semana_rank = Mentoria_cla_posicao_semana.objects.filter(
        semana=semana,
        campeonato=campeonato
    )

    # Preparando a resposta para o arquivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Ranking Semanal Clã - Semana {semana}.xlsx'

    # Criando a planilha
    workbook = xlsxwriter.Workbook(response)
    worksheet = workbook.add_worksheet()

    # Estilo para os cabeçalhos
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  # Adiciona borda
    })

    # Estilo para o conteúdo das células
    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  # Adiciona borda
    })

    # Ajustando a largura das colunas
    for col in range(7):  # De A (0) até G (6)
        worksheet.set_column(col, col, 24)

    # Cabeçalhos das colunas
    headers = ['Posição', 'Clã ID', 'Clã', 'Pontuação Total', 'Recebimentos', 'Contratos', 'Retenção', 'Desafios', 'Certificação', 'Manual']
    
    # Escrevendo os cabeçalhos
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Preenchendo os dados
    row = 1
    for rank in semana_rank:
        worksheet.write(row, 0, rank.posicao, cell_format)
        worksheet.write(row, 1, rank.cla.id, cell_format)
        worksheet.write(row, 2, rank.cla.nome, cell_format)
        worksheet.write(row, 3, rank.pontos_totais, cell_format)
        worksheet.write(row, 4, rank.pontos_recebimento, cell_format)
        worksheet.write(row, 5, rank.pontos_contrato, cell_format)
        worksheet.write(row, 6, rank.pontos_retencao, cell_format)
        worksheet.write(row, 7, rank.pontos_desafio, cell_format)
        worksheet.write(row, 8, rank.pontos_certificacao, cell_format)
        worksheet.write(row, 9, rank.pontos_manual, cell_format)
        
        row += 1

    # Fechar o workbook e retornar a resposta
    workbook.close()
    #return HttpResponse("Erro ao exportar excel")
    return response

@login_required
def ranking_cla(request):
    campeonato, _ = calcular_semana_vigente()

    # Lista de semanas disponíveis
    semanas_disponiveis = Mentoria_cla_posicao_semana.objects.filter(
        campeonato=campeonato
    ).values_list('semana', flat=True).distinct().order_by('-semana')

    # Semana vinda do filtro (GET)
    semana_param = request.GET.get('semana')
    if semana_param and semana_param.isdigit():
        semana_filtrada = int(semana_param)
    else:
        semana_filtrada = semanas_disponiveis.first()

    # Campo de busca
    q = request.GET.get('q', '').strip()

    # Base da query
    semana_rank_list = Mentoria_cla_posicao_semana.objects.filter(
        semana=semana_filtrada,
        campeonato=campeonato
    )

        # Aplica filtro de busca se houver
    if q:
        semana_rank_list = semana_rank_list.filter(
            Q(cla__nome__icontains=q) |
            Q(cla__sigla__icontains=q) |
            Q(cla__id__iexact=q)
        )
    
    # Contagem de todos os alunos
    cont_rank = semana_rank_list.count()

    semana_rank_list = semana_rank_list.order_by('posicao')

    paginator = Paginator(semana_rank_list, 20)
    page_number = request.GET.get('page')
    cla_rank = paginator.get_page(page_number)

    ultima_att = semana_rank_list.first().data if semana_rank_list.exists() else None

    context = {
        "cla_rank": cla_rank,
        "semana": semana_filtrada,
        "cont_rank": cont_rank,
        "semanas_disponiveis": semanas_disponiveis,
        "q": q,
        "ultima_att": ultima_att,
    }
    
    return render(request, "Ranking/ranking_cla.html", context)

