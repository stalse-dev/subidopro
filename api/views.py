from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from rest_framework import status
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime, parse_date
from subidometro.models import *
from subidometro.utils import *
from django.db.models import Sum, Count, Func, CharField, IntegerField, Max, Q, Case, When
from django.db.models.functions import TruncMonth, TruncWeek, Cast
from api.models import Log
from api.utils import registrar_log
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from collections import defaultdict
from .serializers import *
import calendar
from django.utils.timezone import localtime
from django.utils.timezone import make_aware, is_naive
from datetime import datetime
import hashlib


def union_pontuacao(aluno, campeonato):
    envios = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato).annotate(
        desafio_id=Value(None, output_field=IntegerField()),
    ).values(
        "id", "aluno_id", "campeonato_id", "descricao", "data", "data_cadastro", 
        "pontos", "pontos_previsto", "desafio_id", "tipo"
    )

    desafios = Aluno_desafio.objects.filter(aluno=aluno, campeonato=campeonato).values(
        "id", "aluno_id", "campeonato_id", "descricao", "data", "data_cadastro", 
        "pontos", "pontos_previsto", "desafio_id", "tipo"
    )

    certificacao = Aluno_certificacao.objects.filter(aluno=aluno, campeonato=campeonato).annotate(
        desafio_id=Value(None, output_field=IntegerField())
    ).values(
        "id", "aluno_id", "campeonato_id", "descricao", "data", "data_cadastro", 
        "pontos", "pontos_previsto", "desafio_id", "tipo"
    )


    return envios.union(desafios, certificacao).order_by("-data_cadastro")

def mapear_status(status):
    status_dict = {
        0: "pendente",
        1: "aprovado",
        2: "invalidado",
    }
    return status_dict.get(status, "desconhecido")

def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

