from subidometro.models import *
from django.db.models.functions import Coalesce
from django.db.models import OuterRef, Subquery, F, Value, Q, DecimalField, Value, Sum, Window
from datetime import date, timedelta
from django.db.models.functions import Rank

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

def calculo_ranking_def():
    campeonato, semana = calcular_semana_vigente()

    mentoria_ids = Mentoria_cla.objects.filter(definido=1).values_list('id', flat=True)

    alunos_qs = Alunos.objects.filter(
        Q(status__in=['ACTIVE', 'APPROVED', 'COMPLETE']),
        nivel__lt=16,
        cla__in=mentoria_ids
    )

    subquery_pontos = Aluno_pontuacao.objects.filter(
        aluno=OuterRef('pk'),
        status=3,
        semana__gt=0
    ).filter(
        Q(envio__campeonato_id=campeonato.id) |
        Q(desafio__campeonato_id=campeonato.id) |
        Q(certificacao__campeonato_id=campeonato.id)
    ).values('aluno').annotate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    ).values('total')

    # Subquery para total de pontos clientes (garantindo DecimalField)
    subquery_pontos_clientes = Aluno_clientes.objects.filter(
        aluno=OuterRef('pk'),
        status=1,
        pontos__gt=0
    ).values('aluno').annotate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    ).values('total')

    # Subquery para total de pontos clientes retencao (garantindo DecimalField)
    subquery_total_pontos_clientes_retencao = Alunos_clientes_pontos_meses_retencao.objects.filter(
        aluno=OuterRef('pk'),
        campeonato_id=campeonato.id,
        pontos__gt=0
    ).values('aluno').annotate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    ).values('total')

    # Aplicando as subqueries
    alunos_qs = alunos_qs.annotate(
        total_pontos=Coalesce(Subquery(subquery_pontos, output_field=DecimalField()), Value(0, output_field=DecimalField())),
        total_pontos_clientes=Coalesce(Subquery(subquery_pontos_clientes, output_field=DecimalField()), Value(0, output_field=DecimalField())),
        total_pontos_clientes_retencao=Coalesce(Subquery(subquery_total_pontos_clientes_retencao, output_field=DecimalField()), Value(0, output_field=DecimalField())),
        total_pontos_final=F('total_pontos') + F('total_pontos_clientes') + F('total_pontos_clientes_retencao')
    )

    # Criando lista de dicionários
    resultado = [
        {
            "id": aluno.id,
            "nome": aluno.nome_completo,
            "cla": aluno.cla.id,
            "cla_name": aluno.cla.nome,
            "totalPontos": aluno.total_pontos,
            "totalPontosClientes": aluno.total_pontos_clientes,
            "totalPontosClientesRetencao": aluno.total_pontos_clientes_retencao,
            "totalPontosFinal": aluno.total_pontos_final,
        }
        for aluno in alunos_qs
    ]

    # Ordena a lista pelo totalPontosFinal (do maior para o menor)
    resultado = sorted(resultado, key=lambda x: x["totalPontosFinal"], reverse=True)

    # Atribui ranking (1 para o maior pontuador, 2 para o segundo, etc.)
    for i, aluno in enumerate(resultado, start=1):
        aluno["rank"] = i

    return  resultado

def ranking_streamer():
    campeonato, semana = calcular_semana_vigente()
    mentoria_ids = Mentoria_cla.objects.filter(definido=1).values_list('id', flat=True)
    print(campeonato, semana)
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
        total_pontos_final=F('pontos_recebimento') + F('pontos_desafio') + F('pontos_certificacao') + F('pontos_contrato') + F('pontos_retencao')
    ).annotate(
        ranking=Window(
            expression=Rank(),
            order_by=F('total_pontos_final').desc()
        )
    )

    return alunos_qs
