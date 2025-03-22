from django.shortcuts import render, HttpResponse, redirect
from django.utils import timezone
from .models import *
from django.db.models import OuterRef, Subquery, F, Count, Sum
from django.db.models.functions import TruncMonth
from datetime import date
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
    
def calculo_retencao_func_v1(request):

    def gera_pontos_clientes(valor):
        if valor >= 0 and valor < 1000:
            return 60
        elif valor >= 1000 and valor < 3000:
            return 480
        elif valor >= 3000 and valor < 5000:
            return 1080
        elif valor >= 5000 and valor < 9000:
            return 1920
        elif valor >= 9000:
            return 2460
        else:
            return 0

    def gera_pontos_retencao(pontos):
        mapping = {
            60: 40,
            480: 320,
            1080: 720,
            1920: 1280,
            2460: 1640,
        }
        return mapping.get(pontos, 0)
    
    campeonatoVigente, semana = calcular_semana_vigente()
    #data_inicio = campeonatoVigente.data_inicio
    data_inicio = "2024-09-04"
    hoje = date.today()
    # Subquery para obter a data do contrato mais recente (status = 1) para cada cliente
    latest_contract_id_qs = Aluno_clientes_contratos.objects.filter(
        cliente=OuterRef('pk'),  # Filtra contratos pelo cliente
        status=1
    ).order_by('-data_contrato', '-id').values('id')[:1] # Exclui contratos sem data

    ultimo_envio_qs = Aluno_envios.objects.filter(
        cliente=OuterRef('contratos__cliente'),  # Filtrando pelo cliente
        status=3,
        tipo=2,
        data__range=(data_inicio, hoje),
        semana__gt=0
    ).exclude(valor__isnull=True).order_by('-data').values('valor')[:1]

    # Filtramos os clientes ativos e contratos ativos
    clientes_com_ultimo_contrato = Aluno_clientes.objects.annotate(
        latest_contract_id=Subquery(latest_contract_id_qs),  # Pega o ID do último contrato
    ).filter(
        status=1,  # Clientes ativos
        contratos__id=F('latest_contract_id')  # Filtra apenas o contrato mais recente
    ).distinct()

    # Filtramos os envios conforme as condições
    retencoes = clientes_com_ultimo_contrato.filter(
        envios_cliente_cl__status=3,
        envios_cliente_cl__tipo=2,
        envios_cliente_cl__data__range=(data_inicio, hoje),
        envios_cliente_cl__semana__gt=0
    )

    retencoes = retencoes.annotate(
        envio_month=TruncMonth('envios_cliente_cl__data'),
        ultimo_envio=Subquery(ultimo_envio_qs)  # Último valor de envio
    )

    retencoes = retencoes.values(
        'id',  # ID do Cliente
        'contratos__id',  # ID do Contrato
        'contratos__valor_contrato',  # Valor do Contrato
        'contratos__tipo_contrato',  # Tipo do Contrato
        'contratos__porcentagem_contrato',  # Porcentagem do Contrato
        'contratos__data_vencimento',  # Data de Vencimento do Contrato
        'aluno__id',  # ID do Aluno
        'aluno__nome_completo',  # Nome do Aluno
        'ultimo_envio',  # Último valor de envio
    ).annotate(
        total_envios=Count('envio_month', distinct=True)
    ).filter(
        total_envios__gt=1
    ).order_by('-total_envios')


    retencao_por_cliente = (
        Alunos_clientes_pontos_meses_retencao.objects
        .values("cliente_id")  # Agrupa por cliente
        .annotate(total_envios_cl=Count("id"))  # Conta os registros de cada cliente
        .order_by("-total_envios_cl")  # Opcional: ordena pelo total em ordem decrescente
    )


    # Criar um dicionário com os envios da segunda query (total de retenções)
    historico_envios = {
        int(item['cliente_id']): item['total_envios_cl']  # ID do Cliente -> Total de envios retidos
        for item in retencao_por_cliente
    }

    # Lista de clientes onde os envios do contrato recente são menores que os envios retidos
    clientes_que_vai_ser_retidos = []

    now = timezone.now()

    for cliente in retencoes:
        total_envios_historico = historico_envios.get(int(cliente['id']), 0)
        if int(total_envios_historico) < (int(cliente['total_envios']) - 1):
            comp = "Total de envios: " + str(int(cliente['total_envios']) - 1) + " - Total de envios retidos: " + str(total_envios_historico)

            if cliente['contratos__tipo_contrato'] == 2:
                valor_inicial = float(cliente['ultimo_envio'])
                valor_final = valor_inicial * 0.1

                # Atualiza o valor do envio para o valor de comissão
                cliente['valorEnvio'] = valor_final
                pontos_cliente = gera_pontos_clientes(valor_final)
                cliente['pontosCliente'] = pontos_cliente
            else:
                # Se não houver valor de contrato, utiliza valorEnvio; caso contrário, utiliza valorContrato
                if not cliente['contratos__valor_contrato']:
                    valor_final = float(cliente['ultimo_envio'])
                    pontos_cliente = gera_pontos_clientes(float(cliente['ultimo_envio']))
                else:
                    valor_final = float(cliente['contratos__valor_contrato'])
                    pontos_cliente = gera_pontos_clientes(float(cliente['contratos__valor_contrato']))

                cliente['valorEnvio'] = valor_final
                cliente['pontosCliente'] = pontos_cliente

            pontos_retencao = gera_pontos_retencao(cliente['pontosCliente'])

            tem_envio_camp = Aluno_envios.objects.filter(cliente_id=cliente['id'], campeonato=campeonatoVigente).exists()
            if tem_envio_camp:
                clientes_que_vai_ser_retidos.append({
                    "aluno": cliente['aluno__nome_completo'],
                    "cliente_id": cliente['id'],
                    "contratos_id": cliente['contratos__id'],
                    "total_envios": comp,
                    "valor_envio": cliente['valorEnvio'],
                    "pontos_cliente": int(cliente['pontosCliente']),
                    "pontos_retencao": int(pontos_retencao)
                })

                novo_registro = Alunos_clientes_pontos_meses_retencao.objects.get_or_create(
                    aluno_id=cliente['aluno__id'],
                    cliente_id=cliente['id'],
                    campeonato=campeonatoVigente,
                    data=now,
                    defaults={
                        "pontos": pontos_retencao,
                        "qtd_envios": int(cliente['total_envios']),
                        "ids_envios": "",
                        "semana": semana
                    }
                )

    context = {"retencoes": clientes_que_vai_ser_retidos}
    return render(request, "Retencao/retencao.html", context)