def gera_pontos(valor):
    """Calcula a pontuação com base no valor informado."""
    valor = float(valor)  # Garante que o valor seja float antes do cálculo
    return int((valor // 100) * 10)  # Usa divisão normal

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
        cliente = get_object_or_404(Aluno_clientes, id=int(envio_data.get("vinculoCliente")))
        contrato = get_object_or_404(Aluno_clientes_contratos, id=int(envio_data.get("vinculoContrato")))

        envio = Aluno_envios.objects.filter(id=int(envio_data.get("id"))).first()
        if envio:
            return Response({"message": f"Envio já existente! - '{envio.descricao}'"}, status=status.HTTP_400_BAD_REQUEST)
    

        data = envio_data.get("data")

        data_formatada = make_aware(datetime.strptime(data, "%Y-%m-%d"))
        data_limite = make_aware(datetime(2025, 3, 1))

        if data_formatada > data_limite:
            if contrato.tipo_contrato == 2:
                valor_inicial = float(envio_data.get("valorPreenchido"))
                valor_minimo = valor_inicial * 0.1
                pontos = gera_pontos(valor_minimo)
                pontos_previsto = pontos
                valor_calculado = valor_minimo 
            else:
                pontos = gera_pontos(float(envio_data.get("valorPreenchido")))
                pontos_previsto = pontos
                valor_calculado = float(envio_data.get("valorPreenchido")) 
        else:
            pontos = 0
            pontos_previsto = 0
            valor_calculado = float(envio_data.get("valorPreenchido"))  
                
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
            valor=envio_data.get("valorPreenchido"),
            valor_calculado=valor_calculado,
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
            pontos=pontos,
            pontos_previsto=pontos_previsto
        )
        novo_envio.save()


        #### validar pontos de contrato
        contagem_contratos = cliente.cliente_aluno_contrato.count()
        if contagem_contratos == 0:
            data_limite = make_aware(datetime(2025, 3, 1))
            if cliente.data_criacao > data_limite:
                if contrato.tipo_contrato == 2:
                    valor_inicial = float(envio_data.get("valorPreenchido"))
                    
                    valor_final = valor_inicial * 0.1

                    pontos = int(gera_pontos_contrato(valor_final))
                    contrato.valor_contrato = valor_final
                    contrato.save()
                else:
                    valor_final = float(envio_data.get("valorPreenchido"))
                    pontos = gera_pontos_contrato(float(envio_data.get("valor")))

                Aluno_contrato_novo = Aluno_contrato.objects.create(
                    campeonato=campeonato, 
                    aluno=aluno, cliente=cliente, 
                    contrato=contrato, 
                    envio=novo_envio, 
                    descricao=envio_data.get("descricao"), 
                    valor=envio_data.get("valorPreenchido"), 
                    data=envio_data.get("data"),
                    data_cadastro=envio_data.get("dataCadastro"), 
                    pontos=pontos, status=0)
                
                Aluno_contrato_novo.save()

    elif tipo == 4: #Tabela de Desafios tipo 4 = envio de desafio


        #Verificar se desafio já existe
        desafio_envio = Aluno_desafio.objects.filter(id=int(envio_data.get("id"))).first()
        if desafio_envio:
            return Response({"message": "Desafio já existente!"}, status=status.HTTP_400_BAD_REQUEST)
        
        desafio = Desafios.objects.get(id=int(envio_data.get("desafio")))
        if not desafio:
            return Response({"message": "Desafio não encontrado!"}, status=status.HTTP_400_BAD_REQUEST)
        
        pontos = Decimal(envio_data.get("pontos"))
        pontos_previsto=0

        novo_desafio = Aluno_desafio.objects.create(
            id=int(envio_data.get("id")),
            campeonato=campeonato,
            aluno=aluno,
            desafio=desafio,
            descricao=envio_data.get("descricao", ""),
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
            pontos=pontos,
            pontos_previsto=pontos_previsto
        )

        novo_desafio.save()
    elif tipo == 3 or tipo == 5: #Tabela de Certificados tipo 3 ou tipo 5 = certificado
        #Verificar se certificado já existe
        certificado = Aluno_certificacao.objects.filter(id=int(envio_data.get("id"))).first()
        if certificado:
            return Response({"message": f"Certificado já existente! - '{envio.descricao}'"}, status=status.HTTP_400_BAD_REQUEST)
        
        pontos = Decimal(envio_data.get("pontos"))
        pontos_previsto=0
        
        
        novo_certificado = Aluno_certificacao.objects.create(
            id=int(envio_data.get("id")),
            campeonato=campeonato,
            aluno=aluno,
            descricao=envio_data.get("descricao", ""),
            data=envio_data.get("data", data_now),
            data_cadastro=envio_data.get("dataCadastro", data_now),
            rastreador_analise=envio_data.get("rastreadorAnalise", 0),
            data_analise=envio_data.get("dataAnalise", data_now),
            status=envio_data.get("status", 0),
            status_motivo=envio_data.get("statusMotivo", 0),
            status_comentario=envio_data.get("statusComentario", 0),
            semana=envio_data.get("semana", 0),
            tipo=tipo,
            pontos=pontos,
            pontos_previsto=pontos_previsto
        )

        

        novo_certificado.save()
    else: #Tipo de envio não encontrado
        return Response({"message": "Tipo de envio não encontrado!"}, status=status.HTTP_400_BAD_REQUEST)

def criar_aluno_subidometro(aluno_data):
    # Validar se aluno existe
    aluno = get_object_or_404(Alunos, id=int(aluno_data.get("aluno")))
    campeonato = get_object_or_404(Campeonato, id=int(aluno_data.get("campeonato")))
    cla = get_object_or_404(Mentoria_cla, id=int(aluno_data.get("cla")))

    novo_aluno_subidometro = Alunos_Subidometro.objects.create(
        id=int(aluno_data.get("id")),
        campeonato=campeonato,
        aluno=aluno,
        cla=cla,
        data=aluno_data.get("data"),
        semana=aluno_data.get("semana"),
        nivel=aluno_data.get("nivel"),
        nivel_motivo=aluno_data.get("nivelMotivo"),
        nivel_comentario=aluno_data.get("nivelComentario"),
        envios=aluno_data.get("envios"),
        cliente=aluno_data.get("cliente"),
        faturamento=aluno_data.get("faturamento"),
        faturamento_valor=aluno_data.get("faturamentoValor"),
        pontos=aluno_data.get("pontos"),
        pontuacao_geral=aluno_data.get("pontuacaoGeral"),
        pontuacao_cla=aluno_data.get("pontuacaoCla"),
        rastreador=aluno_data.get("rastreador"),
        status_aluno=aluno_data.get("statusAluno"),
    )
    
    novo_aluno_subidometro.save()
    return novo_aluno_subidometro

def criar_aluno(aluno_data):
    aluno = Alunos.objects.filter(id=int(aluno_data.get("id"))).first()
    if aluno:
        return Response({"message": f"Aluno já existente! - '{aluno.nome}'"}, status=status.HTTP_400_BAD_REQUEST)
    
    cla = get_object_or_404(Mentoria_cla, id=int(aluno_data.get("cla")))

    novo_aluno = Alunos.objects.create(
        id=int(aluno_data.get("id")),
        cla=cla,
        nome_completo=aluno_data.get("nomeCompleto"),
        nome_social=aluno_data.get("nomeSocial"),
        apelido=aluno_data.get("apelido"),
        email=aluno_data.get("email"),
        data_criacao=parse_datetime(aluno_data.get("dataCriacao")) if aluno_data.get("dataCriacao") else None,
        status=aluno_data.get("status"),
        hotmart=aluno_data.get("hotmart"),
        termo_aceito=aluno_data.get("termoAceito"),
        nivel=aluno_data.get("nivel"),
        aluno_consultor=aluno_data.get("alunoConsultor"),
        tags_interna=aluno_data.get("tagsInterna"),
 
    )
    
    novo_aluno.save()
    return novo_aluno

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
        contrato_aluno = Aluno_contrato.objects.filter(envio=envio)
        contrato_aluno.delete()
        envio.delete()
    elif tipo == 4:
        desafio = Aluno_desafio.objects.filter(id=int(envio_data.get("id"))).first()
        desafio.delete()

    elif tipo == 3 or tipo == 5:
        certificado = Aluno_certificacao.objects.filter(id=int(envio_data.get("id"))).first()
        certificado.delete()

    else:
        return Response({"message": "Tipo de envio não encontrado!"}, status=status.HTTP_400_BAD_REQUEST)

def deletar_aluno_subidometro(aluno_data):
    aluno_subidometro = Alunos_Subidometro.objects.filter(id=int(aluno_data.get("id"))).first()
    if aluno_subidometro: 
        aluno_subidometro.delete()
        return aluno_subidometro
    else: return None

def deletar_aluno(aluno_data):
    aluno = Alunos.objects.filter(id=int(aluno_data.get("id"))).first()
    if aluno: 
        #aluno.delete()
        return aluno
    else: return None

def alterar_aluno_cliente(aluno_data):
    cliente_id = int(aluno_data.get("id"))
    
    aluno_cliente = get_object_or_404(Aluno_clientes, id=cliente_id)
    aluno = get_object_or_404(Alunos, id=int(aluno_data.get("aluno")))
    novo_status = int(aluno_data.get("status"))
    #Validar alteração de Status
    if aluno_cliente.status != novo_status:
        if novo_status == 2:
            envios_alterados = Aluno_envios.objects.filter(cliente=aluno_cliente)
            contratos_alterados = Aluno_clientes_contratos.objects.filter(cliente=aluno_cliente)
            
            retencoes = Alunos_clientes_pontos_meses_retencao.objects.filter(cliente=aluno_cliente)
            for retencao in retencoes:
                retencao.delete()

            for envio in envios_alterados:
                envio.status = 2
                envio.pontos = 0
                envio.save()

            for contrato in contratos_alterados:
                contrato.status = 2
                contrato.save()
            
            contratos = Aluno_contrato.objects.filter(cliente=aluno_cliente)
            for contrato in contratos:
                print('Invalidou o contrato ', contrato)
                contrato.status = 2
                contrato.save()

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

    novo_tipo = int(contrato_data.get("tipoContrato"))
    if contrato_cliente.tipo_contrato != novo_tipo:
        envios = Aluno_envios.objects.filter(contrato=contrato_cliente).order_by('-data_cadastro')
        if novo_tipo == 2:
            if envios.exists():
                for envio in envios:
                    #Apenas ajustar a data maior que data 01/03/2025
                    if envio.data > datetime(2025, 3, 1).date():
                        valor_inicial = float(envio.valor)
                        valor_minimo = valor_inicial * 0.1
                        pontos = gera_pontos(valor_minimo)
                        envio.pontos = pontos
                        envio.pontos_previsto = pontos
                        envio.valor_calculado = valor_minimo # atribuir o valor calculado 
                        envio.save()
                        
                    else:
                        valor_inicial = float(envio.valor)
                        valor_minimo = valor_inicial * 0.1
                        pontos = 0
                        envio.pontos = pontos
                        envio.pontos_previsto = pontos
                        envio.valor_calculado = valor_minimo
                        envio.save()
        else:
            if envios.exists():
                for envio in envios:
                    if envio.data > datetime(2025, 3, 1).date():
                        valor_inicial = float(envio.valor)
                        pontos = gera_pontos(valor_inicial)
                        envio.pontos = pontos
                        envio.pontos_previsto = pontos
                        envio.valor_calculado = valor_inicial # atribuir o valor calculado
                        envio.save()
                    else:
                        pontos = 0
                        envio.pontos = pontos
                        envio.pontos_previsto = pontos
                        envio.valor_calculado = envio.valor
                        envio.save()

    novo_status = int(contrato_data.get("status"))
    #Validar alteração de Status
    if contrato_cliente.status != novo_status:
        if int(contrato_data.get("status")) == 2:
            envios_alterados = Aluno_envios.objects.filter(contrato=contrato_cliente)
            for envio in envios_alterados:
                envio.status = 2
                envio.pontos = 0
                envio.save()
                
            retencoes = Alunos_clientes_pontos_meses_retencao.objects.filter(contrato=contrato_cliente)
            for retencao in retencoes:
                retencao.delete()
            
            contratos = Aluno_contrato.objects.filter(contrato=contrato_cliente)
            for contrato in contratos:
                contrato.status = 2
                contrato.save()

    contrato_cliente.cliente = cliente
    contrato_cliente.tipo_contrato = int(contrato_data.get("tipoContrato", contrato_cliente.tipo_contrato)) if contrato_data.get("tipoContrato") else None
    contrato_cliente.valor_contrato = Decimal(contrato_data.get("valorContrato") or "0.00")
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
        cliente = get_object_or_404(Aluno_clientes, id=int(envio_data.get("vinculoCliente")))
        contrato = get_object_or_404(Aluno_clientes_contratos, id=int(envio_data.get("vinculoContrato")))

        if float(envio.valor) != float(envio_data.get("valor")):
            if envio.data > datetime(2025, 3, 1).date():
                if contrato.tipo_contrato == 2:
                    valor_inicial = float(envio_data.get("valor"))
                    valor_minimo = valor_inicial * 0.1
                    pontos = gera_pontos(valor_minimo)
                    pontos_previsto = pontos
                    valor_calculado = valor_minimo
                else:
                    pontos = gera_pontos(float(envio_data.get("valor")))
                    pontos_previsto = pontos
                    valor_calculado = float(envio_data.get("valor"))
            else:
                if contrato.tipo_contrato == 2:
                    valor_inicial = float(envio_data.get("valor"))
                    valor_minimo = valor_inicial * 0.1
                    pontos = 0
                    pontos_previsto = 0
                    valor_calculado = valor_minimo
                else:
                    pontos = 0
                    pontos_previsto = 0
                    valor_calculado = float(envio_data.get("valor"))
        else:
            pontos = envio.pontos
            pontos_previsto = envio.pontos_previsto
            valor_calculado = envio.valor_calculado
        
        novo_status = int(envio_data.get("status"))

        if envio.status != novo_status:
            if novo_status == 2:
                pontos = 0
            elif novo_status == 3 and envio.status == 2:
                if envio.data > datetime(2025, 3, 1).date():
                    if contrato.tipo_contrato == 2:
                        valor_inicial = float(envio_data.get("valor"))
                        valor_minimo = valor_inicial * 0.1
                        pontos = gera_pontos(valor_minimo)
                        pontos_previsto = pontos
                        valor_calculado = valor_minimo
                    else:
                        pontos = gera_pontos(float(envio_data.get("valor")))
                        pontos_previsto = pontos
                        valor_calculado = float(envio_data.get("valor"))
                else:
                    if contrato.tipo_contrato == 2:
                        valor_inicial = float(envio_data.get("valor"))
                        valor_minimo = valor_inicial * 0.1
                        pontos = 0
                        pontos_previsto = 0
                        valor_calculado = valor_minimo
                    else:
                        pontos = 0
                        pontos_previsto = 0
                        valor_calculado = float(envio_data.get("valor"))

        

        envio.campeonato=campeonato
        envio.aluno=aluno
        envio.cliente=cliente
        envio.contrato=contrato
        envio.data=envio_data.get("data")
        envio.descricao=envio_data.get("descricao")
        envio.valor=envio_data.get("valor")
        envio.valor_calculado=valor_calculado
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
        envio.pontos=pontos
        envio.pontos_previsto=pontos_previsto



        if envio_data.get("acaoRastreador"):
            envio.pontos=envio_data.get("pontos")
            envio.pontos_previsto=envio_data.get("pontosPreenchidos")

        envio.save()
        
        #Aprovar pontos de contrato se existir
        if int(envio_data.get("status")) == 3:
            aluno_contrato = Aluno_contrato.objects.filter(cliente=cliente).first()
            if aluno_contrato:
                aluno_contrato.status = 3
                aluno_contrato.save()
        
        if int(envio_data.get("status")) == 2:
            pontos = 0
                
    elif tipo == 4:
        desafio = get_object_or_404(Aluno_desafio, id=int(envio_data.get("id")))
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
        desafio.pontos=Decimal(envio_data.get("pontos"))
        desafio.save()
    elif tipo == 3 or tipo == 5:
        certificado = get_object_or_404(Aluno_certificacao, id=int(envio_data.get("id")))
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
        certificado.pontos=Decimal(envio_data.get("pontos"))
        certificado.pontos_previsto=Decimal(envio_data.get("pontosPreenchidos"))

        certificado.save()
    else:
        return Response({"message": "Tipo de envio não encontrado!"}, status=status.HTTP_400_BAD_REQUEST)

def alterar_aluno_subidometro(aluno_data):
    aluno_subidometro = get_object_or_404(Alunos_Subidometro, id=int(aluno_data.get("id")))
    aluno = get_object_or_404(Alunos, id=int(aluno_data.get("aluno")))
    cla = get_object_or_404(Mentoria_cla, id=int(aluno_data.get("cla")))
    campeonato = get_object_or_404(Campeonato, id=int(aluno_data.get("campeonato")))

    aluno_subidometro.campeonato=campeonato
    aluno_subidometro.aluno=aluno 
    aluno_subidometro.cla=cla
    aluno_subidometro.data=aluno_data.get("data")
    aluno_subidometro.semana=aluno_data.get("semana")
    aluno_subidometro.nivel=aluno_data.get("nivel")
    aluno_subidometro.nivel_motivo=aluno_data.get("nivelMotivo")
    aluno_subidometro.nivel_comentario=aluno_data.get("nivelComentario")
    aluno_subidometro.envios=aluno_data.get("envios")
    aluno_subidometro.cliente=aluno_data.get("cliente")
    aluno_subidometro.faturamento=aluno_data.get("faturamento")
    aluno_subidometro.faturamento_valor=aluno_data.get("faturamentoValor")
    aluno_subidometro.pontuacao_geral=aluno_data.get("pontuacaoGeral")
    aluno_subidometro.pontuacao_cla=aluno_data.get("pontuacaoCla")
    aluno_subidometro.rastreador=aluno_data.get("rastreador")
    aluno_subidometro.status_aluno=aluno_data.get("statusAluno")
    aluno_subidometro.save()

    return aluno_subidometro
    
def alterar_aluno(aluno_data):
    aluno = get_object_or_404(Alunos, id=int(aluno_data.get("id")))
    cla = get_object_or_404(Mentoria_cla, id=int(aluno_data.get("cla")))

    aluno.cla=cla
    aluno.nome_completo=aluno_data.get("nomeCompleto")
    aluno.nome_social=aluno_data.get("nomeSocial")
    aluno.apelido=aluno_data.get("apelido")
    aluno.email=aluno_data.get("email")
    aluno.data_criacao=parse_datetime(aluno_data.get("dataCriacao")) if aluno_data.get("dataCriacao") else None
    aluno.status=aluno_data.get("status")
    aluno.hotmart=aluno_data.get("hotmart")
    aluno.termo_aceito=aluno_data.get("termoAceito")
    aluno.nivel=aluno_data.get("nivel")
    aluno.aluno_consultor=aluno_data.get("alunoConsultor")
    aluno.tags_interna=aluno_data.get("tagsInterna")

    aluno.save()

def obter_tipo_descricao(tipo):
    tipos = {
        2: "Recebimento",
        3: "Certificação",
        4: "Desafio",
        5: "Manual"
    }
    return tipos.get(tipo, "Desconhecido")

def obter_status_descricao(status):
    status_dict = {
        0: "pendente",
        1: "analisando",
        2: "invalido",
        3: "validado"
    }
    return status_dict.get(status, "Desconhecido")

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
           # try:
            if acao == 'add':
                if tabela == 'alunosClientes':
                    registrar_log(acao, tabela, dados_novos=registro_atual[tabela], dados_geral=data)  # Log antes da operação
                    criar_aluno_cliente(registro_atual['alunosClientes'])
                elif tabela == 'alunosClientesContratos':
                    registrar_log(acao, tabela, dados_novos=registro_atual[tabela], dados_geral=data)  # Log antes da operação
                    criar_contrato(registro_atual['alunosClientesContratos'])
                elif tabela == 'alunosEnvios':
                    registrar_log(acao, tabela, dados_novos=registro_atual[tabela], dados_geral=data)  # Log antes da operação
                    criar_envio(registro_atual['alunosEnvios'])
                else:
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], status='erro', erro=f"Tabela {tabela} não encontrada!", dados_geral=data)
                    print("Tabela não encontrada!")
                

            elif acao == 'alt':
                if tabela == 'alunosClientes':
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_novos=registro_atual[tabela], dados_geral=data)
                    alterar_aluno_cliente(registro_atual['alunosClientes'])
                elif tabela == 'alunosClientesContratos':
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_novos=registro_atual[tabela], dados_geral=data)
                    alterar_contrato(registro_atual['alunosClientesContratos'])
                elif tabela == 'alunosEnvios':
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_novos=registro_atual[tabela], dados_geral=data)
                    alterar_envio(registro_atual['alunosEnvios'])
                else:
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], status='erro', erro=f"Tabela {tabela} não encontrada!", dados_geral=data)
                    print("Tabela não encontrada!")

            elif acao == 'del':
                
                if tabela == 'alunosClientes':
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_geral=data)
                    deletar_aluno_cliente(registro_atual['alunosClientes'])
                elif tabela == 'alunosClientesContratos':
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_geral=data)
                    deletar_contrato(registro_atual['alunosClientesContratos'])
                elif tabela == 'alunosEnvios':
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_geral=data)
                    deletar_envio(registro_atual['alunosEnvios'])
                else:
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], status='erro', erro=f"Tabela {tabela} não encontrada!", dados_geral=data)
                    print("Tabela não encontrada!")

            # except Exception as e:
            #     registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], status='erro', erro=str(e), dados_geral=data)
            #     print(f"Erro ao processar {tabela}: {str(e)}")
            #     return Response({"message": f"Erro ao processar {tabela}: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Operação concluída!"}, status=status.HTTP_200_OK)

