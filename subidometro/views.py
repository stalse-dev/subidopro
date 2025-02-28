from django.shortcuts import render, HttpResponse, redirect
from django.utils import timezone
from .models import *
from django.db.models import OuterRef, Subquery, F, Count, Sum
from django.db.models.functions import TruncMonth
from datetime import date
from .utils import *
from collections import defaultdict


def calcula_balanceamento(request):
    limit = 3000
    pontuacoes = (
        Aluno_pontuacao.objects
        .annotate(mes=TruncMonth('data'))
        .values('aluno_id', 'mes')
        .annotate(total_pontos=Sum('pontos'), total_envios=Count('envio_id', distinct=True))
        .filter(total_pontos__gt=limit, tipo=2, status=3, semana__gt=0, data__gte='2024-09-01')
        .order_by('aluno_id', 'mes')
    )

    updates = []
    zerados = []
    pontos_modificados = []  # Lista para armazenar alterações (DE -> PARA)

    for pontos in pontuacoes:
        aluno_id = pontos["aluno_id"]
        aluno_nome = Alunos.objects.get(id=aluno_id).nome_completo
        mes = pontos["mes"].strftime("%B")  # Converte mês para extenso
        pontos["aluno_nome"] = aluno_nome  # Adiciona o nome do aluno
        pontos["mes"] = mes  # Substitui pela versão por extenso

    for pontos in pontuacoes:
        aluno_id = pontos["aluno_id"]
        pontos_detalhados = (
            Aluno_pontuacao.objects
            .filter(aluno_id=aluno_id, tipo=2, status=3, semana__gt=0, data__gte='2024-09-01')
            .order_by('-pontos')  # Processar do maior para o menor
            .values('envio_id', 'pontos')
        )
        aluno_nome = Alunos.objects.get(id=aluno_id).nome_completo
        mes = pontos["mes"]
        total = 0
        ajustado = []
        zerar_envios = False

        ids_envios = []  # Lista com IDs de envios afetados
        ids_envios_com_pontos = []  # IDs com pontuação mantida

        for pontos_det in pontos_detalhados:
            envio_id = pontos_det['envio_id']
            pontos_envio = pontos_det['pontos']
            ids_envios.append(envio_id)  # Todos os envios afetados

            if zerar_envios or total + pontos_envio > limit:
                if total < limit:
                    #Falta um pouco de pontos
                    faltante = limit - total
                else:
                    faltante = 0
                
                total += pontos_envio
                zerados.append({"id": envio_id, "pontos": faltante})
                pontos_modificados.append({
                    "id": envio_id,
                    "aluno_id": aluno_id,
                    "nome": aluno_nome,
                    "mes": mes,
                    "de": pontos_envio,
                    "para": faltante
                })
                zerar_envios = True

                #ATUALIZANDO O PONTO DO ENVIO NO BANCO
                Aluno_pontuacao.objects.filter(envio_id=envio_id, ).update(pontos=faltante)
            else:
                ajustado.append({"id": envio_id, "pontos": pontos_envio})
                ids_envios_com_pontos.append(envio_id)  # IDs mantidos com pontos
                pontos_modificados.append({
                    "id": envio_id,
                    "aluno_id": aluno_id,
                    "nome": aluno_nome,
                    "mes": mes,
                    "de": pontos_envio,
                    "para": pontos_envio
                })
                total += pontos_envio

        updates.extend(ajustado)

    return render(request, 'Balanceamento/balanceamento.html', {
        'pontuacoes': pontuacoes,
        'pontos_modificados': pontos_modificados,
    })
    
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

