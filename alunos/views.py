from django.shortcuts import render
from django.http import HttpResponse
from subidometro.models import *
from subidometro.utils import *
from django.db.models.functions import TruncMonth, Cast
from django.db.models import OuterRef, Subquery, F, Sum, Count, Value, CharField, DecimalField, IntegerField, DateTimeField, DateField

from django.contrib.auth.decorators import login_required
from datetime import date
from django.core.paginator import Paginator
import pandas as pd
import xlsxwriter
from django.utils import timezone
from datetime import timedelta
from datetime import datetime


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
def exportar_aluno_pontuacoes(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato, semana = calcular_semana_vigente()
    pontuacoes = Aluno_pontuacao.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data')

    # Preparando a resposta para o arquivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=aluno_pontuacoes_{aluno.id}_subidopro.xlsx'

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
    for col in range(9):  # De A (0) até I (8)
        worksheet.set_column(col, col, 24)

    # Cabeçalhos das colunas
    headers = [
        'ID', 'Tipo Pontuação', 'ID Vínculo', 'Descrição', 'Pontos',
        'Data', 'Status', 'Status Motivo', 'Status Comentário'
    ]

    # Escrevendo os cabeçalhos
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Preenchendo os dados
    row = 1
    for pontuacao in pontuacoes:
        # Remover o timezone dos datetimes
        data = pontuacao.data.replace(tzinfo=None) if pontuacao.data else None

        # Determinar ID de vínculo
        if pontuacao.tipo_pontuacao.id == 1:
            id_vinculo = pontuacao.envio.id if pontuacao.envio else ''
        elif pontuacao.tipo_pontuacao.id == 2:
            id_vinculo = pontuacao.desafio.id if pontuacao.desafio else ''
        elif pontuacao.tipo_pontuacao.id == 3:
            id_vinculo = pontuacao.certificacao.id if pontuacao.certificacao else ''
        else:
            id_vinculo = ''

        worksheet.write(row, 0, pontuacao.id, cell_format)  # ID
        worksheet.write(row, 1, pontuacao.tipo_pontuacao.nome, cell_format)  # Tipo Pontuação
        worksheet.write(row, 2, id_vinculo, cell_format)  # ID Vínculo
        worksheet.write(row, 3, pontuacao.descricao, cell_format)  # Descrição
        worksheet.write(row, 4, pontuacao.pontos, cell_format)  # Pontos
        worksheet.write(row, 5, data.strftime('%d/%m/%Y %H:%M') if data else '', cell_format)  # Data
        worksheet.write(row, 6, 'Aprovado' if pontuacao.status == 3 else 'Pendente', cell_format)  # Status
        worksheet.write(row, 7, pontuacao.status_motivo, cell_format)  # Status Motivo
        worksheet.write(row, 8, pontuacao.status_comentario, cell_format)  # Status Comentário
        row += 1

    # Fechar o workbook e retornar a resposta
    workbook.close()
    return response

@login_required
def aluno(request, aluno_id):
    aluno = Alunos.objects.get(id=aluno_id)
    campeonato, semana = calcular_semana_vigente()
    pontuacoes = Aluno_pontuacao.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data')
    pontos_aluno = Alunos_posicoes_semana.objects.filter(aluno=aluno, semana=semana).first()
    pontos_contratos = Aluno_contrato.objects.filter(aluno=aluno, campeonato=campeonato, pontos__gt=0).order_by('-data')
    context = {
        'aluno': aluno,
        'pontuacoes': pontuacoes,
        'pontos_aluno': pontos_aluno,
        'pontos_contratos': pontos_contratos,
    }
    return render(request, 'Alunos/aluno.html', context) 

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
    contratos = Aluno_clientes_contratos.objects.filter(cliente=cliente).order_by('-data_contrato')
    envios = Aluno_envios.objects.filter(cliente=cliente).order_by('-data')
    context = {
        'cliente': cliente,
        'contratos': contratos,
        'envios': envios,
    }
    return render(request, 'Clientes/cliente.html', context)

@login_required
def balanceamento(request):
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

                print("O ID Envio: ", envio_id, "Vai receber: ", faltante)
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

@login_required
def retencao(request):
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

    latest_contract_id_qs = Aluno_clientes_contratos.objects.filter(
    cliente=OuterRef('pk'),
    status=1
    ).order_by('-data_contrato', '-id').values('id')[:1] 

    data_inicio = '2024-09-01'
    hoje = date.today()

    ultimo_envio_qs = Aluno_envios.objects.filter(
        cliente=OuterRef('contratos__cliente'),  # Filtrando pelo cliente
        status=3,
        tipo=2,
        data__range=(data_inicio, hoje),
        semana__gt=0
    ).exclude(valor__isnull=True).order_by('-data').values('valor')[:1]

    clientes_com_ultimo_contrato = Aluno_clientes.objects.annotate(
        latest_contract_id=Subquery(latest_contract_id_qs),
    ).filter(
        status=1,
        contratos__id=F('latest_contract_id')
    ).distinct()

    retencoes = clientes_com_ultimo_contrato.filter(
        envios_cliente_cl__status=3,
        envios_cliente_cl__tipo=2,
        envios_cliente_cl__data__range=(data_inicio, hoje),
        envios_cliente_cl__semana__gt=0
    )

    retencoes = retencoes.annotate(
        envio_month=TruncMonth('envios_cliente_cl__data'),
        ultimo_envio=Subquery(ultimo_envio_qs)  
    )

    retencoes = retencoes.values(
        'id',
        'contratos__id',  
        'contratos__valor_contrato', 
        'contratos__tipo_contrato', 
        'contratos__porcentagem_contrato', 
        'contratos__data_vencimento', 
        'aluno__id',
        'aluno__apelido',
        'ultimo_envio',  
    ).annotate(
        total_envios=Count('envio_month', distinct=True)
    ).filter(
        total_envios__gt=1
    ).order_by('-total_envios')

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
            cliente['PontosRetencao'] = pontos_retencao

    return render(request, "Retencao/retencao.html", {"retencoes": retencoes})

@login_required
def exportar_ranking(request):
    alunos = calculo_ranking_def()

    campeonato, semana = calcular_semana_vigente()

    # Preparando a resposta para o arquivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=ranking_subidopro.xlsx'


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

    # Estilo para as células do corpo
    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  # Adiciona borda
    })

    # Ajustando a largura das colunas
    for col in range(11):  # De A até K (0 a 10)
        worksheet.set_column(col, col, 24)  # Define largura de 24

    # Cabeçalhos das colunas
    headers = [
        'Posição', 'ID Aluno', 'Nome do Aluno', 'Clã', 
        'PF Pontos potenciais', 'PF Pontos efetivos', 
        'Pontos Desafios', 'Pontos Certificações',
        'Pontos Contratos', 'Pontos Clientes Retenção', 'Pontos Final'
    ]
    
    # Escrevendo os cabeçalhos
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)


    row = 1
    for aluno in alunos:
        worksheet.write(row, 0, aluno["rank"])
        worksheet.write(row, 1, aluno["id"])
        worksheet.write(row, 2, aluno["nome"])
        worksheet.write(row, 3, aluno["cla_name"])

        # Subqueries separadas por tipo de pontuação
        pontos_envios_potenciais = Aluno_pontuacao.objects.filter(
            aluno_id=aluno["id"],
            status=3,
            semana__gt=0,
            tipo_pontuacao_id=1  # Envios
        ).filter(
            Q(envio__campeonato_id=campeonato.id) |
            Q(desafio__campeonato_id=campeonato.id) |
            Q(certificacao__campeonato_id=campeonato.id)
        ).aggregate(total=Coalesce(Sum('pontos_previsto', output_field=DecimalField()), Value(0, output_field=DecimalField())))['total']

        # Subqueries separadas por tipo de pontuação
        pontos_envios = Aluno_pontuacao.objects.filter(
            aluno_id=aluno["id"],
            status=3,
            semana__gt=0,
            tipo_pontuacao_id=1  # Envios
        ).filter(
            Q(envio__campeonato_id=campeonato.id) |
            Q(desafio__campeonato_id=campeonato.id) |
            Q(certificacao__campeonato_id=campeonato.id)
        ).aggregate(total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField())))['total']

        pontos_desafios = Aluno_pontuacao.objects.filter(
            aluno_id=aluno["id"],
            status=3,
            semana__gt=0,
            tipo_pontuacao_id=2  # Desafios
        ).filter(
            Q(envio__campeonato_id=campeonato.id) |
            Q(desafio__campeonato_id=campeonato.id) |
            Q(certificacao__campeonato_id=campeonato.id)
        ).aggregate(total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField())))['total']

        pontos_certificacoes = Aluno_pontuacao.objects.filter(
            aluno_id=aluno["id"],
            status=3,
            semana__gt=0,
            tipo_pontuacao_id=3  # Certificações
        ).filter(
            Q(envio__campeonato_id=campeonato.id) |
            Q(desafio__campeonato_id=campeonato.id) |
            Q(certificacao__campeonato_id=campeonato.id)
        ).aggregate(total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField())))['total']

        # Escrevendo os valores no Excel

        worksheet.write(row, 4,  pontos_envios_potenciais)  
        worksheet.write(row, 5, pontos_envios)  
        worksheet.write(row, 6, pontos_desafios or 0)
        worksheet.write(row, 7, pontos_certificacoes or 0)

        worksheet.write(row, 8, aluno["totalPontosClientes"])
        worksheet.write(row, 9, aluno["totalPontosClientesRetencao"])
        worksheet.write(row, 10, aluno["totalPontosFinal"])

        row += 1


    # Fechar o workbook e retornar a resposta
    workbook.close()
    return response
    
