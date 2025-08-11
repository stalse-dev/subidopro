from subidometro.models import *
from django.db.models.functions import Coalesce
from django.db.models import OuterRef, Subquery, F, Value, Q, DecimalField, Value, Sum, Window
from django.db.models.functions import Rank, TruncMonth
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import OuterRef, Subquery, F, Count, Sum, Exists
from collections import defaultdict


def calcular_semana_vigente(campeonato):
    if not campeonato:
        campeonato = Campeonato.objects.order_by('-id').first()
        return 0
    
    data_inicio = campeonato.data_inicio
    hoje = date.today()
    
    if hoje < data_inicio:
        return 0
    
    delta = hoje - data_inicio
    semana_vigente = delta.days // 7
    
    return semana_vigente

def gera_pontos_retencao(valor):
    """
    Calcula os pontos de retenção com base no valor do envio.
    """
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

def calcula_balanceamento():
    limit = 3000
    pontuacoes = (
        Aluno_envios.objects
        .annotate(mes=TruncMonth('data'))
        .values('aluno_id', 'mes')
        .annotate(total_pontos=Sum('pontos'), total_envios=Count('id', distinct=True))
        .filter(total_pontos__gt=limit, status=3, semana__gt=0)
        .order_by('aluno_id', 'mes')
    )

    pontos_modificados = []

    for pontos in pontuacoes:
        aluno_id = pontos["aluno_id"]
        aluno_nome = Alunos.objects.get(id=aluno_id).nome_completo
        mes_dt = pontos["mes"]
        pontos["mes_dt"] = mes_dt
        pontos["aluno_nome"] = aluno_nome
        pontos["mes"] = mes_dt.strftime("%B")

    for pontos in pontuacoes:
        aluno_id = pontos["aluno_id"]
        mes_atual = pontos["mes"]
        mes_dt = pontos["mes_dt"]
        pontos_detalhados = (
            Aluno_envios.objects
            .filter(aluno_id=aluno_id, status=3, semana__gt=0, data__month=mes_dt.month)
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
                    "para": pontos_fat,
                    "campeonato": item.campeonato.identificacao,
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
                    "campeonato": item.campeonato.identificacao,
                })  

    return ({
        'pontuacoes': pontuacoes,
        'pontos_modificados': pontos_modificados
    }) 

def calculo_retencao(data_referencia, campeonatoVigente):
   
    semana = calcular_semana_vigente(campeonatoVigente)
    cliente__data_criacao = campeonatoVigente.data_inicio if campeonatoVigente else date(2024, 9, 1)

    # Primeiro dia do mês atual
    primeiro_dia_mes_atual = data_referencia.replace(day=1)

    # Último dia do mês atual
    ultimo_dia_mes_atual = (primeiro_dia_mes_atual + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Primeiro dia do mês anterior
    primeiro_dia_mes_passado = (primeiro_dia_mes_atual - timedelta(days=1)).replace(day=1)

    # Último dia do mês anterior
    ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)

    print(f"Período de Referência: {primeiro_dia_mes_atual.strftime('%d/%m/%Y')} a {ultimo_dia_mes_atual.strftime('%d/%m/%Y')}")
    print(f"Período Mês Passado: {primeiro_dia_mes_passado.strftime('%d/%m/%Y')} a {ultimo_dia_mes_passado.strftime('%d/%m/%Y')}")

    # Filtrando os envios aprovados desde 01/09/2024
    envios = Aluno_envios.objects.filter(data__gte=cliente__data_criacao, status=3, campeonato=campeonatoVigente, cliente__data_criacao__gte=cliente__data_criacao, contrato__data_contrato__gte=cliente__data_criacao)

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
        data__range=[primeiro_dia_mes_atual, ultimo_dia_mes_atual],
        status=3
    ).order_by('data').values('id', 'valor', 'contrato__tipo_contrato', 'contrato__id')[:1]

    # Verifica se já foi registrado na tabela de retenção
    retencao_envios_mes_atual_subquery = Alunos_clientes_pontos_meses_retencao.objects.filter(
        envio=OuterRef('pk'),
        data__range=[primeiro_dia_mes_atual, ultimo_dia_mes_atual]
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
            data=data_referencia,
            defaults={
                "pontos": pontos_retencao,
                "qtd_envios": 0,
                "ids_envios": "",
                "semana": semana
            }
        )
    print(f"--- Cálculo de retenção para {data_referencia.strftime('%Y-%m')} finalizado. {len(clientes_que_vai_ser_retidos)} retenções processadas. ---")

