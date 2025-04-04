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

class AlunosRankingStreamerSerializer(serializers.ModelSerializer):
    pontos_recebimento = serializers.SerializerMethodField()
    pontos_potenciais = serializers.SerializerMethodField()
    pontos_desafio = serializers.SerializerMethodField()
    pontos_certificacoes = serializers.SerializerMethodField()
    pontos_manual = serializers.SerializerMethodField()
    pontos_contrato = serializers.SerializerMethodField()
    pontos_retencao = serializers.SerializerMethodField()
    total_pontos_final = serializers.SerializerMethodField()
    ranking = serializers.SerializerMethodField()
    cla = serializers.CharField(source="cla.nome", read_only=True)

    class Meta:
        model = Alunos
        fields = ['id', 'nome_completo', 'cla', 'nivel', 'apelido', 'email', 'data_criacao', 'status', 'ranking', 'pontos_recebimento','pontos_potenciais' , 'pontos_desafio', 'pontos_certificacoes', 'pontos_manual', 'pontos_contrato', 'pontos_retencao', 'total_pontos_final']

    def get_pontos_recebimento(self, obj):
        return getattr(obj, 'pontos_recebimento', 0)

    def get_pontos_potenciais(self, obj):
        return getattr(obj, 'pontos_potenciais', 0)

    def get_pontos_desafio(self, obj):
        return getattr(obj, 'pontos_desafio', 0)

    def get_pontos_certificacoes(self, obj):
        return getattr(obj, 'pontos_certificacoes', 0)

    def get_pontos_manual(self, obj):
        return getattr(obj, 'pontos_manual', 0)

    def get_pontos_contrato(self, obj):
        return getattr(obj, 'pontos_contrato', 0)

    def get_pontos_retencao(self, obj):
        return getattr(obj, 'pontos_retencao', 0)

    def get_total_pontos_final(self, obj):
        return getattr(obj, 'total_pontos_final', 0)

    def get_ranking(self, obj):
        return getattr(obj, 'ranking', None)
    
class AlunosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alunos
        fields = '__all__'