@login_required
def ranking(request):
    alunos = calculo_ranking_def()
    return render(request, "Ranking/ranking.html", {"alunos": alunos})

@login_required
def ranking_semana(request):
    campeonato, semana = calcular_semana_vigente()
    semana_rank_list = Alunos_posicoes_semana.objects.filter(semana=semana).order_by('posicao')
    paginator = Paginator(semana_rank_list, 20)
    page_number = request.GET.get('page')
    semana_rank = paginator.get_page(page_number)
    return render(request, "Ranking/ranking_semana.html", {"alunos": semana_rank, "semana": semana})

@login_required
def ranking_cla(request):
    campeonato, semana = calcular_semana_vigente()
    cla_rank_list = Mentoria_cla_posicao_semana.objects.filter(semana=semana).order_by('posicao')
    paginator = Paginator(cla_rank_list, 20)
    page_number = request.GET.get('page')
    cla_rank = paginator.get_page(page_number)
    return render(request, "Ranking/ranking_cla.html", {"cla_rank": cla_rank, "semana": semana})


@login_required
def extrato(request, aluno_id):
    campeonato, semana = calcular_semana_vigente()
    data_limite = timezone.now() - timedelta(weeks=1)

    # pontuacoes = Aluno_pontuacao.objects.filter(campeonato=campeonato, data_cadastro__gte=data_limite).order_by('-data_cadastro')
    # contratos = Aluno_contrato.objects.filter(campeonato=campeonato, pontos__gt=0, data_cadastro__gte=data_limite).order_by('-data_cadastro')

    pontuacoes = Aluno_pontuacao.objects.filter(campeonato=campeonato, aluno_id=aluno_id).order_by('-data_cadastro')
    contratos = Aluno_contrato.objects.filter(campeonato=campeonato, aluno_id=aluno_id).order_by('-data_cadastro')

    extrato_list = []
    for pontuacao in pontuacoes:
        tipo_pontuacao = {
            1: "Comprovante de recebimento",
            2: "Desafio",
            3: "Certificação"
        }.get(pontuacao.tipo_pontuacao.id, f"Outro ({pontuacao.tipo})")

        cliente_titulo = pontuacao.envio.cliente.titulo if pontuacao.tipo_pontuacao.id == 1 else "Sem Cliente"
        cliente_id = pontuacao.envio.cliente.id if pontuacao.tipo_pontuacao.id == 1 else "N/A"
        contrato_id = pontuacao.envio.contrato.id if pontuacao.tipo_pontuacao.id == 1 else "Sem Contrato"
        contrato_tipo = ("Fixo" if pontuacao.envio.contrato.tipo_contrato == 1 else "Contrato variável") if pontuacao.tipo_pontuacao.id == 1 else "Sem contrato"
        valor = f"R$ {pontuacao.envio.valor:.2f}" if pontuacao.tipo_pontuacao.id == 1 else "R$ 0.00"

        status = {
            0: "Não analisado",
            1: "Pendente de análise",
            2: "Invalidado",
            3: "Validado"
        }.get(pontuacao.status, "Sem status")


        data_pontuacao = pontuacao.data.replace(tzinfo=None) if pontuacao.data else None  # Variável renomeada

        # Remover timezone da data_cadastro
        data_cadastro = pontuacao.data_cadastro.replace(tzinfo=None) if pontuacao.data_cadastro else None

        if pontuacao.envio and pontuacao.envio.data_analise is not None:
            data_analise = pontuacao.envio.data_analise.replace(tzinfo=None)
        else:
            data_analise = None

        if pontuacao.envio and pontuacao.envio.rastreador_analise is not None:
            rastreador_analise = pontuacao.envio.rastreador_analise
        else:
            rastreador_analise = "N/A"

        extrato_list.append([
            data_pontuacao,
            data_cadastro,
            pontuacao.aluno.nome_completo,
            pontuacao.aluno.id,
            tipo_pontuacao,
            cliente_titulo,
            cliente_id,
            contrato_id,
            contrato_tipo,
            valor,
            status,
            data_analise,
            rastreador_analise,
            pontuacao.pontos_previsto,
            pontuacao.pontos
        ])

    for contrato in contratos:
        contrato_tipo = "Fixo" if contrato.envio.contrato.tipo_contrato == 1 else "Contrato variável"
        status = {
            0: "Não analisado",
            1: "Pendente de análise",
            2: "Invalidado",
            3: "Validado"
        }.get(contrato.envio.status, "Sem status")

        data_pontuacao = contrato.data if contrato.data else None


        # Remover timezone da data_cadastro
        data_cadastro = contrato.data_cadastro.replace(tzinfo=None) if contrato.data_cadastro else None


        # Remover timezone da data_analise
        if contrato.envio.data_analise == None:
            data_analise = None
        else:
            data_analise = contrato.envio.data_analise.replace(tzinfo=None)
        rastreador_analise = contrato.envio.rastreador_analise or "N/A"

        extrato_list.append([
            data_pontuacao,
            data_cadastro,
            contrato.aluno.nome_completo,
            contrato.aluno.id,
            "Contrato",
            contrato.envio.cliente.titulo,
            contrato.envio.cliente.id,
            contrato.envio.contrato.id,
            contrato_tipo,
            f"R$ {contrato.envio.valor:.2f}",
            status,
            data_analise,
            rastreador_analise,
            contrato.pontos,
            contrato.pontos
        ])

    df = pd.DataFrame(extrato_list, columns=[
        "Data Recebimento", "Data Cadastro", "Aluno", "ID Aluno", "Tipo Pontuação", "Cliente",
        "ID Cliente", "ID Contrato", "Tipo Contrato", "Valor",
        "Status", "Data Análise", "Rastreador Análise", "Pontos Previsto", "Pontos Efetivos"
    ])

    # Remover timezone das datas no DataFrame
    df["Data Recebimento"] = pd.to_datetime(df["Data Recebimento"], errors="coerce")
    df["Data Cadastro"] = pd.to_datetime(df["Data Cadastro"], errors="coerce")
    df["Data Análise"] = pd.to_datetime(df["Data Análise"], errors="coerce")

    df["Mês"] = df["Data Recebimento"].dt.month

    # Reorganizar as colunas para que "Mês" fique em primeiro lugar
    colunas_ordenadas = ["Mês"] + [col for col in df.columns if col != "Mês"]
    df = df[colunas_ordenadas]

    # Ordenar pela data mais recente
    df = df.sort_values(by="Data Recebimento", ascending=False)

    # Criar resposta HTTP para download do Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=extrato_aluno_{aluno_id}.xlsx'

    # Criar um arquivo Excel na resposta
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Extrato', index=False)

        # Ajustar a largura das colunas
        workbook = writer.book
        worksheet = writer.sheets['Extrato']
        for i, column in enumerate(df.columns):
            worksheet.set_column(i, i, 20)  # Define largura de 20 para cada coluna

    return response
