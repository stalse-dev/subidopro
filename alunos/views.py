from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from subidometro.models import *
from subidometro.utils import *
from django.db.models.functions import TruncMonth, ExtractMonth
from django.db.models import OuterRef, Subquery, F, Sum, Count, Value, CharField, DecimalField, IntegerField, DateTimeField, DateField, Max, Exists
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

@never_cache
@login_required
def home(request):
    return render(request, 'Home/home.html')

@login_required
def exportar_alunos(request):
    alunos = Alunos.objects.all()
    
    # Preparando a resposta para o arquivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=alunos_subidopro.xlsx'

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
    headers = ['ID', 'Nome Completo', 'Nível', 'Apelido', 'Email', 'Data Criação', 'Status']
    
    # Escrevendo os cabeçalhos
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Preenchendo os dados
    row = 1
    for aluno in alunos:
        # Remover o timezone dos datetimes
        data_criacao = aluno.data_criacao.replace(tzinfo=None) if aluno.data_criacao else None
        
        worksheet.write(row, 0, aluno.id, cell_format)  # ID
        worksheet.write(row, 1, aluno.nome_completo, cell_format)  # Nome Completo
        worksheet.write(row, 2, aluno.nivel, cell_format)  # Nível
        worksheet.write(row, 3, aluno.apelido, cell_format)  # Apelido
        worksheet.write(row, 4, aluno.email, cell_format)  # Email
        worksheet.write(row, 5, data_criacao.strftime('%d/%m/%Y %H:%M') if data_criacao else '', cell_format)  # Data Criação
        worksheet.write(row, 6, 'Ativo' if aluno.status == 'ACTIVE' else 'Inativo', cell_format)  # Status
        row += 1

    # Fechar o workbook e retornar a resposta
    workbook.close()
    return response

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

    paginator = Paginator(alunos_list, 20)
    page_number = request.GET.get('page')
    alunos = paginator.get_page(page_number)

    context = {
        'alunos': alunos,
        'query': query
    }
    return render(request, 'Alunos/alunos.html', context)

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
    return response

@login_required
def aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato, semana = calcular_semana_vigente()

    nivel_aluno = Mentoria_lista_niveis.objects.filter(id=aluno.nivel).first()

    context = {
        'aluno': aluno,
        'nivel_aluno': nivel_aluno,
    }
    return render(request, 'Alunos/aluno.html', context) 

@login_required
def aluno_pontos(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato, semana = calcular_semana_vigente()
 
    pontos_recebimentos = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_cadastro')
    pontos_desafio = Aluno_desafio.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_cadastro')
    pontos_certificacao = Aluno_certificacao.objects.filter(aluno=aluno, campeonato=campeonato, tipo=3).order_by('-data_cadastro')
    
    pontos_contratos = Aluno_contrato.objects.filter(aluno=aluno, pontos__gt=0, campeonato=campeonato, status=3).order_by('-data_cadastro')
    pontos_retencao = Alunos_clientes_pontos_meses_retencao.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data')

    pontos_aluno_semana = Alunos_posicoes_semana.objects.filter(aluno=aluno, semana=semana, campeonato=campeonato).first()
    context = {
        'aluno': aluno,
        'pontos_recebimentos': pontos_recebimentos,
        'pontos_desafio': pontos_desafio,
        'pontos_certificacao': pontos_certificacao,
        'pontos_contratos': pontos_contratos,
        'pontos_retencao': pontos_retencao,
        'pontos_aluno_semana': pontos_aluno_semana,
    }
    return render(request, 'Alunos/partials/aba_pontos.html', context)

@login_required
def aluno_clientes(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato, semana = calcular_semana_vigente()

    clientes = Aluno_clientes.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_criacao')
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
    campeonato = Campeonato.objects.get(id=5)
    cla = Mentoria_cla.objects.get(id=cla_id, campeonato=campeonato)
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

@login_required
def clientes(request):
    query = request.GET.get('q', '')

    clientes_list = Aluno_clientes.objects.all().order_by('id')

    if query:
        clientes_list = clientes_list.filter(
            Q(titulo__icontains=query) | 
            Q(documento__icontains=query)
        )

    paginator = Paginator(clientes_list, 20)
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)

    context = {
        'clientes': clientes,
        'query': query
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

    # Filtra apenas de março (3) a agosto (8)
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

    # Fechar o workbook e retornar a resposta
    workbook.close()
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

