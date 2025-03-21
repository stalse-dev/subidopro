from django.shortcuts import render
from django.http import HttpResponse
from subidometro.models import *
from subidometro.utils import *
from django.db.models.functions import TruncMonth, Cast
from django.db.models import OuterRef, Subquery, F, Sum, Count, Value, CharField, DecimalField, IntegerField, DateTimeField, DateField, Max, Min
from django.contrib.auth.decorators import login_required
from datetime import date
from django.core.paginator import Paginator
import pandas as pd
import xlsxwriter
from django.utils import timezone 
from datetime import timedelta
from datetime import datetime
from django.views.decorators.cache import never_cache


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
 
    pontos_recebimentos = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_cadastro')
    pontos_desafio = Aluno_desafio.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_cadastro')
    pontos_certificacao = Aluno_certificacao.objects.filter(aluno=aluno, campeonato=campeonato).order_by('-data_cadastro')
    
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
    semana = semana  + 1

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
        
        # novo_registro = Alunos_clientes_pontos_meses_retencao.objects.get_or_create(
        #         aluno_id=cli_retencao.aluno.id,
        #         cliente_id=cli_retencao.id,
        #         campeonato=campeonatoVigente,
        #         data=hoje,
        #         defaults={
        #             "pontos": pontos_retencao,
        #             "qtd_envios": 0,
        #             "ids_envios": "",
        #             "semana": semana
        #         }
        #     )


    #Contar quantos clientes tem 
    cont_clientes = clientes_nova_retencao.count()


    context = {
        "cont_retencoes": cont_clientes,
        "retencoes": clientes_que_vai_ser_retidos
    }

    return render(request, "Retencao/retencao.html", context)


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

    context = {"retencoes": clientes_que_vai_ser_retidos}
    return render(request, "Retencao/retencao_v2.html", context)

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
    alunos = ranking_streamer()
    return render(request, "Ranking/ranking.html", {"alunos": alunos})

@login_required
def ranking_semana(request):
    campeonato, semana = calcular_semana_vigente()
    # Obtendo a maior semana disponível para o campeonato vigente
    maior_semana = Alunos_posicoes_semana.objects.filter(campeonato=campeonato).aggregate(Max('semana'))['semana__max']
    print(f"Maior semana: {maior_semana}")
    # Buscando os registros com a maior semana encontrada
    semana_rank_list = Alunos_posicoes_semana.objects.filter(semana=maior_semana, campeonato=campeonato).order_by('posicao')
    paginator = Paginator(semana_rank_list, 20)
    page_number = request.GET.get('page')
    semana_rank = paginator.get_page(page_number)
    return render(request, "Ranking/ranking_semana.html", {"alunos": semana_rank, "semana": maior_semana})

@login_required
def ranking_cla(request):
    campeonato, semana = calcular_semana_vigente()

    maior_semana = Mentoria_cla_posicao_semana.objects.filter(campeonato=campeonato).aggregate(Max('semana'))['semana__max']

    cla_rank_list = Mentoria_cla_posicao_semana.objects.filter(semana=maior_semana, campeonato=campeonato).order_by('posicao')
    paginator = Paginator(cla_rank_list, 20)
    page_number = request.GET.get('page')
    cla_rank = paginator.get_page(page_number)
    return render(request, "Ranking/ranking_cla.html", {"cla_rank": cla_rank, "semana": maior_semana})

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

@login_required
def teste_gabriel(request):
    # Obtém a data de hoje
    hoje = timezone.now().date()
    primeiro_dia_mes_atual = hoje.replace(day=1)
    primeiro_dia_mes_passado = (primeiro_dia_mes_atual - timedelta(days=1)).replace(day=1)
    ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)

    # Buscar primeiro envio do mês passado para cada cliente
    envios_mes_passado = Aluno_envios.objects.filter(
        data__range=[primeiro_dia_mes_passado, ultimo_dia_mes_passado], status=3
    ).values('cliente').annotate(id_envio=Min('id'))

    # Buscar primeiro envio do mês atual para cada cliente
    envios_mes_atual = Aluno_envios.objects.filter(
        data__range=[primeiro_dia_mes_atual, hoje], status=3
    ).values('cliente').annotate(id_envio=Min('id'))

    # Criar dicionários {cliente_id: id_envio} para ambos os meses
    dict_envios_passado = {e['cliente']: e['id_envio'] for e in envios_mes_passado}
    dict_envios_atual = {e['cliente']: e['id_envio'] for e in envios_mes_atual}

    # Identificar clientes que enviaram nos dois meses consecutivos
    clientes_retenção = set(dict_envios_passado.keys()).intersection(set(dict_envios_atual.keys()))

    # Buscar clientes com envios repetitivos no mês atual
    clientes_repetitivos = Aluno_envios.objects.filter(
        data__range=[primeiro_dia_mes_atual, hoje], status=3
    ).values('cliente').annotate(qtd_envios=Count('id')).filter(qtd_envios__gt=1)

    dict_clientes_repetitivos = {c['cliente']: c['qtd_envios'] for c in clientes_repetitivos}

    # Buscar id_retencao_mes na tabela Alunos_clientes_pontos_meses_retencao
    retencao_clientes = Alunos_clientes_pontos_meses_retencao.objects.filter(
        data__range=[primeiro_dia_mes_atual, hoje]
    ).values('cliente', 'id')

    dict_retencao_clientes = {r['cliente']: r['id'] for r in retencao_clientes}

    # Montar a lista de retorno
    clientes_retorno = [
        {
            "cliente": cliente,
            "id_envio_mes_passado": dict_envios_passado.get(cliente, "Não enviado"),
            "id_envio_mes_atual": dict_envios_atual.get(cliente, "Não enviado"),
            "qtd_envios_mes_atual": dict_clientes_repetitivos.get(cliente, 1),
            "id_retencao_mes": dict_retencao_clientes.get(cliente, "Não retido")
        }
        for cliente in clientes_retenção
    ]

    context = {
        "clientes_retorno": clientes_retorno
    }

    return render(request, "test.html", context)

@login_required
def teste_gabriel_2(request):
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
        
        # novo_registro = Alunos_clientes_pontos_meses_retencao.objects.get_or_create(
        #         aluno_id=cli_retencao.aluno.id,
        #         cliente_id=cli_retencao.id,
        #         campeonato=campeonatoVigente,
        #         data=hoje,
        #         defaults={
        #             "pontos": pontos_retencao,
        #             "qtd_envios": "",
        #             "ids_envios": "",
        #             "semana": semana
        #         }
        #     )



            


    #Contar quantos clientes tem 
    cont_clientes = clientes_nova_retencao.count()


    context = {
        "cont_retencoes": cont_clientes,
        "retencoes": clientes_que_vai_ser_retidos
    }

    return render(request, "Retencao/retencao.html", context)

