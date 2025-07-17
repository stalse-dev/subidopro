from rest_framework import serializers
from subidometro.models import *

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

class AlunoEnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_envios
        fields = ["id", "aluno", "cliente", "contrato", "data", "descricao", "valor", "arquivo1", "arquivo1_motivo", "arquivo1_status", 
                "data_cadastro", "rastreador_analise", "status", "status_motivo", "status_comentario", "semana"]

