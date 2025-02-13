from django.shortcuts import render
from subidometro.models import *
from django.db.models.functions import Coalesce
from django.db.models import OuterRef, Subquery, F, Value, Q, DecimalField, Value, Sum
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'Home/home.html')

@login_required
def alunos(request):
    alunos = Alunos.objects.all().order_by('id')
    context = {
        'alunos': alunos,
    }
    return render(request, 'Alunos/alunos.html', context)

@login_required
def aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato = Campeonato.objects.get(id=5)
    pontuacoes = Aluno_pontuacao.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data')

    context = {
        'aluno': aluno,
        'pontuacoes': pontuacoes,
    }
    return render(request, 'Alunos/aluno.html', context)

@login_required
def clas(request):
    campeonato = Campeonato.objects.get(id=5)
    clas = Mentoria_cla.objects.filter(campeonato=campeonato).order_by('id')

    context = {
        'clas': clas,
    }
    return render(request, 'Clas/clas.html', context)

@login_required
def cla(request, cla_id):
    campeonato = Campeonato.objects.get(id=5)
    cla = Mentoria_cla.objects.get(id=cla_id, campeonato=campeonato)
    alunos = Alunos.objects.filter(cla=cla).order_by('-nivel')
    
    context = {
        'cla': cla,
        'alunos': alunos,
    }

    return render(request, 'Clas/cla.html', context)

@login_required
def clientes(request):
    PAGE = 150
    clientes = Aluno_clientes.objects.all().order_by('id')[:PAGE]
    context = {
        'clientes': clientes,
    }
    return render(request, 'Clientes/clientes.html', context)

@login_required
def cliente(request, cliente_id):
    
    cliente = Aluno_clientes.objects.get(id=cliente_id)
    contratos = Aluno_clientes_contratos.objects.filter(cliente=cliente).order_by('-data_contrato')
    envios = Aluno_envios.objects.filter(cliente=cliente).order_by('-data')
    context = {
        'cliente': cliente,
        'contratos': contratos,
        'envios': envios,
    }
    return render(request, 'Clientes/cliente.html', context)

@login_required
def ranking(request):
    CAMPEONATO_ID = 5
    try:
        campeonatoVigente = Campeonato.objects.get(id=CAMPEONATO_ID)
    except Campeonato.DoesNotExist:
        return render(request, "ranking.html", {"error": "Campeonato vigente não encontrado."})

    # IDs dos registros de mentoria_cla com definido = 1
    mentoria_ids = Mentoria_cla.objects.filter(definido=1).values_list('id', flat=True)

    # Filtra os alunos conforme as condições:
    alunos_qs = Alunos.objects.filter(
        Q(status__in=['ACTIVE', 'APPROVED', 'COMPLETE']),
        nivel__lt=16,
        cla__in=mentoria_ids
    )

    # Subquery para total de pontos (garantindo DecimalField)
    subquery_pontos = Aluno_pontuacao.objects.filter(
        aluno=OuterRef('pk'),
        status=3,
        semana__gt=0
    ).filter(
        Q(envio__campeonato_id=CAMPEONATO_ID) |
        Q(desafio__campeonato_id=CAMPEONATO_ID) |
        Q(certificacao__campeonato_id=CAMPEONATO_ID)
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
        campeonato_id=CAMPEONATO_ID,
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

    return render(request, "Ranking/ranking.html", {"alunos": resultado})