from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from rest_framework import status
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime, parse_date
from subidometro.models import *
from django.http import JsonResponse
from api.models import Log
from api.utils import registrar_log
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.utils import timezone

def gera_pontos(valor):
    """Calcula a pontuação com base no valor informado."""
    valor = float(valor)  # Garante que o valor seja float antes do cálculo
    return int((valor // 100) * 10)

def gera_pontos_contrato(valor):
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

def criar_aluno_cliente(aluno_data):
    # Validar se cliente já existe
    cliente_existente = Aluno_clientes.objects.filter(id=int(aluno_data.get("id"))).exists()
    if cliente_existente: return cliente_existente  # Retorna o cliente existente sem gerar erro

    campeonato = get_object_or_404(Campeonato, id=int(aluno_data.get("campeonato")))
    aluno = get_object_or_404(Alunos, id=int(aluno_data.get("aluno")))

    #Criando um novo registro no modelo Aluno_clientes
    novo_aluno = Aluno_clientes.objects.create(
        id=int(aluno_data.get("id")),
        campeonato=campeonato,
        aluno=aluno,
        titulo=aluno_data.get("titulo"),
        estrangeiro=int(aluno_data.get("estrangeiro", 0)),
        tipo_cliente=int(aluno_data.get("tipoCliente")) if aluno_data.get("tipoCliente") else None,
        tipo_contrato=int(aluno_data.get("tipoContrato")) if aluno_data.get("tipoContrato") else None,
        sociedade=int(aluno_data.get("sociedade")) if aluno_data.get("sociedade") else None,
        cliente_antes_subidopro=int(aluno_data.get("clienteAntesSubidoPro")) if aluno_data.get("clienteAntesSubidoPro") else None,
        documento_antigo=aluno_data.get("documentoANTIGO", ""),
        documento=aluno_data.get("documento"),
        telefone=aluno_data.get("telefone", ""),
        email=aluno_data.get("email", ""),
        data_criacao=parse_datetime(aluno_data.get("dataCriacao")) if aluno_data.get("dataCriacao") else None,
        rastreador=int(aluno_data.get("rastreador", 0)),
        status=int(aluno_data.get("status", 0)),
        motivo_invalido=int(aluno_data.get("motivoInvalido")) if aluno_data.get("motivoInvalido") else None,
        descricao_invalido=aluno_data.get("descricaoInvalido", ""),
        pontos=float(aluno_data.get("pontos", "0")),
        sem_pontuacao=int(aluno_data.get("semPontuacao")) if aluno_data.get("semPontuacao") else None,
        rastreador_analise=int(aluno_data.get("rastreadorAnalise")) if aluno_data.get("rastreadorAnalise") else None
    )

    novo_aluno.save()

    return novo_aluno

def criar_contrato(contrato_data):
    contrato_existente = Aluno_clientes_contratos.objects.filter(id=int(contrato_data.get("id"))).exists()
    if contrato_existente:
        print("Contrato já existente!")
        return contrato_existente
    cliente = get_object_or_404(Aluno_clientes, id=int(contrato_data.get("cliente")))
    # Criando um novo registro no modelo Aluno_clientes
    novo_contrato = Aluno_clientes_contratos.objects.create(
        id=int(contrato_data.get("id")),
        cliente=cliente,
        tipo_contrato=int(contrato_data.get("tipoContrato")) if contrato_data.get("tipoContrato") else None,
        valor_contrato=Decimal(contrato_data.get("valorContrato") or "0.00"),
        porcentagem_contrato=contrato_data.get("porcentagemContrato"),
        arquivo1=contrato_data.get("arquivo1"),
        semana=int(contrato_data.get("semana")) if contrato_data.get("semana") else None,
        status=int(contrato_data.get("status", 0)),
        data_contrato=parse_date(contrato_data.get("dataContrato")) if contrato_data.get("dataContrato") else None,
        data_vencimento=parse_date(contrato_data.get("dataVencimento")) if contrato_data.get("dataVencimento") else None,
        data_criacao=parse_datetime(contrato_data.get("dataCriacao")) if contrato_data.get("dataCriacao") else None,
        motivo_invalido=int(contrato_data.get("motivoInvalido")) if contrato_data.get("motivoInvalido") else None,
        descricao_invalido=contrato_data.get("descricaoInvalido"),
        rastreador_analise=int(contrato_data.get("rastreadorAnalise")) if contrato_data.get("rastreadorAnalise") else None,
        analise_data=parse_datetime(contrato_data.get("analiseData")) if contrato_data.get("analiseData") else None,
        camp_anterior=int(contrato_data.get("campAnterior")),
        id_camp_anterior=int(contrato_data.get("idCampAnterior")) if contrato_data.get("idCampAnterior") else None
    )

    novo_contrato.save()

    return novo_contrato

def criar_envio(envio_data):
    aluno = get_object_or_404(Alunos, id=int(envio_data.get("vinculoAluno")))
    campeonato = get_object_or_404(Campeonato, id=int(envio_data.get("campeonato")))


    tipo = int(envio_data.get("tipo"))
    novo_envio = None
    novo_desafio = None
    novo_certificado = None
    data_now = timezone.now()

    if tipo == 2: #Tabela de Envios tipo 2 = recebimento
        print("Tipo de envio: Recebimento")
        cliente = get_object_or_404(Aluno_clientes, id=int(envio_data.get("vinculoCliente")))
        contrato = get_object_or_404(Aluno_clientes_contratos, id=int(envio_data.get("vinculoContrato")))

        envio = Aluno_envios.objects.filter(id=int(envio_data.get("id"))).first()
        if envio:
            print("Envio já existente!")
            return Response({"message": f"Envio já existente! - '{envio.descricao}'"}, status=status.HTTP_400_BAD_REQUEST)
    

        if contrato.tipo_contrato == 2:  # Co-produção/Multisserviços
            valor_inicial = float(envio_data.get("valor"))
            valor_minimo = valor_inicial * 0.1
            pontos = int(gera_pontos(valor_minimo))
            pontos_previsto = pontos
        else:
            pontos = gera_pontos(float(envio_data.get("valor")))  # Garantindo float
            pontos_previsto = pontos
                
        envio = Aluno_envios.objects.filter(id=int(envio_data.get("id"))).first()
        if envio:
            return Response({"message": f"Envio já existente! - '{envio.descricao}'"}, status=status.HTTP_400_BAD_REQUEST) 


        novo_envio = Aluno_envios.objects.create(
            id=int(envio_data.get("id")),
            campeonato=campeonato,
            aluno=aluno,
            cliente=cliente,
            contrato=contrato,
            data=envio_data.get("data"),
            descricao=envio_data.get("descricao"),
            valor=envio_data.get("valor"),
            arquivo1=envio_data.get("arquivo1", ""),
            arquivo1_motivo=envio_data.get("arquivo1Motivo", ""),
            arquivo1_status=envio_data.get("arquivo1Status", ""),
            data_cadastro=envio_data.get("dataCadastro", ""),
            rastreador_analise=envio_data.get("rastreadorAnalise", ""),
            data_analise=envio_data.get("dataAnalise", ""),
            status=envio_data.get("status"),
            status_motivo=envio_data.get("statusMotivo", ""),
            status_comentario=envio_data.get("statusComentario", ""),
            semana=envio_data.get("semana", ""),
            tipo=tipo,
        )
        novo_envio.save()


        tipo_pontuacao = TipoPontuacao.objects.get(id=1)

    elif tipo == 4: #Tabela de Desafios tipo 4 = envio de desafio


        #Verificar se desafio já existe
        desafio_envio = Aluno_desafio.objects.filter(id=int(envio_data.get("id"))).first()
        if desafio_envio:
            return Response({"message": "Desafio já existente!"}, status=status.HTTP_400_BAD_REQUEST)
        
        desafio = Desafios.objects.get(id=int(envio_data.get("desafio")))
        if not desafio:
            return Response({"message": "Desafio não encontrado!"}, status=status.HTTP_400_BAD_REQUEST)

        
        novo_desafio = Aluno_desafio.objects.create(
            id=int(envio_data.get("id")),
            campeonato=campeonato,
            aluno=aluno,
            desafio=desafio,
            status=envio_data.get("status"),
            texto=envio_data.get("texto", ""),
            data=envio_data.get("data", data_now),
            data_cadastro=envio_data.get("dataCadastro", data_now),
            rastreador_analise=envio_data.get("rastreadorAnalise", 0),
            data_analise=envio_data.get("dataAnalise", data_now),
            status_motivo=envio_data.get("statusMotivo", 0),
            status_comentario=envio_data.get("statusComentario", 0),
            semana=envio_data.get("semana", 0),
            tipo=tipo,
        )
        pontos = Decimal(envio_data.get("pontos"))
        pontos_previsto=0
        tipo_pontuacao = TipoPontuacao.objects.get(id=2)
        novo_desafio.save()
    elif tipo == 3 or tipo == 5: #Tabela de Certificados tipo 3 ou tipo 5 = certificado
        #Verificar se certificado já existe
        certificado = Aluno_certificacao.objects.filter(id=int(envio_data.get("id"))).first()
        if certificado:
            return Response({"message": f"Certificado já existente! - '{envio.descricao}'"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        novo_certificado = Aluno_certificacao.objects.create(
            id=int(envio_data.get("id")),
            campeonato=campeonato,
            aluno=aluno,
            descricao=envio_data.get("descricao", ""),
            data=envio_data.get("data", data_now),
            data_cadastro=envio_data.get("dataCadastro", data_now),
            rastreador_analise=envio_data.get("rastreadorAnalise", 0),
            data_analise=envio_data.get("dataAnalise", data_now),
            status_motivo=envio_data.get("statusMotivo", 0),
            status_comentario=envio_data.get("statusComentario", 0),
            semana=envio_data.get("semana", 0),
            tipo=tipo,
        )
        novo_certificado.save()
        tipo_pontuacao = TipoPontuacao.objects.get(id=3)
        pontos = Decimal(envio_data.get("pontos"))
        pontos_previsto=0

        novo_certificado.save()
    else: #Tipo de envio não encontrado
        return Response({"message": "Tipo de envio não encontrado!"}, status=status.HTTP_400_BAD_REQUEST)

    #Creditar pontuação
    aluno_pontuacao = Aluno_pontuacao.objects.create(
        aluno=aluno,
        campeonato=campeonato,
        tipo_pontuacao=tipo_pontuacao,
        envio=novo_envio,
        desafio=novo_desafio,
        certificacao=novo_certificado,
        descricao=envio_data.get("descricao", ""),
        pontos=pontos,
        pontos_previsto=pontos_previsto,
        data=envio_data.get("data", data_now),
        data_cadastro=envio_data.get("dataCadastro", data_now),
        tipo=tipo,
        status=envio_data.get("status"),
        semana=envio_data.get("semana", 0),
        status_motivo=envio_data.get("statusMotivo", ""),
        status_comentario=envio_data.get("statusComentario", ""),
    )
    aluno_pontuacao.save()

def deletar_aluno_cliente(aluno_data):
    cliente_existente = Aluno_clientes.objects.filter(id=int(aluno_data.get("id"))).first()
    if cliente_existente: 
        cliente_existente.delete()
        return cliente_existente
    else: return None

def deletar_contrato(contrato_data):
    contrato_existente = Aluno_clientes_contratos.objects.filter(id=int(contrato_data.get("id"))).first()
    if contrato_existente: 
        contrato_existente.delete()
        return contrato_existente
    else: return None

def deletar_envio(envio_data):
    tipo = int(envio_data.get("tipo"))
    envio = None
    desafio = None
    certificado = None
    if tipo == 2:
        envio = Aluno_envios.objects.filter(id=int(envio_data.get("id"))).first()
        pontuacao = Aluno_pontuacao.objects.filter(envio=envio)
        contrato_aluno = Aluno_contrato.objects.filter(envio=envio)
        contrato_aluno.delete()
        pontuacao.delete()
        envio.delete()
    elif tipo == 4:
        desafio = Aluno_desafio.objects.filter(id=int(envio_data.get("id"))).first()
        pontuacao = Aluno_pontuacao.objects.filter(desafio=desafio).first()
        pontuacao.delete()
        desafio.delete()

    elif tipo == 3 or tipo == 5:
        certificado = Aluno_certificacao.objects.filter(id=int(envio_data.get("id"))).first()
        pontuacao = Aluno_pontuacao.objects.filter(certificacao=certificado).first()
        pontuacao.delete()
        certificado.delete()

    else:
        return Response({"message": "Tipo de envio não encontrado!"}, status=status.HTTP_400_BAD_REQUEST)
    
def alterar_aluno_cliente(aluno_data):
    cliente_id = int(aluno_data.get("id"))
    
    aluno_cliente = get_object_or_404(Aluno_clientes, id=cliente_id)
    aluno = get_object_or_404(Alunos, id=int(aluno_data.get("aluno")))

    aluno_cliente.aluno = aluno
    aluno_cliente.titulo = aluno_data.get("titulo", aluno_cliente.titulo)
    aluno_cliente.estrangeiro = int(aluno_data.get("estrangeiro", aluno_cliente.estrangeiro))
    aluno_cliente.tipo_cliente = int(aluno_data.get("tipoCliente", aluno_cliente.tipo_cliente)) if aluno_data.get("tipoCliente") else None
    aluno_cliente.tipo_contrato = int(aluno_data.get("tipoContrato", aluno_cliente.tipo_contrato)) if aluno_data.get("tipoContrato") else None
    aluno_cliente.sociedade = int(aluno_data.get("sociedade", aluno_cliente.sociedade)) if aluno_data.get("sociedade") else None
    aluno_cliente.documento = aluno_data.get("documento", aluno_cliente.documento)
    aluno_cliente.telefone = aluno_data.get("telefone", aluno_cliente.telefone)
    aluno_cliente.email = aluno_data.get("email", aluno_cliente.email)
    aluno_cliente.status = int(aluno_data.get("status", aluno_cliente.status))


    aluno_cliente.save()

def alterar_contrato(contrato_data):
    id_contrato = int(contrato_data.get("id"))

    contrato_cliente = get_object_or_404(Aluno_clientes_contratos, id=id_contrato)
    cliente = get_object_or_404(Aluno_clientes, id=int(contrato_data.get("cliente")))

    contrato_cliente.cliente = cliente
    contrato_cliente.tipo_contrato = int(contrato_data.get("tipoContrato", contrato_cliente.tipo_contrato)) if contrato_data.get("tipoContrato") else None
    contrato_cliente.valor_contrato = Decimal(contrato_data.get("valorContrato", "0.00"))
    contrato_cliente.porcentagem_contrato = contrato_data.get("porcentagemContrato")
    contrato_cliente.arquivo1 = contrato_data.get("arquivo1")
    contrato_cliente.semana = int(contrato_data.get("semana", contrato_cliente.semana)) if contrato_data.get("semana") else None
    contrato_cliente.status = int(contrato_data.get("status", contrato_cliente.status))
    contrato_cliente.data_contrato = parse_date(contrato_data.get("dataContrato")) if contrato_data.get("dataContrato") else None
    contrato_cliente.data_vencimento = parse_date(contrato_data.get("dataVencimento")) if contrato_data.get("dataVencimento") else None
    contrato_cliente.data_criacao = parse_datetime(contrato_data.get("dataCriacao")) if contrato_data.get("dataCriacao") else None
    contrato_cliente.motivo_invalido = int(contrato_data.get("motivoInvalido", contrato_cliente.motivo_invalido)) if contrato_data.get("motivoInvalido") else None
    contrato_cliente.descricao_invalido = contrato_data.get("descricaoInvalido")
    contrato_cliente.rastreador_analise = int(contrato_data.get("rastreadorAnalise", contrato_cliente.rastreador_analise)) if contrato_data.get("rastreadorAnalise") else None
    contrato_cliente.analise_data = parse_datetime(contrato_data.get("analiseData")) if contrato_data.get("analiseData") else None
    contrato_cliente.camp_anterior = int(contrato_data.get("campAnterior", contrato_cliente.camp_anterior))
    contrato_cliente.id_camp_anterior = int(contrato_data.get("idCampAnterior", contrato_cliente.id_camp_anterior)) if contrato_data.get("idCampAnterior") else None 

    contrato_cliente.save()

def alterar_envio(envio_data):
    campeonato = get_object_or_404(Campeonato, id=int(envio_data.get("campeonato")))
    aluno = get_object_or_404(Alunos, id=int(envio_data.get("vinculoAluno")))
    tipo = int(envio_data.get("tipo"))
    envio = None
    desafio = None
    certificado = None
    if tipo == 2:
        envio = get_object_or_404(Aluno_envios, id=int(envio_data.get("id")))
        pontuacao = get_object_or_404(Aluno_pontuacao, envio=envio)

        cliente = get_object_or_404(Aluno_clientes, id=int(envio_data.get("vinculoCliente")))
        contrato = get_object_or_404(Aluno_clientes_contratos, id=int(envio_data.get("vinculoContrato")))

        envio.campeonato=campeonato
        envio.aluno=aluno
        envio.cliente=cliente
        envio.contrato=contrato
        envio.data=envio_data.get("data")
        envio.descricao=envio_data.get("descricao")
        envio.valor=envio_data.get("valor")
        envio.arquivo1=envio_data.get("arquivo1")
        envio.arquivo1_motivo=envio_data.get("arquivo1Motivo")
        envio.arquivo1_status=envio_data.get("arquivo1Status")
        envio.data_cadastro=envio_data.get("dataCadastro")
        envio.rastreador_analise=envio_data.get("rastreadorAnalise")
        envio.data_analise=envio_data.get("dataAnalise")
        envio.status=envio_data.get("status")
        envio.status_motivo=envio_data.get("statusMotivo")
        envio.status_comentario=envio_data.get("statusComentario")
        envio.semana=envio_data.get("semana")
        envio.tipo=tipo

        envio.save()
        tipo_pontuacao = TipoPontuacao.objects.get(id=1)

        if int(envio_data.get("status")) == 3:
            contagem_contratos = cliente.cliente_aluno_contrato.count()
            print("Numero de contratos:", contagem_contratos)
            if contagem_contratos == 0:
                print("Criando novo contrato")
                if contrato.tipo_contrato == 2:
                    valor_inicial = float(envio_data.get("valor"))
                    
                    valor_final = valor_inicial * 0.1

                    pontos = int(gera_pontos_contrato(valor_final))
                    contrato.valor_contrato = valor_final
                    contrato.save()
                else:
                    valor_final = float(envio_data.get("valor"))
                    pontos = gera_pontos_contrato(float(envio_data.get("valor")))




                print("Pontos do contrato:", pontos)
                Aluno_contrato_novo = Aluno_contrato.objects.create(
                    campeonato=campeonato, 
                    aluno=aluno, cliente=cliente, 
                    contrato=contrato, 
                    envio=envio, 
                    descricao=envio_data.get("descricao"), 
                    valor=contrato.valor_contrato, 
                    data=envio_data.get("data"),
                    data_cadastro=envio_data.get("dataCadastro"), 
                    pontos=pontos)
                
                Aluno_contrato_novo.save()


    elif tipo == 4:
        desafio = get_object_or_404(Aluno_desafio, id=int(envio_data.get("id")))
        pontuacao = get_object_or_404(Aluno_pontuacao, desafio=desafio)


        desafio_de_fato = get_object_or_404(Desafios, id=int(envio_data.get("desafio")))

        desafio.campeonato=campeonato
        desafio.aluno=aluno
        desafio.desafio=desafio_de_fato
        desafio.status=envio_data.get("status")
        desafio.texto=envio_data.get("texto")
        desafio.data=envio_data.get("data")
        desafio.data_cadastro=envio_data.get("dataCadastro")
        desafio.rastreador_analise=envio_data.get("rastreadorAnalise")
        desafio.data_analise=envio_data.get("dataAnalise")
        desafio.status_motivo=envio_data.get("statusMotivo")
        desafio.status_comentario=envio_data.get("statusComentario")
        desafio.semana=envio_data.get("semana")
        desafio.tipo=tipo

        desafio.save()
        tipo_pontuacao = TipoPontuacao.objects.get(id=2)
    elif tipo == 3 or tipo == 5:
        certificado = get_object_or_404(Aluno_certificacao, id=int(envio_data.get("id")))
        pontuacao = get_object_or_404(Aluno_pontuacao, certificacao=certificado)

        certificado.campeonato=campeonato
        certificado.aluno=aluno
        certificado.descricao=envio_data.get("descricao")
        certificado.data=envio_data.get("data")
        certificado.data_cadastro=envio_data.get("dataCadastro")
        certificado.rastreador_analise=envio_data.get("rastreadorAnalise")
        certificado.data_analise=envio_data.get("dataAnalise")
        certificado.status_motivo=envio_data.get("statusMotivo")
        certificado.status_comentario=envio_data.get("statusComentario")
        certificado.semana=envio_data.get("semana")
        certificado.tipo=tipo

        certificado.save()
        tipo_pontuacao = TipoPontuacao.objects.get(id=3)
    else:
        return Response({"message": "Tipo de envio não encontrado!"}, status=status.HTTP_400_BAD_REQUEST)

    #Creditar pontuação
    
    pontuacao.aluno=aluno
    pontuacao.campeonato=campeonato
    pontuacao.tipo_pontuacao=tipo_pontuacao
    pontuacao.envio=envio
    pontuacao.desafio=desafio
    pontuacao.certificacao=certificado
    pontuacao.descricao=envio_data.get("descricao")
    pontuacao.data=envio_data.get("data")
    pontuacao.data_cadastro=envio_data.get("dataCadastro")
    pontuacao.tipo=tipo
    pontuacao.status=envio_data.get("status")
    pontuacao.semana=envio_data.get("semana")
    pontuacao.status_motivo=envio_data.get("statusMotivo")
    pontuacao.status_comentario=envio_data.get("statusComentario")

    if tipo == 5:
        pontuacao.pontos=Decimal(envio_data.get("pontos"))
        pontuacao.pontos_previsto=Decimal(envio_data.get("pontosPreenchidos"))

    pontuacao.save()

@login_required
def listar_logs(request):
    logs_list = Log.objects.order_by('-criado_em')
    
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    if query:
        logs_list = logs_list.filter(tabela__icontains=query)

    if status_filter in ['sucesso', 'erro']:
        logs_list = logs_list.filter(status=status_filter)

    paginator = Paginator(logs_list, 50)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    return render(request, 'logs/logs.html', {'logs': logs, 'query': query, 'status_filter': status_filter})

@login_required
def detalhes_log(request, log_id):
    log = Log.objects.get(id=log_id)
    return render(request, 'logs/detalhes_log.html', {'log': log})

@api_view(['POST'])
def receber_dados(request):
    data = request.data
    if not data:
        return Response({"message": "Dados não foram enviados!"}, status=status.HTTP_400_BAD_REQUEST)

    acao = data.get('acao')
    if not acao:
        return Response({"message": "Nenhuma ação encontrada!"}, status=status.HTTP_400_BAD_REQUEST)

    lista_tabelas = data.get('tabela', '').split(',')
    registro_atual = data.get('registroAtual', {})

    for tabela in lista_tabelas:
        if tabela in registro_atual:
            try:
                if acao == 'add':
                    registrar_log(acao, tabela, dados_novos=registro_atual[tabela], dados_geral=data)  # Log antes da operação
                    if tabela == 'alunosClientes':
                        criar_aluno_cliente(registro_atual['alunosClientes'])
                    elif tabela == 'alunosClientesContratos':
                        criar_contrato(registro_atual['alunosClientesContratos'])
                    elif tabela == 'alunosEnvios':
                        criar_envio(registro_atual['alunosEnvios'])

                elif acao == 'alt':
                    dados_anteriores = {}  # Buscar os dados antes da alteração, se necessário
                    registrar_log(acao, tabela, dados_anteriores=dados_anteriores, dados_novos=registro_atual[tabela], dados_geral=data)
                    if tabela == 'alunosClientes':
                        alterar_aluno_cliente(registro_atual['alunosClientes'])
                    elif tabela == 'alunosClientesContratos':
                        alterar_contrato(registro_atual['alunosClientesContratos'])
                    elif tabela == 'alunosEnvios':
                        alterar_envio(registro_atual['alunosEnvios'])

                elif acao == 'del':
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_geral=data)
                    if tabela == 'alunosClientes':
                        deletar_aluno_cliente(registro_atual['alunosClientes'])
                    elif tabela == 'alunosClientesContratos':
                        deletar_contrato(registro_atual['alunosClientesContratos'])
                    elif tabela == 'alunosEnvios':
                        deletar_envio(registro_atual['alunosEnvios'])

            except Exception as e:
                registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], status='erro', erro=str(e), dados_geral=data)
                return Response({"message": f"Erro ao processar {tabela}: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Operação concluída!"}, status=status.HTTP_200_OK)

    