def calculo_retencao_func(request):
    """
        Regras para reter pontos do cliente
        1º O cliente so recebe pontos se ele tiver enviado no mês passado e no mês atual
        2º O cliente não recebe pontos se ele tiver enviado mais de uma vez no mês atual
        3º Os clientes só é considerado apartir da data de criação 01/09/2024
    """
    
    campeonatoVigente, semana = calcular_semana_vigente()

    print(f"Semana: {semana} - Campeonato: {campeonatoVigente}")  
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
    primeiro_dia_mes_atual = hoje.replace(day=1)
    primeiro_dia_mes_passado = (primeiro_dia_mes_atual - timedelta(days=1)).replace(day=1)
    ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)


    clientes = Aluno_clientes.objects.filter(data_criacao__gte='2024-09-01').order_by('id')

    primeiro_envio_mes_passado_subquery = Aluno_envios.objects.filter(
        cliente=OuterRef('pk'), 
        data__range=[primeiro_dia_mes_passado, ultimo_dia_mes_passado], 
        status=3
    ).order_by('data').values('id')[:1]

    primeiro_envio_mes_atual_subquery = Aluno_envios.objects.filter(
        cliente=OuterRef('pk'), 
        data__range=[primeiro_dia_mes_atual, hoje], 
        status=3
    ).order_by('data').values('id', 'valor', 'contrato__tipo_contrato', 'contrato__id')[:1]

    retencao_clientes_mes_atual_subquery = Alunos_clientes_pontos_meses_retencao.objects.filter(
        cliente=OuterRef('pk'),
        data__range=[primeiro_dia_mes_atual, hoje]
    ).values('id')[:1]

    clientes_nova_retencao = clientes.annotate(
        primeiro_envio_mes_passado=Subquery(primeiro_envio_mes_passado_subquery),
        primeiro_envio_mes_atual=Subquery(primeiro_envio_mes_atual_subquery.values('id')),
        contrato_id_anotado=Subquery(primeiro_envio_mes_atual_subquery.values('contrato__id')),
        valor_envio=Subquery(primeiro_envio_mes_atual_subquery.values('valor')),
        tipo_contrato_anotado=Subquery(primeiro_envio_mes_atual_subquery.values('contrato__tipo_contrato')),
        retencao_cliente_mes_atual=Subquery(retencao_clientes_mes_atual_subquery)
    ).filter(
        primeiro_envio_mes_passado__isnull=False,
        primeiro_envio_mes_atual__isnull=False,
        retencao_cliente_mes_atual__isnull=True,
    )

    clientes_que_vai_ser_retidos = []
    for cli_retencao in clientes_nova_retencao:
        if cli_retencao.tipo_contrato_anotado == 2:
            valor_inicial = float(cli_retencao.valor_envio)
            valor_final = valor_inicial * 0.1

        else:
            valor_final = float(cli_retencao.valor_envio)


        pontos_retencao = gera_pontos_retencao(valor_final)

        clientes_que_vai_ser_retidos.append({
                "aluno": cli_retencao.aluno.nome_completo,
                "aluno_id": cli_retencao.aluno.id,
                "cliente_id": cli_retencao.id,
                "contrato_id": cli_retencao.contrato_id_anotado,
                "envio_id": cli_retencao.primeiro_envio_mes_atual,
                "tipo_contrato": cli_retencao.tipo_contrato_anotado,
                "valor_envio": cli_retencao.valor_envio,
                "pontos_retencao": int(pontos_retencao),
            })
        
        novo_registro = Alunos_clientes_pontos_meses_retencao.objects.get_or_create(
                aluno_id=cli_retencao.aluno.id,
                cliente_id=cli_retencao.id,
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
    cont_clientes = clientes_nova_retencao.count()


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

