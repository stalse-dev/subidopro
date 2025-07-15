from rest_framework import serializers
from subidometro.models import *
from collections import defaultdict, OrderedDict
from datetime import datetime


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

class ClientesSerializer(serializers.ModelSerializer):
    status_str = serializers.SerializerMethodField()
    contratos_aprovados = serializers.SerializerMethodField()
    contratos_pendentes = serializers.SerializerMethodField()
    contratos_reprovados = serializers.SerializerMethodField()

    class Meta:
        model = Aluno_clientes
        fields = "__all__"
        # Para incluir os novos campos mesmo com "__all__"
        extra_fields = ['status_str', 'contratos_aprovados', 'contratos_pendentes', 'contratos_reprovados']

    def get_status_str(self, obj):
        return status_map(obj.status)

    def get_contratos_aprovados(self, obj):
        return obj.contratos.filter(status=1).count()

    def get_contratos_pendentes(self, obj):
        return obj.contratos.filter(status=0).count()

    def get_contratos_reprovados(self, obj):
        return obj.contratos.filter(status=2).count()