def executar_calculo_retencao_retroativo():
    """
    Executa o cálculo de retenção retroativo do mês 03/2025 até o mês atual,
    para todos os campeonatos ativos.
    """
    print("\n##### INICIANDO CÁLCULO DE RETENÇÃO RETROATIVO #####")
    campeonatos = Campeonato.objects.filter(ativo=True)
    
    for campeonato in campeonatos:
        print(f"\n=== PROCESSANDO CAMPEONATO: {campeonato.identificacao} (ID: {campeonato.id}) ===")

        data_inicio_retroativo = campeonatos.data_inicio
        hoje = timezone.now().date()

        data_atual_loop = data_inicio_retroativo

        while data_atual_loop <= hoje:
            data_referencia_para_calculo = data_atual_loop.replace(day=1)

            print(f"\n--- Processando retenção para o mês de {data_referencia_para_calculo.strftime('%Y-%m')} ---")

            clientes_retidos = calculo_retencao(data_referencia_para_calculo, campeonato)

            if clientes_retidos:
                print(f"Detalhes das retenções para {data_referencia_para_calculo.strftime('%Y-%m')}:")
                for item in clientes_retidos:
                    print(f"  Aluno ID: {item['aluno_id']}, Cliente ID: {item['cliente_id']}, Envio ID: {item['envio_id']}, Pontos: {item['pontos_retencao']}")
            else:
                print(f"Nenhuma retenção processada para {data_referencia_para_calculo.strftime('%Y-%m')}.")

            proximo_mes = (data_atual_loop.replace(day=1) + timedelta(days=32)).replace(day=1)
            data_atual_loop = proximo_mes

    print("\n##### CÁLCULO DE RETENÇÃO RETROATIVO CONCLUÍDO #####")

def ranking_streamer(campeonato):
    mentoria_ids = Mentoria_cla.objects.filter(definido=1).values_list('id', flat=True)

    alunos_qs = Alunos.objects.filter(
        Q(status__in=['ACTIVE', 'APPROVED', 'COMPLETE']),
        nivel__lt=16,
        cla__in=mentoria_ids,
    )

    subquery_pontos_recebimento = Aluno_envios.objects.filter(
        aluno=OuterRef('pk'),
        status=3,
        campeonato__id=campeonato.id
    ).values('aluno').annotate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    ).values('total')

    subquery_pontos_desafio = Aluno_desafio.objects.filter(
        aluno=OuterRef('pk'),
        status=3,
        campeonato__id=campeonato.id
    ).values('aluno').annotate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    ).values('total')

    subquery_pontos_certificacao = Aluno_certificacao.objects.filter(
        aluno=OuterRef('pk'),
        status=3,
        campeonato__id=campeonato.id,
        tipo=3
    ).values('aluno').annotate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    ).values('total')

    subquery_pontos_manual = Aluno_certificacao.objects.filter(
        aluno=OuterRef('pk'),
        status=3,
        campeonato__id=campeonato.id,
        tipo=5
    ).values('aluno').annotate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    ).values('total')

    subquery_pontos_contrato = Aluno_contrato.objects.filter(
        aluno=OuterRef('pk'),
        cliente__status=1,
        campeonato__id=campeonato.id,
        pontos__gt=0,
        status=3
    ).values('aluno').annotate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    ).values('total')

    subquery_pontos_retencao = Alunos_clientes_pontos_meses_retencao.objects.filter(
        aluno=OuterRef('pk'),
        campeonato_id=campeonato.id,
        pontos__gt=0
    ).values('aluno').annotate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    ).values('total')

    alunos_qs = alunos_qs.annotate(
        pontos_recebimento=Coalesce(Subquery(subquery_pontos_recebimento, output_field=DecimalField()), Value(0, output_field=DecimalField())),
        pontos_desafio=Coalesce(Subquery(subquery_pontos_desafio, output_field=DecimalField()), Value(0, output_field=DecimalField())),
        pontos_certificacao=Coalesce(Subquery(subquery_pontos_certificacao, output_field=DecimalField()), Value(0, output_field=DecimalField())),
        pontos_manual=Coalesce(Subquery(subquery_pontos_manual, output_field=DecimalField()), Value(0, output_field=DecimalField())),
        pontos_contrato=Coalesce(Subquery(subquery_pontos_contrato, output_field=DecimalField()), Value(0, output_field=DecimalField())),
        pontos_retencao=Coalesce(Subquery(subquery_pontos_retencao, output_field=DecimalField()), Value(0, output_field=DecimalField())),
        total_pontos_final=F('pontos_recebimento') + F('pontos_desafio') + F('pontos_certificacao') + F('pontos_contrato') + F('pontos_retencao') + F('pontos_manual')
    ).annotate(
        ranking=Window(
            expression=Rank(),
            order_by=F('total_pontos_final').desc()
        )
    )

    return alunos_qs

def executar_calculo_retencao_rank():
    campeonatos = Campeonato.objects.filter(ativo=True)

    for campeonato in campeonatos:
        semana = calcular_semana_vigente(campeonato)
        print(f"Calculando ranking de retenção para o campeonato {campeonato.identificacao} na semana {semana}...")
        ranking_ja_calculado = Alunos_posicoes_semana.objects.filter(
            campeonato=campeonato,
            semana=semana
        ).exists()

        if ranking_ja_calculado:
            print(f"Ranking já calculado para o campeonato {campeonato.identificacao} na semana {semana}.")
            continue

        resultado = ranking_streamer(campeonato)
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
                campeonato_id=campeonato.id
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
            pontos_anteriores_cla = Mentoria_cla_pontos.objects.filter(
                cla_id=cla_id,
                campeonato=campeonato,
            ).aggregate(total_pontos=Sum('pontos'))
            
            soma_pontos_cla_existente = pontos_anteriores_cla['total_pontos'] or 0

            pontos["pontos_totais"] = (pontos["pontos_totais"] or 0) + soma_pontos_cla_existente

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
                campeonato_id=campeonato.id
            )

        print(f"Ranking de retenção calculado com sucesso para o campeonato {campeonato.identificacao}!")
