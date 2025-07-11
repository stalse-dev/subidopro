from rest_framework import serializers
from subidometro.models import *

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
