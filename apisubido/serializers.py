from rest_framework import serializers
from subidometro.models import *

class RankAlunoSerializer(serializers.ModelSerializer):
    aluno_nome_completo = serializers.CharField(source='aluno.nome_completo', read_only=True)

    class Meta:
        model = Alunos_posicoes_semana
        fields = ['aluno_id', 'aluno_nome_completo', 'posicao', 'pontos_totais', 'semana', 'data']

class RankClaSerializer(serializers.ModelSerializer):
    cla_nome = serializers.CharField(source='cla.nome', read_only=True)

    class Meta:
        model = Mentoria_cla_posicao_semana
        fields = ['cla_id', 'cla_nome', 'posicao', 'pontos_totais', 'semana', 'data']