@api_view(['POST'])
def dados_subdometro(request):
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
                    if tabela == 'alunosSubidometro':
                        registrar_log(acao, tabela, dados_novos=registro_atual[tabela], dados_geral=data)  # Log antes da operação
                        criar_aluno_subidometro(registro_atual['alunosSubidometro'])
                elif acao == 'alt':
                    if tabela == 'alunosSubidometro':
                        registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_novos=registro_atual[tabela], dados_geral=data)
                        alterar_aluno_subidometro(registro_atual['alunosSubidometro'])
                elif acao == 'del':
                    if tabela == 'alunosSubidometro':
                        registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_geral=data)
                        deletar_aluno_subidometro(registro_atual['alunosSubidometro'])
                else:
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], status='erro', erro=f"Tabela {tabela} não encontrada!", dados_geral=data)
                    print("Tabela não encontrada!")
            except Exception as e:
                registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], status='erro', erro=str(e), dados_geral=data)
                return Response({"message": f"Erro ao processar {tabela}: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Operação concluída!"}, status=status.HTTP_200_OK)

@api_view(['POST'])       
def dados_alunos(request):
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
            #try:
            if acao == 'add':
                if tabela == 'alunos':
                    registrar_log(acao, tabela, dados_novos=registro_atual[tabela], dados_geral=data)  # Log antes da operação
                    criar_aluno(registro_atual['alunos'])
            elif acao == 'alt':
                if tabela == 'alunos':
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_novos=registro_atual[tabela], dados_geral=data)
                    alterar_aluno(registro_atual['alunos'])
            elif acao == 'del':
                if tabela == 'alunos':
                    registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], dados_geral=data)
                    deletar_aluno(registro_atual['alunos'])
            else:
                registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], status='erro', erro=f"Tabela {tabela} não encontrada!", dados_geral=data)
                print("Tabela não encontrada!")
            # except Exception as e:
            #     registrar_log(acao, tabela, dados_anteriores=registro_atual[tabela], status='erro', erro=str(e), dados_geral=data)
            #     return Response({"message": f"Erro ao processar {tabela}: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Operação concluída!"}, status=status.HTTP_200_OK)

