from django.shortcuts import render, HttpResponse, redirect
from django.utils import timezone
from .models import *
from django.db.models import OuterRef, Subquery, F, Count, Sum, Exists
from django.db.models.functions import TruncMonth
from datetime import date, datetime
from .utils import *
from collections import defaultdict


def calcula_balanceamento_func(request):
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

                item.pontos = pontos_fat
                item.save()

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
    
def calculo_retencao_func(request):
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
    
    # Obtém a data de hojez
    hoje = timezone.now().date()
    #hoje = timezone.make_aware(datetime(2025, 4, 30)).date()
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
        
        novo_registro = Alunos_clientes_pontos_meses_retencao.objects.get_or_create(
            aluno_id=cli_retencao.aluno.id,
            cliente_id=cli_retencao.cliente.id,
            envio_id=cli_retencao.id,
            contrato_id=cli_retencao.contrato_id_anotado,
            campeonato=campeonatoVigente,
            data=hoje,
            defaults={
                "pontos": pontos_retencao,
                "qtd_envios": 0,
                "ids_envios": "",
                "semana": semana
            }
        )


    #Contar quantos clientes tem 
    cont_clientes = envios_nova_retencao.count()


    context = {
        "cont_retencoes": cont_clientes,
        "retencoes": clientes_que_vai_ser_retidos
    }

    return render(request, "Retencao/retencao.html", context)
        
def calculo_ranking_func(request):
    campeonato_vigente, semana = calcular_semana_vigente()
    
    resultado = ranking_streamer()
    ### Criar novo registro na tabela Alunos_posicoes_semana para cada aluno com ranking
    for posicao in resultado:
        Alunos_posicoes_semana.objects.create(
            aluno_id=posicao.id,
            cla_id=posicao.cla.id if posicao.cla else None,
            semana=semana,
            posicao=posicao.ranking,
            tipo=1,
            data=timezone.now(),
            pontos_recebimento=posicao.pontos_recebimento or 0,
            pontos_desafio=posicao.pontos_desafio or 0,
            pontos_certificacao=posicao.pontos_certificacao or 0,
            pontos_manual=posicao.pontos_manual or 0,
            pontos_contrato=posicao.pontos_contrato or 0,
            pontos_retencao=posicao.pontos_retencao or 0,
            pontos_totais=posicao.total_pontos_final or 0,
            campeonato_id=campeonato_vigente.id
        )

    # Somar os pontos por clã
    clan_pontuacao = defaultdict(lambda: {
        "pontos_recebimento": 0,
        "pontos_desafio": 0,
        "pontos_certificacao": 0,
        "pontos_manual": 0,
        "pontos_contrato": 0,
        "pontos_retencao": 0,
        "pontos_totais": 0
    })

    for aluno in resultado:
        if aluno.cla:
            cla_id = aluno.cla.id
            clan_pontuacao[cla_id]["pontos_recebimento"] += aluno.pontos_recebimento or 0
            clan_pontuacao[cla_id]["pontos_desafio"] += aluno.pontos_desafio or 0
            clan_pontuacao[cla_id]["pontos_certificacao"] += aluno.pontos_certificacao or 0
            clan_pontuacao[cla_id]["pontos_manual"] += aluno.pontos_manual or 0
            clan_pontuacao[cla_id]["pontos_contrato"] += aluno.pontos_contrato or 0
            clan_pontuacao[cla_id]["pontos_retencao"] += aluno.pontos_retencao or 0
            clan_pontuacao[cla_id]["pontos_totais"] += aluno.total_pontos_final or 0

    # Criar ranking dos clãs baseado nos pontos totais
    ranking_cla = sorted(clan_pontuacao.items(), key=lambda x: x[1]["pontos_totais"], reverse=True)

    # Salvar a posição dos clãs na semana
    for rank, (cla_id, pontos) in enumerate(ranking_cla, start=1):
        Mentoria_cla_posicao_semana.objects.create(
            cla_id=cla_id,
            semana=semana,
            posicao=rank,
            data=timezone.now(),
            pontos_recebimento=pontos["pontos_recebimento"],
            pontos_desafio=pontos["pontos_desafio"],
            pontos_certificacao=pontos["pontos_certificacao"],
            pontos_manual=pontos["pontos_manual"],
            pontos_contrato=pontos["pontos_contrato"],
            pontos_retencao=pontos["pontos_retencao"],
            pontos_totais=pontos["pontos_totais"],
            campeonato_id=campeonato_vigente.id
        )


    return render(request, "Ranking/ranking.html", {"alunos": resultado})

def atualizar_subidometro_func(request):
    campeonato_vigente, semana_subidometro = calcular_semana_vigente()

    # Buscar todos os alunos
    alunos = Alunos.objects.all()
    
    # Buscar todos os registros do Subidômetro para a semana e campeonato atuais
    alunos_subidometro = Alunos_Subidometro.objects.filter(
        semana=semana_subidometro, campeonato=campeonato_vigente
    )
    
    # Criar um dicionário para acesso rápido aos registros existentes
    alunos_subidometro_dict = {sub.aluno.id: sub for sub in alunos_subidometro}

    # Processar cada aluno e atualizar/criar registros
    for aluno in alunos:
        cla = aluno.cla if aluno.cla else None
        subidometro_entry = alunos_subidometro_dict.get(aluno.id)

        if subidometro_entry:
            nivel = subidometro_entry.nivel if subidometro_entry.nivel else aluno.nivel
            subidometro_entry.nivel = nivel
            subidometro_entry.save()
        else:
            Alunos_Subidometro.objects.create(
                aluno=aluno,
                campeonato=campeonato_vigente,
                semana=semana_subidometro,
                cla=cla,
                nivel=aluno.nivel,
                data=timezone.now(),
            )

    # Ordenar e atualizar os níveis dos alunos
    alunos_subidometro_ordenado = Alunos_Subidometro.objects.filter(
        semana=semana_subidometro, campeonato=campeonato_vigente
    ).order_by("-pontuacao_geral")

    for subidometro in alunos_subidometro_ordenado:
        aluno = subidometro.aluno
        aluno.nivel = subidometro.nivel
        aluno.save()

    
    return redirect("home")

