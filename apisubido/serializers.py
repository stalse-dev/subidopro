from rest_framework import serializers
from subidometro.models import *
from collections import defaultdict, OrderedDict
from datetime import datetime
from django.utils.timezone import make_aware, is_naive
import calendar
from datetime import datetime, timedelta


def tipo_map(tipo):
    tipos = {
        2: "Recebimento",
        3: "Certificação",
        4: "Desafio",
        5: "Manual"
    }
    return tipos.get(tipo, "Desconhecido")

def status_map_pontos(status):
    return {
        0: "Não analisado",
        1: "Pendente de análise",
        2: "Invalidado",
        3: "Validado"
    }.get(status, "Desconhecido")

def status_map(status):
    return {
        0: "Pendente",
        1: "Validado",
        2: "Invalidado",
    }.get(status, "Desconhecido")

class RankAlunoSerializer(serializers.ModelSerializer):
    aluno_nome_completo = serializers.CharField(source='aluno.nome_completo', read_only=True)
    pontos_totais = serializers.SerializerMethodField()

    def get_pontos_totais(self, obj):
        return int(obj.pontos_totais) if obj.pontos_totais is not None else 0

    class Meta:
        model = Alunos_posicoes_semana
        fields = ['aluno_id', 'aluno_nome_completo', 'posicao', 'pontos_totais', 'semana', 'data']

class RankClaSerializer(serializers.ModelSerializer):
    cla_nome = serializers.CharField(source='cla.nome', read_only=True)
    pontos_totais = serializers.SerializerMethodField()

    def get_pontos_totais(self, obj):
        return int(obj.pontos_totais) if obj.pontos_totais is not None else 0

    class Meta:
        model = Mentoria_cla_posicao_semana
        fields = ['cla_id', 'cla_nome', 'posicao', 'pontos_totais', 'semana', 'data']

class RankAlunoDetalhesSerializer(serializers.ModelSerializer):
    nome_aluno = serializers.CharField(source='aluno.nome_completo', read_only=True)
    nome_cla = serializers.CharField(source='cla.nome', read_only=True)

    # Converte diretamente no campo usando to_representation
    def to_representation(self, instance):
        data = super().to_representation(instance)
        campos_para_int = [
            'pontos_recebimento', 'pontos_desafio', 'pontos_certificacao',
            'pontos_manual', 'pontos_contrato', 'pontos_retencao', 'pontos_totais'
        ]
        for campo in campos_para_int:
            valor = data.get(campo)
            data[campo] = int(float(valor)) if valor else 0
        return data

    class Meta:
        model = Alunos_posicoes_semana
        fields = [
            'id', 'nome_aluno', 'nome_cla',
            'pontos_recebimento', 'pontos_desafio', 'pontos_certificacao',
            'pontos_manual', 'pontos_contrato', 'pontos_retencao', 'pontos_totais',
            'semana', 'posicao', 'tipo', 'data', 'aluno', 'cla', 'campeonato'
        ]

def AlunoEnviosExtratoSerializer(envios, semana_limite):
    recebimentos_temp = defaultdict(lambda: {"infos": {"data": "", "valor_total": "R$ 0,00", "pontos_total": "0"}, "envios": []})
    resumo_mensal = defaultdict(lambda: {"valor_total": 0, "pontos_total": 0})

    for envio in envios:
        if envio.semana == semana_limite + 1:
            continue

        if not envio.data:
            continue  # evita erro se data estiver nula

        data_formatada = envio.data_cadastro.strftime('%d/%m/%Y') if envio.data_cadastro else ""
        data_formatada_data = envio.data.strftime('%d/%m/%Y')
        nome_mes = envio.data.strftime('%B').upper()
        mes_ano = envio.data.strftime('%Y-%m')

        item = {
            "id": envio.id,
            "data_criacao": data_formatada,
            "data": data_formatada_data,
            "descricao": envio.descricao or "",
            "valor": f"R$ {float(envio.valor):.2f}",
            "pontos_efetivos": str(int(envio.pontos)),
            "pontos_preenchidos": str(int(envio.pontos_previsto or envio.pontos)),
            "arquivo": str(envio.arquivo1 or ""),
            "status_str": status_map_pontos(envio.status),
            "status": envio.status,
            "semana": envio.semana
        }

        if envio.status == 3:
            resumo_mensal[mes_ano]["valor_total"] += float(envio.valor)
            resumo_mensal[mes_ano]["pontos_total"] += int(envio.pontos)
            resumo_mensal[mes_ano]["pontos_total"] = min(resumo_mensal[mes_ano]["pontos_total"], 3000)

        recebimentos_temp[mes_ano]["infos"]["data_criacao"] = f"{nome_mes} {envio.data.year}"
        recebimentos_temp[mes_ano]["envios"].append(item)

    for mes_ano, valores in resumo_mensal.items():
        recebimentos_temp[mes_ano]["infos"]["valor_total"] = f"R$ {valores['valor_total']:,.2f}".replace(",", ".")
        recebimentos_temp[mes_ano]["infos"]["pontos_total"] = str(valores["pontos_total"])

    meses_ordenados = sorted(recebimentos_temp.keys(), reverse=True)

    recebimentos = OrderedDict()
    for chave in meses_ordenados:
        recebimentos[chave] = recebimentos_temp[chave]

    return recebimentos