@api_view(['GET'])
def recebimentos_alunos(request, aluno_id):
    Campeonato, semana = calcular_semana_vigente()
    aluno = get_object_or_404(Alunos, id=int(aluno_id))

    pontos_campeonato = Alunos_posicoes_semana.objects.filter(aluno=aluno, campeonato=Campeonato, semana=semana).first()

    if pontos_campeonato:
        pontos_desafio = int(round(pontos_campeonato.pontos_desafio or 0))
        pontos_certificacao = int(round(pontos_campeonato.pontos_certificacao or 0))
        pontos_contrato = int(round(pontos_campeonato.pontos_contrato or 0))
        pontos_retencao = int(round(pontos_campeonato.pontos_retencao or 0))
    else:
        pontos_retencao = 0


    # Filtra os pontos por categoria
    pontuacoes = {
        "recebimentos": Aluno_envios.objects.filter(aluno=aluno, campeonato=Campeonato, status=3).order_by('-data_cadastro'),
        "desafios": Aluno_desafio.objects.filter(aluno=aluno, campeonato=Campeonato, status=3).order_by('-data_cadastro'),
        "certificacoes": Aluno_certificacao.objects.filter(aluno=aluno, tipo=3, campeonato=Campeonato, status=3).order_by('-data_cadastro'),
        "contratos": Aluno_contrato.objects.filter(aluno=aluno, pontos__gt=0, campeonato=Campeonato, status=3).order_by('-data_cadastro'),
        "retencao": Alunos_clientes_pontos_meses_retencao.objects.filter(aluno=aluno, campeonato=Campeonato).order_by('-data')
    }

    resultado = {
        "recebimentos": defaultdict(lambda: {"infos": {"data": "", "valorTotal": "R$ 0,00", "pontos": "0"}, "itens": []}),
        "desafios": {"infos": {"titulo": "DESAFIOS", "pontos": "0"}, "itens": []},
        "certificacoes": {"infos": {"titulo": "CERTIFICAÇÕES", "pontos": "0"}, "itens": []},
        "contratos": {"infos": {"titulo": "CONTRATOS", "pontos": "0"}, "itens": []},
        "retencao": {"infos": {"titulo": "RETENCÃO", "pontos": "0"}, "itens": []}
    }

    resumo_mensal = defaultdict(lambda: {"valorTotal": 0, "pontos": 0})

    for categoria, pontuacao_lista in pontuacoes.items():
        for pontuacao in pontuacao_lista:
            

            if categoria not in ["contratos", "retencao"]:
                if pontuacao.status == 0:
                    status = "Não analisado"
                elif pontuacao.status == 1:
                    status = "Pendente de análise"
                elif pontuacao.status == 2:
                    status = "Invalidado"
                elif pontuacao.status == 3:
                    status = "Validado"
                else:
                    status = "Sem status"
            else:
                status = "Sem status"

            if categoria == "recebimentos":
                if pontuacao.semana == semana + 1:
                    continue
                data_formatada = pontuacao.data_cadastro.strftime('%d/%m/%Y') if pontuacao.data_cadastro else ""
                data_formatada_data = pontuacao.data.strftime('%d/%m/%Y') if pontuacao.data else ""
                nome_mes = pontuacao.data.strftime('%B').upper() if pontuacao.data else ""
                mes_ano = pontuacao.data.strftime('%Y-%m') if pontuacao.data else "sem-data"

                item = {
                    "id": pontuacao.id,
                    "dataCriacao": data_formatada,
                    "data": data_formatada_data,
                    "descricao": pontuacao.descricao or "",
                    "valor": f"R$ {float(pontuacao.valor):.2f}",
                    "pontosEfetivos": str(int(pontuacao.pontos)),
                    "pontosPreenchidos": str(int(pontuacao.pontos_previsto or pontuacao.pontos)),
                    "arquivo1": str(pontuacao.arquivo1 or ""),
                    "statusStr": str(status),
                    "status": pontuacao.status,
                    "semana": pontuacao.semana
                }

                if pontuacao.status == 3:
                    resumo_mensal[mes_ano]["valorTotal"] += float(pontuacao.valor)
                    
                    # Soma os pontos normalmente
                    resumo_mensal[mes_ano]["pontos"] += int(pontuacao.pontos)

                    # Limita os pontos a no máximo 3000
                    resumo_mensal[mes_ano]["pontos"] = min(resumo_mensal[mes_ano]["pontos"], 3000)

                resultado[categoria][mes_ano]["infos"]["dataCriacao"] = f"{nome_mes} {pontuacao.data.year}"
                resultado[categoria][mes_ano]["itens"].append(item)

            elif categoria == "desafios":
                data_formatada = pontuacao.data_cadastro.strftime('%d/%m/%Y') if pontuacao.data_cadastro else ""
                item = {
                    "id": pontuacao.id,
                    "dataCriacao": data_formatada,
                    "descricao": pontuacao.desafio.titulo or "",
                    "pontosEfetivos": str(int(pontuacao.pontos)),
                    "pontosPreenchidos": str(int(pontuacao.pontos_previsto or pontuacao.pontos)),
                    "statusStr": str(status),
                    "status": pontuacao.status,
                    "semana": pontuacao.semana
                }

                resultado[categoria]["itens"].append(item)

            elif categoria == "certificacoes":
                data_formatada = pontuacao.data_cadastro.strftime('%d/%m/%Y') if pontuacao.data_cadastro else ""
                item = {
                    "id": pontuacao.id,
                    "dataCriacao": data_formatada,
                    "descricao": pontuacao.descricao or "",
                    "pontosEfetivos": str(int(pontuacao.pontos)),
                    "pontosPreenchidos": str(int(pontuacao.pontos_previsto or pontuacao.pontos)),
                    "statusStr": str(status),
                    "status": pontuacao.status,
                    "semana": pontuacao.semana
                }

                resultado[categoria]["itens"].append(item)

            elif categoria == "contratos":
                item = {
                    "id": pontuacao.id,
                    "tipo": pontuacao.cliente.tipo_cliente,
                    "dataCriacao": data_formatada,
                    "titulo": pontuacao.cliente.titulo or "",
                    "descricao": pontuacao.descricao or "",
                    "pontos": str(int(pontuacao.pontos)),
                    
                }

                resultado[categoria]["itens"].append(item)
            
            elif categoria == "retencao":
                item = {
                    "id": pontuacao.id,
                    "dataCriacao": data_formatada,
                    "titulo": pontuacao.cliente.titulo or "",
                    "pontos": str(int(pontuacao.pontos)),
                }

                resultado[categoria]["itens"].append(item)

    # Atualizando o resumo corretamente
    for mes_ano, valores in resumo_mensal.items():
        resultado["recebimentos"][mes_ano]["infos"]["valorTotal"] = f"R$ {valores['valorTotal']:,.2f}".replace(",", ".")
        resultado["recebimentos"][mes_ano]["infos"]["pontos"] = str(valores["pontos"])

    resultado["desafios"]["infos"]["pontos"] = pontos_desafio
    resultado["certificacoes"]["infos"]["pontos"] = pontos_certificacao
    resultado["contratos"]["infos"]["pontos"] = pontos_contrato
    resultado["retencao"]["infos"]["pontos"] = pontos_retencao

    return Response(resultado)

