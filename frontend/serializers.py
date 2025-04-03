from rest_framework import serializers
from subidometro.models import *

class AlunosPosicoesSemanaSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source="aluno.nome_completo", read_only=True)
    cla = serializers.CharField(source="cla.nome", read_only=True)

    class Meta:
        model = Alunos_posicoes_semana
        fields = [
            "id", "aluno", "aluno_nome", "cla", "campeonato", "semana", "posicao", "tipo", 
            "pontos_recebimento", "pontos_desafio", "pontos_certificacao", 
            "pontos_manual", "pontos_contrato", "pontos_retencao", "pontos_totais", "data"
        ]

class MentoriaClaPosicaoSemanaSerializer(serializers.ModelSerializer):
    cla_nome = serializers.CharField(source="cla.nome", read_only=True)
    cla_sigla = serializers.CharField(source="cla.sigla", read_only=True)

    class Meta:
        model = Mentoria_cla_posicao_semana
        fields = [
            "id", "cla", "cla_nome", "cla_sigla", "campeonato", 
            "semana", "posicao", "pontos_recebimento", 
            "pontos_desafio", "pontos_certificacao", 
            "pontos_manual", "pontos_contrato", "pontos_retencao", 
            "pontos_totais", "data"
        ]