def calculo_retencao(request):
    # Subquery para obter a data do contrato mais recente (status = 1) para cada cliente
    latest_contract_id_qs = Aluno_clientes_contratos.objects.filter(
    cliente=OuterRef('pk'),  # Filtra contratos pelo cliente
    status=1
    ).order_by('-data_contrato', '-id').values('id')[:1] # Exclui contratos sem data

    # Define a data de início e a data de hoje
    data_inicio = '2024-09-01'
    hoje = date.today()

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

    # Pegamos o último envio relacionado ao contrato
    retencoes = retencoes.annotate(
        envio_month=TruncMonth('envios_cliente_cl__data'),
        ultimo_envio=Subquery(ultimo_envio_qs)  # Último valor de envio
    )

    # Agrupamos e contamos os envios distintos
    retencoes = retencoes.values(
        'id',  # ID do Cliente
        'contratos__id',  # ID do Contrato
        'contratos__valor_contrato',  # Valor do Contrato
        'contratos__tipo_contrato',  # Tipo do Contrato
        'contratos__porcentagem_contrato',  # Porcentagem do Contrato
        'contratos__data_vencimento',  # Data de Vencimento do Contrato
        'aluno__id',  # ID do Aluno
        'ultimo_envio',  # Último valor de envio
    ).annotate(
        total_envios=Count('envio_month', distinct=True)
    ).filter(
        total_envios__gt=1
    ).order_by('-total_envios')

    campeonatoVigente, semana = calcular_semana_vigente()

    now = timezone.now()
    contador = 0
    #Itera sobre cada cliente para aplicar a lógica
    for cliente in retencoes:
        if cliente['total_envios'] > 0:
            # Se o tipo de contrato for 2 e houver porcentagem, calcula comissão
            if cliente['contratos__tipo_contrato'] == 2 and float(cliente['contratos__porcentagem_contrato']) > 0:
                valor_inicial = float(cliente['ultimo_envio'])
                porcentagem = float(cliente['contratos__porcentagem_contrato'])
                valor_final = valor_inicial - (valor_inicial * (porcentagem / 100))
                valor_comissao = valor_inicial - valor_final

                # Atualiza o valor do envio para o valor de comissão
                cliente['valorEnvio'] = valor_comissao
                pontos_cliente = gera_pontos_clientes(valor_comissao)
                cliente['pontosCliente'] = pontos_cliente
            else:
                # Se não houver valor de contrato, utiliza valorEnvio; caso contrário, utiliza valorContrato
                if not cliente['contratos__valor_contrato']:
                    pontos_cliente = gera_pontos_clientes(float(cliente['ultimo_envio']))
                else:
                    pontos_cliente = gera_pontos_clientes(float(cliente['contratos__valor_contrato']))
                cliente['pontosCliente'] = pontos_cliente

            # # Se pontosCliente estiver vazio ou zero, garante que seja igual aos pontos calculados
            if not cliente['pontosCliente'] or cliente['pontosCliente'] == 0:
                cliente['pontosCliente'] = pontos_cliente

            # Calcula os pontos de retenção com base nos pontos do cliente
            pontos_retencao = gera_pontos_retencao(cliente['pontosCliente'])
            # Conforme o código PHP final, usamos apenas pontos_retencao (apesar de haver comentário de multiplicação)
            pontos_soma = pontos_retencao
            # Verifica quantos registros já existem para esse cliente na tabela de retenção
            registros_count = Alunos_clientes_pontos_meses_retencao.objects.filter(cliente_id=cliente['id']).count()
            opa = int(cliente['total_envios']) - 1
            print(registros_count, opa)
            if registros_count < (int(cliente['total_envios']) - 1):
                contador += 1
                print(f"Registros: novo registro {contador} de {len(retencoes)}")
                
                #Insere um novo registro na tabela de retenção
                novo_registro = Alunos_clientes_pontos_meses_retencao.objects.get_or_create(
                    aluno_id=cliente['aluno__id'],
                    cliente_id=cliente['id'],
                    campeonato=campeonatoVigente,
                    data=now,
                    defaults={
                        "pontos": pontos_soma,
                        "qtd_envios": int(cliente['total_envios']),
                        "ids_envios": "",
                        "semana": 21
                    }
                )



    return render(request, "Retencao/retencao.html", {"retencoes": retencoes})

def calculo_ranking(request):
    campeonato_vigente, semana = calcular_semana_vigente()
    semana = semana + 1

    resultado = calculo_ranking_def()

    print(semana)
    ### Criar novo registro na tabela Alunos_posicoes_semana para cada aluno com ranking
    for posicao in resultado:
        pontos = posicao["totalPontosFinal"] if posicao["totalPontosFinal"] else 0

        # Criar novo registro na tabela AlunosPosicoesSemana
        Alunos_posicoes_semana.objects.create(
            aluno_id=posicao['id'],
            cla_id=campeonato_vigente.id,
            semana=semana,
            posicao=posicao["rank"],
            tipo=1,
            data=timezone.now(),
            pontos=pontos,
            campeonato_id=5
        )

    clan_pontuacao = defaultdict(lambda: 0)
    for aluno in resultado:
        if aluno["cla"]:  # Garantir que o aluno tem um clã
            clan_pontuacao[aluno["cla"]] += aluno["totalPontosFinal"]

    ranking_cla = sorted(clan_pontuacao.items(), key=lambda x: x[1], reverse=True)
    ranking_cla_final = []
    for i, (cla_id, pontos) in enumerate(ranking_cla, start=1):
        ranking_cla_final.append({
            "cla_id": cla_id,
            "pontos": pontos,
            "rank": i
        })

    for posicao in ranking_cla_final:
        pontos = posicao["pontos"] if posicao["pontos"] else 0

        Mentoria_cla_posicao_semana.objects.create(
            cla_id=posicao['cla_id'],
            semana=semana,  # Atualize conforme necessário
            posicao=posicao["rank"],
            data=timezone.now(),
            pontos=pontos,
            campeonato_id=campeonato_vigente.id
        )


    return render(request, "Ranking/ranking.html", {"alunos": resultado})

def atualizar_subidometro(request):
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


def teste(request):
    campeonato, semana = calcular_semana_vigente()
    ponto = Aluno_pontuacao.objects.filter(id=8386).first()
    return HttpResponse(f"Semana: {semana}, Campeonato: {campeonato}, data: {ponto.data_cadastro}")