@api_view(['GET'])
def painel_inicial_aluno(request, aluno_id):
    aluno = get_object_or_404(Alunos, id=int(aluno_id))
    campeonato_vigente, semana_subidometro = calcular_semana_vigente()
    data_int = datetime.strptime('2024-09-01', '%Y-%m-%d').date()

    # Buscar faturamento dos envios# Somar Valores de todos os envios que o tipo de contrato seja = 2
    total_valores_envios = Aluno_envios.objects.filter(aluno=aluno, status=3, semana__gt=0, data__gte=data_int).aggregate(total=Sum('valor_calculado'))['total'] or 0

    #Buscar faturamento dos campeonatos antigos
    total_valor_camp = Aluno_camp_faturamento_anterior.objects.filter(aluno=aluno).aggregate(total=Sum('valor'))['total'] or 0

    total_total_total = float(total_valores_envios) + float(total_valor_camp)

    # Evolução do aluno
    total_clientes = Aluno_clientes.objects.filter(aluno=aluno, status=1).count()

    mes_mais_ganhou = (
        Aluno_envios.objects
        .filter(aluno=aluno, status=3, semana__gt=0, data__gte=data_int)
        .annotate(mes=TruncMonth('data'))  # Agrupa por mês
        .values('mes')  # Seleciona apenas o mês
        .annotate(total_mes=Sum('valor_calculado'))  # Soma os valores por mês
        .order_by('-total_mes')  # Ordena do maior para o menor
        .first()  # Pega o primeiro, que é o maior
    )

    mes_mais_ganhou_valor = mes_mais_ganhou['total_mes'] if mes_mais_ganhou else 0

    # Subidômetro do aluno
    ultima_posicao = Alunos_posicoes_semana.objects.filter(aluno=aluno, semana=semana_subidometro).order_by('-data').first()
    ultima_cla = Mentoria_cla_posicao_semana.objects.filter(cla=aluno.cla, semana=semana_subidometro).order_by('-data').first()

    # Últimos 10 alunos
    ultimos_dez_posicoes = Alunos_posicoes_semana.objects.filter(semana=semana_subidometro).order_by('posicao')[:10]

    # Últimos 10 clãs
    ultimos_dez_clas = Mentoria_cla_posicao_semana.objects.filter(semana=semana_subidometro).order_by('posicao')[:10]

    resposta = {
        "evolucao": {
            "clientes": f"{total_clientes} clientes",
            "acumulou": f"R$ {total_total_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            "mesMaisGanhou": f"R$ {mes_mais_ganhou_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),  
        },
        "subidometro": {
            "posicao": str(ultima_posicao.posicao) if ultima_posicao else None,
            "pontos": int(float(ultima_posicao.pontos_totais)) if ultima_posicao and ultima_posicao.pontos_totais is not None else None,
            "posicaoCla": str(ultima_cla.posicao) if ultima_cla else None,
            "pontosCla": int(float(ultima_cla.pontos_totais)) if ultima_cla and ultima_cla.pontos_totais is not None else None
        },
        "placaCampeonato": {
            "alunos": [
                {
                    "posicao": str(alunos.posicao),
                    "pontos": int(float(alunos.pontos_totais)) if hasattr(alunos, 'pontos_totais') and alunos.pontos_totais is not None else None,
                    "aluno": str(alunos.aluno_id)
                } for alunos in ultimos_dez_posicoes
            ],
            "clas": [
                {
                    "posicao": str(cla.posicao),
                    "pontos": int(float(cla.pontos_totais)) if hasattr(cla, 'pontos_totais') and cla.pontos_totais is not None else None,
                    "cla": str(cla.cla_id)
                } for cla in ultimos_dez_clas
            ]
        }
    }

    return Response(resposta)

