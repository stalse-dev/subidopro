from rest_framework import serializers
from subidometro.models import *

class AlunosPosicoesSemanaSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source="aluno.nome_completo", read_only=True)

    class Meta:
        model = Alunos_posicoes_semana
        fields = [
            "id", "aluno", "aluno_nome", "cla", "campeonato", "semana", "posicao", "tipo", 
            "pontos_recebimento", "pontos_desafio", "pontos_certificacao", 
            "pontos_manual", "pontos_contrato", "pontos_retencao", "pontos_totais", "data"
        ]
