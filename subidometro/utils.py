from subidometro.models import *
from django.db.models.functions import Coalesce
from django.db.models import OuterRef, Subquery, F, Value, Q, DecimalField, Value, Sum, Window
from django.db.models.functions import Rank
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import OuterRef, Subquery, F, Count, Sum, Exists


def calcular_semana_vigente():
    """
    Calcula a semana vigente de um campeonato com base na data de início.
    
    :return: tuple - Campeonato e número da semana vigente.
    """
    # Buscar o campeonato com o maior ID
    campeonato = Campeonato.objects.filter(ativo=True).order_by('id').first()
    if not campeonato:
        campeonato = Campeonato.objects.order_by('-id').first()
        return None, 0  # Nenhum campeonato encontrado
    
    data_inicio = campeonato.data_inicio
    hoje = date.today()
    
    if hoje < data_inicio:
        return campeonato, 0  # O campeonato ainda não começou
    
    delta = hoje - data_inicio
    semana_vigente = delta.days // 7
    
    return campeonato, semana_vigente

def ranking_streamer():
    campeonato, semana = calcular_semana_vigente()
    mentoria_ids = Mentoria_cla.objects.filter(definido=1).values_list('id', flat=True)

    alunos_qs = Alunos.objects.filter(
        Q(status__in=['ACTIVE', 'APPROVED', 'COMPLETE']),
        nivel__lt=16,
        cla__in=mentoria_ids
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


def calculo_retencao_func(data_referencia):
    """
        Regras para reter pontos do cliente
        1º O cliente so recebe pontos se ele tiver enviado no mês passado e no mês atual
        2º O cliente não recebe pontos se ele tiver enviado mais de uma vez no mês atual
        3º Os clientes só é considerado apartir da data de criação 01/09/2024
    """
    
    campeonatoVigente, semana = calcular_semana_vigente()
    

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
    envios = Aluno_envios.objects.filter(data__gte='2024-09-01', status=3, campeonato=campeonatoVigente, cliente__data_criacao__gte='2024-09-01', contrato__data_contrato__gte='2024-09-01')

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



def calculo_retencao_mensal(data_referencia):
    """
    Calcula a retenção de pontos para um mês específico e registra no banco de dados.
    Recebe uma data de referência (qualquer dia do mês para o qual o cálculo deve ser feito).
    Retorna o número de retenções processadas e a lista de clientes retidos.
    """
    print(f"\n--- Iniciando cálculo de retenção para o mês de {data_referencia.strftime('%Y-%m')} ---")
    
    # 1º O cliente só recebe pontos se ele tiver enviado no mês passado e no mês atual
    # 2º O cliente não recebe pontos se ele tiver enviado mais de uma vez no mês atual
    # 3º Os clientes só é considerado a partir da data de criação 01/09/2024
    
    campeonatoVigente, semana_vigente = calcular_semana_vigente() 
    
    primeiro_dia_mes_atual = data_referencia.replace(day=1)
    ultimo_dia_mes_atual = (primeiro_dia_mes_atual + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    primeiro_dia_mes_passado = (primeiro_dia_mes_atual - timedelta(days=1)).replace(day=1)
    ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)

    print(f"Período de Referência: {primeiro_dia_mes_atual.strftime('%d/%m/%Y')} a {ultimo_dia_mes_atual.strftime('%d/%m/%Y')}")
    print(f"Período Mês Passado: {primeiro_dia_mes_passado.strftime('%d/%m/%Y')} a {ultimo_dia_mes_passado.strftime('%d/%m/%Y')}")


    # Filtrando os envios aprovados desde 01/09/2024 que são do mês de referência
    # E que o cliente foi criado a partir de 01/09/2024
    envios_do_mes_atual = Aluno_envios.objects.filter(
        data__range=[primeiro_dia_mes_atual, ultimo_dia_mes_atual], 
        status=3, 
        campeonato=campeonatoVigente, 
        cliente__data_criacao__gte='2024-09-01'
    ).order_by('cliente', 'contrato', 'data') 

    print(f"Total de envios aprovados no mês de referência para análise: {envios_do_mes_atual.count()}")

    # Subquery para verificar se houve envio do MESMO CLIENTE no mês passado
    envio_mes_passado_CL_subquery = Aluno_envios.objects.filter(
        cliente=OuterRef('cliente'),
        data__range=[primeiro_dia_mes_passado, ultimo_dia_mes_passado],
        status=3
    ).values('id')[:1] 

    # Subquery para verificar se houve envio do MESMO CONTRATO no mês passado
    envio_mes_passado_CT_subquery = Aluno_envios.objects.filter(
        contrato=OuterRef('contrato'),
        data__range=[primeiro_dia_mes_passado, ultimo_dia_mes_passado],
        status=3
    ).values('id')[:1]

    # Contar envios por cliente e contrato no mês atual para aplicar a regra "enviou apenas uma vez"
    envios_por_cliente_contrato_mes_atual = Aluno_envios.objects.filter(
        cliente=OuterRef('cliente'),
        contrato=OuterRef('contrato'),
        data__range=[primeiro_dia_mes_atual, ultimo_dia_mes_atual],
        status=3
    ).annotate(
        num_envios_no_mes=Count('id')
    ).values('num_envios_no_mes')


    # Anotando os resultados e filtrando os registros
    envios_para_analisar = envios_do_mes_atual.annotate(
        houve_envio_mes_passado_cl=Exists(envio_mes_passado_CL_subquery),
        houve_envio_mes_passado_ct=Exists(envio_mes_passado_CT_subquery),
        contagem_envios_mes_atual=Subquery(envios_por_cliente_contrato_mes_atual[:1])
    ).filter(
        houve_envio_mes_passado_cl=True,  # Garante que teve envio do cliente no mês passado
        houve_envio_mes_passado_ct=True,  # Garante que teve envio do contrato no mês passado
        contagem_envios_mes_atual=1, # Garante que é o primeiro (e único) envio do cliente/contrato no mês atual
    ).distinct() # Usa distinct para evitar duplicação de envios se a lógica permitir

    print(f"Total de envios qualificados para retenção: {envios_para_analisar.count()}")

    clientes_retidos_info = [] # Para armazenar informações para o print final
    
    for envio in envios_para_analisar:
        # Verifica se este envio já foi processado para retenção neste mês/período
        ja_registrado = Alunos_clientes_pontos_meses_retencao.objects.filter(
            envio=envio,
            data__range=[primeiro_dia_mes_atual, ultimo_dia_mes_atual] 
        ).exists()

        if ja_registrado:
            print(f"  [SKIPPED] Envio {envio.id} (Aluno: {envio.aluno.nome_completo}, Cliente: {envio.cliente.id}) já foi registrado para retenção neste mês.")
            continue 

        valor_final = float(envio.valor)
        if envio.contrato and envio.contrato.tipo_contrato == 2: 
            valor_final = valor_final * 0.1
        
        pontos_retencao = gera_pontos_retencao(valor_final)

        clientes_retidos_info.append({
            "aluno_id": envio.aluno.id,
            "cliente_id": envio.cliente.id,
            "contrato_id": envio.contrato.id if envio.contrato else None,
            "envio_id": envio.id,
            "pontos_retencao": int(pontos_retencao),
        })
        
        # Cria ou atualiza o registro na tabela de retenção
        novo_registro, created = Alunos_clientes_pontos_meses_retencao.objects.get_or_create(
            aluno=envio.aluno,
            cliente=envio.cliente,
            envio=envio,
            contrato=envio.contrato,
            campeonato=campeonatoVigente,
            data=ultimo_dia_mes_atual, 
            defaults={
                "pontos": pontos_retencao,
                "qtd_envios": 1, 
                "ids_envios": str(envio.id),
                "semana": semana_vigente 
            }
        )
        if created:
            print(f"  [CREATED] Retenção para Envio {envio.id} (Aluno: {envio.aluno.nome_completo}, Pontos: {pontos_retencao})")
        else:
            print(f"  [UPDATED] Retenção para Envio {envio.id} (Aluno: {envio.aluno.nome_completo}, Pontos: {pontos_retencao}) já existia e foi atualizada.") # Teoricamente, não deveria ser atualizada com get_or_create se 'envio' é único

    print(f"--- Cálculo de retenção para {data_referencia.strftime('%Y-%m')} finalizado. {len(clientes_retidos_info)} retenções processadas. ---")
    return clientes_retidos_info

def executar_calculo_retencao_retroativo():
    """
    Executa o cálculo de retenção retroativo do mês 03/2025 até o mês atual,
    com prints para acompanhamento no shell.
    """
    print("\n##### INICIANDO CÁLCULO DE RETENÇÃO RETROATIVO #####")
    
    data_inicio_retroativo = datetime(2025, 3, 1).date()
    hoje = timezone.now().date()
    
    print(f"Período de cálculo: De {data_inicio_retroativo.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}")

    data_atual_loop = data_inicio_retroativo
    
    while data_atual_loop <= hoje:
        # Pega o primeiro dia do mês para garantir que a data_referencia sempre seja o início do mês
        # Isso é importante para a consistência do cálculo de "mês atual" dentro da função `calculo_retencao_mensal`
        data_referencia_para_calculo = data_atual_loop.replace(day=1)
        
        # Se for o mês atual, ajustamos o ultimo_dia_mes_atual para 'hoje' dentro da função `calculo_retencao_mensal`
        # para incluir dados até o dia corrente.
        # No entanto, para a data de referência passada para a função, basta o primeiro dia do mês.

        print(f"\n--- Processando retenção para o mês de {data_referencia_para_calculo.strftime('%Y-%m')} ---")
        
        clientes_retidos = calculo_retencao_func(data_referencia_para_calculo)
        
        if clientes_retidos:
            print(f"Detalhes das retenções para {data_referencia_para_calculo.strftime('%Y-%m')}:")
            for item in clientes_retidos:
                print(f"  Aluno ID: {item['aluno_id']}, Cliente ID: {item['cliente_id']}, Envio ID: {item['envio_id']}, Pontos: {item['pontos_retencao']}")
        else:
            print(f"Nenhuma retenção processada para {data_referencia_para_calculo.strftime('%Y-%m')}.")
        
        # Avança para o próximo mês
        proximo_mes = (data_atual_loop.replace(day=1) + timedelta(days=32)).replace(day=1)
        data_atual_loop = proximo_mes

    print("\n##### CÁLCULO DE RETENÇÃO RETROATIVO CONCLUÍDO #####")