@api_view(['GET'])
def meus_clientes(request, aluno_id):
    aluno = get_object_or_404(Alunos, id=int(aluno_id))
    
    total_clientes = Aluno_clientes.objects.filter(aluno=aluno).count()
    clientes = Aluno_clientes.objects.filter(aluno=aluno).order_by('-data_criacao')
    
    alunos_lista = []
    for cliente in clientes:
        aluno_info = {
            "id": cliente.id,
            "titulo": cliente.titulo,
            "tipo": "Pessoa Física" if cliente.tipo_cliente == 1 else "Pessoa Jurídica",
            "contratosAprovados": str(Aluno_clientes_contratos.objects.filter(cliente=cliente, status=1).count()),
            "contratosPendentes": str(Aluno_clientes_contratos.objects.filter(cliente=cliente, status=0).count()),
            "contratosReprovados": str(Aluno_clientes_contratos.objects.filter(cliente=cliente, status=2).count()),
            "status": mapear_status(cliente.status),
            "int_status": cliente.status,
        }
        
        if cliente.status == 3:  # Caso o status seja "invalido"
            aluno_info["motivo"] = cliente.descricao_invalido
        
        alunos_lista.append(aluno_info)
    
    resposta = {
        "infos": {
            "totalClientes": str(total_clientes)
        },
        "alunos": alunos_lista
    }
    
    return Response(resposta)