def AlunoDesafioExtratoSerializer(desafios, semana_limite, pontos_desafio):
    desafios_temp = {"infos": {"total_pontos": pontos_desafio}, "desafios": []}

    for desafio in desafios:
        if desafio.semana == semana_limite + 1:
            continue

        data_formatada = desafio.data_cadastro.strftime('%d/%m/%Y') if desafio.data_cadastro else ""

        item = {
            "id": desafio.id,
            "data_criacao": data_formatada,
            "descricao": desafio.desafio.titulo or "",
            "pontos_efetivos": str(int(desafio.pontos)),
            "pontos_preenchidos": str(int(desafio.pontos_previsto or desafio.pontos)),
            "status_str": status_map_pontos(desafio.status),
            "status": desafio.status,
            "semana": desafio.semana
        }

        desafios_temp["desafios"].append(item)

    return desafios_temp

def AlunoCertificacaoExtratoSerializer(certificacoes, semana_limite, pontos_certificacao):
    certificacoes_temp = {"infos": {"total_pontos": pontos_certificacao}, "certificacoes": []}

    for certificacao in certificacoes:
        if certificacao.semana == semana_limite + 1:
            continue

        data_formatada = certificacao.data_cadastro.strftime('%d/%m/%Y') if certificacao.data_cadastro else ""
        item = {
            "id": certificacao.id,
            "data_criacao": data_formatada,
            "descricao": certificacao.descricao or "",
            "pontos": str(int(certificacao.pontos)),
            "semana": certificacao.semana
        }

        certificacoes_temp["certificacoes"].append(item)

    return certificacoes_temp

def AlunoManualExtratoSerializer(manuals, semana_limite, pontos_manual):
    manuals_temp = {"infos": {"total_pontos": pontos_manual}, "manual": []}

    for manual in manuals:
        if manual.semana == semana_limite + 1:
            continue

        data_formatada = manual.data_cadastro.strftime('%d/%m/%Y') if manual.data_cadastro else ""
        item = {
            "id": manual.id,
            "data_criacao": data_formatada,
            "descricao": manual.descricao or "",
            "pontos_efetivos": str(int(manual.pontos)),
            "semana": manual.semana
        }

        manuals_temp["manual"].append(item)

    return manuals_temp

def AlunoContratoExtratoSerializer(contratos, pontos_contrato):
    contratos_temp = {"infos": {"total_pontos": pontos_contrato}, "contratos": []}

    for contrato in contratos:
        data_formatada = contrato.data_cadastro.strftime('%d/%m/%Y') if contrato.data_cadastro else ""

        item = {
            "id": contrato.id,
            "tipo": contrato.cliente.tipo_cliente,
            "data_criacao": data_formatada,
            "titulo": contrato.cliente.titulo or "",
            "descricao": contrato.descricao or "",
            "pontos": str(int(contrato.pontos)),
        }

        contratos_temp["contratos"].append(item)

    return contratos_temp

def AlunosRetencaoExtratoSerializer(retencoes, pontos_retencao):
    retencao_temp = {"infos": {"total_pontos": pontos_retencao}, "retencao": []}

    for retencao in retencoes:
        data_formatada = retencao.data.strftime('%d/%m/%Y') if retencao.data else ""

        item = {
            "id": retencao.id,
            "data_criacao": data_formatada,
            "titulo": retencao.cliente.titulo or "",
            "pontos": str(int(retencao.pontos)),
        }

        retencao_temp["retencao"].append(item)

    return retencao_temp

def ClientesSerializer(clientes):
    clientes_temp = []
    for cliente in clientes:
        aluno_info = {
            "id": cliente.id,
            "titulo": cliente.titulo,
            "tipo": "Pessoa Física" if cliente.tipo_cliente == 1 else "Pessoa Jurídica",
            "contratos_aprovados": str(Aluno_clientes_contratos.objects.filter(cliente=cliente, status=1).count()),
            "contratos_pendentes": str(Aluno_clientes_contratos.objects.filter(cliente=cliente, status=0).count()),
            "contratos_reprovados": str(Aluno_clientes_contratos.objects.filter(cliente=cliente, status=2).count()),
            "status_str": status_map(cliente.status),
            "int_status": cliente.status,
        }
        
        if cliente.status == 3:  # Caso o status seja "invalido"
            aluno_info["motivo"] = cliente.descricao_invalido
        
        clientes_temp.append(aluno_info)

    return clientes_temp