@api_view(['GET'])
def meus_envios(request, aluno_id):
    aluno = get_object_or_404(Alunos, id=int(aluno_id))
    campeonato, _ = calcular_semana_vigente()
    semana = _ + 1
    envios_da_semana = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato, semana=semana).count()
    if not campeonato:
        return Response({"erro": "Nenhum campeonato encontrado."}, status=400)

    data_inicio = campeonato.data_inicio
    

    #pontos_aluno = union_pontuacao(aluno, campeonato)
    pontos_aluno = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato, data_cadastro__gte=data_inicio).order_by('-data_cadastro')
    dados_por_semana = defaultdict(lambda: {"infos": {}, "itens": []})

    for envio in pontos_aluno:
        if isinstance(envio.data_cadastro, datetime):
            data_local = envio.data_cadastro
        else:
            data_local = datetime.combine(envio.data_cadastro, datetime.min.time())

        if is_naive(data_local):
            data_local = make_aware(data_local)

        # Calcular a semana relativa ao campeonato
        delta = (data_local.date() - data_inicio).days
        semana_numero = (delta // 7) + 1  # Para começar a contagem da semana em 1
        semana_key = str(semana_numero)

        dia_semana = calendar.day_name[data_local.weekday()]

        dados_por_semana[semana_key]["infos"] = {
            "semana": semana_numero,
            "dataInicio": (data_inicio + timedelta(weeks=semana_numero - 1)).strftime('%d/%m/%Y'),
            "dataFim": (data_inicio + timedelta(weeks=semana_numero) - timedelta(days=1)).strftime('%d/%m/%Y'),
        }

        item = {
            "dataCriacao": data_local.strftime('%d/%m/%Y'),
            "data": envio.data.strftime('%d/%m/%Y'),
            "diaSemana": dia_semana,
            "tipo": str(envio.tipo),
            "tipoDescricao": obter_tipo_descricao(envio.tipo),
            "descricao": envio.descricao,
            "pontosEfetivos": int(envio.pontos),
            "pontosPreenchidos": int(envio.pontos_previsto or 0),
            "statusDescricao": obter_status_descricao(envio.status),
            "status": int(envio.status),
            "semana": int(envio.semana)
        }

        if envio.valor:
            item["valor"] = f"R$ {envio.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        if envio.arquivo1:
            item["arquivo1"] = envio.arquivo1
        if envio.arquivo1_motivo:
            item["arquivo2"] = envio.arquivo1_motivo

        dados_por_semana[semana_key]["itens"].append(item)

    # Ordenando as semanas da maior para a menor
    dados_ordenados = dict(sorted(dados_por_semana.items(), key=lambda x: int(x[0]), reverse=True))

    dados_geral = {
        "totalEnvios": envios_da_semana,
        "semanas": dados_ordenados
    }

    return Response(dados_geral)

@api_view(['GET'])
def subdometro_aluno(request, aluno_id):
    Campeonato, semana = calcular_semana_vigente()

    print("A Semana atual é: ", semana)
    aluno = get_object_or_404(Alunos, id=int(aluno_id))
    DataInicio = Campeonato.data_inicio
    data_int = datetime.strptime('2024-09-01', '%Y-%m-%d').date()


    # Filtra clientes com data de criação maior que a data de início do campeonato
    clientes = Aluno_clientes.objects.filter(aluno=aluno, status=1)

    # Contagem total de clientes
    total_clientes = clientes.count()

    # Somar Valores de todos os envios que o tipo de contrato seja = 2
    total_valores_envios = Aluno_envios.objects.filter(aluno=aluno, status=3, semana__gt=0, data__gte=data_int).aggregate(total=Sum('valor_calculado'))['total'] or 0
    

    #Buscar faturamento dos campeonatos antigos
    total_valor_camp = Aluno_camp_faturamento_anterior.objects.filter(aluno=aluno).aggregate(total=Sum('valor'))['total'] or 0


    total_total_total = float(total_valores_envios) + float(total_valor_camp)

    # Agrupar por mês e calcular a soma
    mes_mais_ganhou = (
        Aluno_envios.objects
        .filter(aluno=aluno, status=3, semana__gt=0, data__gte=data_int)
        .annotate(mes=TruncMonth('data'))  # Agrupa por mês
        .values('mes')  # Seleciona apenas o mês
        .annotate(total_mes=Sum('valor_calculado'))  # Soma os valores por mês
        .order_by('-total_mes')  # Ordena do maior para o menor
        .first()  # Pega o primeiro, que é o maior
    )

    mes_mais_ganhou_valor = mes_mais_ganhou['total_mes'] if mes_mais_ganhou else 0


    # Buscar os envios do aluno com status=3 e data válida
    todos_ganhos = Aluno_envios.objects.filter(
        aluno=aluno, 
        status=3, 
        semana__gt=0, 
        data__gte=data_int
    ).order_by('-data')

    # Dicionário para armazenar os valores por mês
    dados_por_mes = defaultdict(lambda: {"data": "", "valorAcumulado": 0})

    # Iterar sobre os ganhos e preencher os dados por mês
    for envio in todos_ganhos:
        if isinstance(envio.data, datetime):
            data_local = envio.data
        else:
            data_local = datetime.combine(envio.data, datetime.min.time())

        if is_naive(data_local):
            data_local = make_aware(data_local)

        # Obter o identificador do mês (YYYY-MM)
        mes_key = data_local.strftime("%Y-%m")

        # Atualizar os valores do mês corretamente somando os envios do mesmo mês
        dados_por_mes[mes_key]["data"] = mes_key
        dados_por_mes[mes_key]["valorAcumulado"] += round(envio.valor_calculado or 0, 2)  # Evita erro se `valor` for None

    # Ordenar os meses em ordem crescente
    meses_ordenados = sorted(dados_por_mes.keys())

    # Criar a lista final ordenada com os valores individuais de cada mês
    resultado_final = [dados_por_mes[mes] for mes in meses_ordenados]

    subdometro = Alunos_Subidometro.objects.filter(aluno=aluno, campeonato=Campeonato)

    semanas_campeonato = []
    
    for entry in subdometro:
        if entry.semana == semana + 1:
            continue  # pula a semana vigente
        semanas_campeonato.append({
            "semana": entry.semana,
            "pontos": int(entry.pontos) if entry.pontos else "0",
            "nivelAluno": str(entry.nivel) if entry.nivel else "0"
        })

    response_data = {
        "evolucao": {
            "clientes": f"{total_clientes} clientes",
            "acumulou": f"R$ {total_total_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            "mesMaisGanhou": f"R$ {mes_mais_ganhou_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        },
        "evolucaoGanhos": resultado_final,
        "semanasCampeonato": {
            "alunos": semanas_campeonato
        }
    }

    return Response(response_data)

class MD5(Func):
    function = 'MD5'
    template = "%(function)s(%(expressions)s)"

@api_view(['GET'])
def detalhes_cliente(request, aluno_id, cliente_md5):
    Campeonato, semana = calcular_semana_vigente()
    cliente = Aluno_clientes.objects.annotate(
            md5_id=MD5(Cast('id', output_field=CharField()))
        ).get(aluno_id=aluno_id, md5_id=cliente_md5)

    #ID para MD5
    md5_id = hashlib.md5(str(cliente.id).encode('utf-8')).hexdigest()

    DataInicio = Campeonato.data_inicio

    tipo_cliente = "Pessoa Física" if cliente.tipo_cliente == 1 else "Pessoa Jurídica"
    status = "Aprovado" if cliente.status == 1 else "Inativo"

    dados_por_semana = defaultdict(lambda: {"infos": [], "envios": []})

    for envio in cliente.envios_cliente_cl.all():
        if isinstance(envio.data, datetime):
            data_local = envio.data
        else:
            data_local = datetime.combine(envio.data, datetime.min.time())

        if is_naive(data_local):
            data_local = make_aware(data_local)

        # Calcular a semana relativa ao campeonato
        delta = (data_local.date() - DataInicio).days
        semana_numero = (delta // 7) + 1  # Para começar a contagem da semana em 1
        semana_key = str(semana_numero)

        # Criar dicionário de envio
        envio_dict = {
            "id": str(envio.id),
            "dataCadastro": envio.data_cadastro.strftime("%Y-%m-%d"),
            "data": envio.data.strftime("%Y-%m-%d"),
            "semana": str(semana_numero),
            "valor": f"R$ {envio.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "pontos": int(envio.pontos),
            "arquivo1": envio.arquivo1,
            "status": str(envio.status),
        }

        # Adicionar envio à semana correspondente
        dados_por_semana[semana_key]["envios"].append(envio_dict)

    # Adicionar total de envios por semana
    for semana, dados in dados_por_semana.items():
        dados["infos"].append({
            "semana": semana,
            "totalEnvios": str(len(dados["envios"]))
        })
    
    semanas_ordenadas = dict(sorted(dados_por_semana.items(), key=lambda x: int(x[0]), reverse=True))
    
    contratos_data = []
    for contrato in cliente.contratos.all():
        contratos_data.append({
            "semana": str(contrato.semana),
            "dataInicio": contrato.data_contrato.strftime("%d/%m/%Y"),
            "dataFim": contrato.data_vencimento.strftime("%d/%m/%Y"),
            "dataCadastro": contrato.data_criacao.strftime("%d/%m/%Y"),
            "arquivo": contrato.arquivo1,
            "tipo": str(contrato.tipo_contrato),
            "valor": f"R$ {contrato.valor_contrato:.2f}" if contrato.valor_contrato else contrato.porcentagem_contrato,
            "status": "Aprovado" if contrato.status == 1 else "Inativo"
        })

    response_data = {
        'detalhe': {
            "md5ID": md5_id,
            'id': str(cliente.id),
            'titulo': cliente.titulo,
            'tipo': tipo_cliente,
            'documento': cliente.documento,
            'status': status
        },
        'contratos': contratos_data,
        "envios": {
            "semanas": semanas_ordenadas
        }
    }

    return Response(response_data)

@api_view(['GET'])
def rankingAPI(request):
    alunos_qs = ranking_streamer()
    serializer = RankingSerializer(alunos_qs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def ranking_semanalAPI(request):
    campeonato, semana = calcular_semana_vigente()
    # Obtendo a maior semana disponível para o campeonato vigente
    maior_semana = Alunos_posicoes_semana.objects.filter(campeonato=campeonato).aggregate(Max('semana'))['semana__max']
    
    # Usando select_related para otimizar queries relacionadas
    alunos_rank_semanal = Alunos_posicoes_semana.objects.filter(
        campeonato=campeonato, semana=maior_semana
    ).select_related("aluno", "cla").order_by("posicao")

    serializer = RankingSemanalSerializer(alunos_rank_semanal, many=True)

    return Response(serializer.data)

@api_view(['GET'])
def ranking_semanal_claAPI(request):
    campeonato, semana = calcular_semana_vigente()
    # Obtendo a maior semana disponível para o campeonato vigente
    maior_semana = Mentoria_cla_posicao_semana.objects.filter(campeonato=campeonato).aggregate(Max('semana'))['semana__max']
    print(f"Maior semana: {maior_semana}")
    print(f"Campeonato: {campeonato}", f"Semana: {semana}")
    # Usando select_related para otimizar queries relacionadas
    alunos_rank_semanal = Mentoria_cla_posicao_semana.objects.filter(
        campeonato=campeonato, semana=maior_semana
    ).select_related("cla").order_by("posicao")

    serializer = RankingSemanalClaSerializer(alunos_rank_semanal, many=True)
    
    return Response(serializer.data)

@api_view(['GET'])
def meu_cla(request, aluno_id):
    aluno = get_object_or_404(Alunos, id=int(aluno_id))
    campeonato, semana = calcular_semana_vigente()
    data_int = datetime.strptime('2024-09-01', '%Y-%m-%d').date()
    if not aluno.cla:
        return Response({"error": "Este aluno não pertence a nenhum clã."}, status=404)

    cla = aluno.cla

    # Verifica se o clã é o fake (id == 1000)
    if cla.id == 1000:
        return Response({})

    # Dados do clã
    meu_cla_detalhes = {
        "id": str(cla.id),
        "titulo": cla.nome,
        "sigla": cla.sigla or "",
        "codigoBrasao": cla.brasao or "",
        "qtdAlunos": str(cla.aluno_cla.count())
    }

    # Alunos do clã
    alunos_data = {}
    for aluno in cla.aluno_cla.filter(status='ACTIVE'):
        rank_semanal = Alunos_posicoes_semana.objects.filter(
            aluno=aluno,
            campeonato=campeonato,
            semana=semana
        ).first()

        qnt_envios_validos = Aluno_envios.objects.filter(
            aluno=aluno,
            campeonato=campeonato,
            status=3,
            semana__gt=0,
            data__gte=data_int
        ).count()

        if not rank_semanal:
            print(f"Sem posição para aluno ID {aluno.id}, nome {aluno.nome_completo}")


        alunos_data[str(aluno.id)] = {
            "id": str(aluno.id),
            "nome": aluno.nome_completo or aluno.nome_social or aluno.apelido or "",
            "nivel": str(aluno.nivel or 0),
            "qtdEnviosValidosGeral": qnt_envios_validos,
            "pontos": rank_semanal.pontos_totais if rank_semanal else 0,
            "ranking": rank_semanal.posicao if rank_semanal else None,
        }

    return Response({
        "meuClaDetalhes": meu_cla_detalhes,
        "alunos": alunos_data
    })

@api_view(['GET'])
def ranking_semanalAPI_test(request):
    #campeonato, semana = calcular_semana_vigente()
    campeonato = Campeonato.objects.get(id=5)
    
    # Usando select_related para otimizar queries relacionadas
    alunos_rank_semanal = Alunos_posicoes_semana.objects.filter(
        campeonato=campeonato, semana=26
    ).select_related("aluno", "cla").order_by("posicao")

    serializer = RankingSemanalSerializer(alunos_rank_semanal, many=True)
    return Response(serializer.data)