def MeusEnviosSerializer(envios, data_inicio):
    dados_por_semana = defaultdict(lambda: {"infos": {}, "envios": []})

    for envio in envios:
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
            "data_inicio": (data_inicio + timedelta(weeks=semana_numero - 1)).strftime('%d/%m/%Y'),
            "data_fim": (data_inicio + timedelta(weeks=semana_numero) - timedelta(days=1)).strftime('%d/%m/%Y'),
        }

        item = {
            "data_criacao": data_local.strftime('%d/%m/%Y'),
            "data": envio.data.strftime('%d/%m/%Y'),
            "dia_semana": dia_semana,
            "tipo": str(envio.tipo),
            "tipo_descricao": tipo_map(envio.tipo),
            "descricao": envio.descricao,
            "pontos_efetivos": int(envio.pontos),
            "pontos_preenchidos": int(envio.pontos_previsto or 0),
            "status_str": status_map_pontos(envio.status),
            "status": int(envio.status),
            "semana": int(envio.semana)
        }

        if envio.valor:
            item["valor"] = f"R$ {envio.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        if envio.arquivo1:
            item["arquivo"] = envio.arquivo1

        dados_por_semana[semana_key]["envios"].append(item)

    dados_ordenados = {
        f"semana {semana}": dados_por_semana[semana]
        for semana in sorted(dados_por_semana.keys(), key=int, reverse=True)
    }

    return dados_ordenados

def EvolucaoMesSerializer(envios):
    dados_por_mes = defaultdict(lambda: {"data": "", "valor_acumulado": 0})

    for envio in envios:
        if isinstance(envio.data, datetime):
            data_local = envio.data
        else:
            data_local = datetime.combine(envio.data, datetime.min.time())

        if is_naive(data_local):
            data_local = make_aware(data_local)

        mes_key = data_local.strftime("%Y-%m")
        dados_por_mes[mes_key]["data"] = mes_key
        dados_por_mes[mes_key]["valor_acumulado"] += round(envio.valor_calculado or 0, 2)

    meses_ordenados = sorted(dados_por_mes.keys())
    resultado_final = [dados_por_mes[mes] for mes in meses_ordenados]

    return resultado_final

def EvolucaoSemanaSerializer(subdometro, semana):
    semanas_campeonato = []
    
    for entry in subdometro:
        if entry.semana == semana + 1:
            continue
        semanas_campeonato.append({
            "semana": entry.semana,
            "pontos": int(entry.pontos) if entry.pontos else "0",
            "nivel_aluno": str(entry.nivel) if entry.nivel else "0"
        })

    return semanas_campeonato

def ContratosSerializer(contratos):
    contratos_temp = []
    for contrato in contratos:
        contratos_temp.append({
            "semana": str(contrato.semana),
            "dataInicio": contrato.data_contrato.strftime("%d/%m/%Y"),
            "dataFim": contrato.data_vencimento.strftime("%d/%m/%Y"),
            "dataCadastro": contrato.data_criacao.strftime("%d/%m/%Y"),
            "arquivo": contrato.arquivo1,
            "tipo": str(contrato.tipo_contrato),
            "valor": f"R$ {contrato.valor_contrato:.2f}" if contrato.valor_contrato else contrato.porcentagem_contrato,
            "status": "Aprovado" if contrato.status == 1 else "Inativo"
        })

    return contratos_temp

def EnviosSerializer(envios):
    envios_temp = []
    for envio in envios:
        envios_temp.append({
            "id": str(envio.id),
            "data_cadastro": envio.data_cadastro.strftime("%Y-%m-%d"),
            "data": envio.data.strftime("%Y-%m-%d"),
            "semana": str(envio.semana),
            "valor": f"R$ {envio.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "pontos": int(envio.pontos),
            "arquivo1": envio.arquivo1,
            "status": str(envio.status),
            "status_str": status_map_pontos(envio.status),
            "campeonato": envio.campeonato_id,
        })

    return envios_temp

def AlunosListClaSerializer(alunos, campeonato, data_int, semana):
    alunos_data = []
    for aluno in alunos:
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
            continue


        alunos_data.append({
            "id": str(aluno.id),
            "nome": aluno.nome_completo or aluno.nome_social or aluno.apelido or "",
            "nivel": str(aluno.nivel or 0),
            "qtd_envios_validos_geral": qnt_envios_validos,
            "pontos": rank_semanal.pontos_totais if rank_semanal else 0,
            "ranking": rank_semanal.posicao if rank_semanal else None,
        })

    return alunos_data

class AlunoClientesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_clientes
        fields = ["id", "titulo", "estrangeiro", "tipo_cliente", "tipo_contrato",
                "sociedade", "cliente_antes_subidopro", "documento_antigo", "documento",
                "telefone", "email", "data_criacao",
                "rastreador", "status", "motivo_invalido",
                "descricao_invalido", "sem_pontuacao", "rastreador_analise", "campeonato", "aluno"]

class AlunoClientesContratosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_clientes_contratos
        fields = ["id","cliente", "tipo_contrato", "valor_contrato", 
                "porcentagem_contrato", "data_contrato", "data_vencimento", 
                "data_criacao", "arquivo1", "status", "data_contrato", "data_vencimento", "data_criacao",
                "motivo_invalido", "descricao_invalido", "rastreador_analise", "analise_data"]

