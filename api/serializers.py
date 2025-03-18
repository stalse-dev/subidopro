from rest_framework import serializers
from subidometro.models import *

class RankingSerializer(serializers.ModelSerializer):
    pontos_recebimento = serializers.SerializerMethodField()
    pontos_desafio = serializers.SerializerMethodField()
    pontos_certificacoes = serializers.SerializerMethodField()
    pontos_manual = serializers.SerializerMethodField()
    pontos_contrato = serializers.SerializerMethodField()
    pontos_retencao = serializers.SerializerMethodField()
    total_pontos_final = serializers.SerializerMethodField()
    ranking = serializers.SerializerMethodField()

    class Meta:
        model = Alunos
        fields = ['id', 'nome_completo', 'nivel', 'apelido', 'email', 'data_criacao', 'status', 'ranking', 'pontos_recebimento', 'pontos_desafio', 'pontos_certificacoes', 'pontos_manual', 'pontos_contrato', 'pontos_retencao', 'total_pontos_final']

    def get_pontos_recebimento(self, obj):
        return getattr(obj, 'pontos_recebimento', 0)

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

class RankingSemanalSerializer(serializers.ModelSerializer):
    nome_aluno = serializers.SerializerMethodField()
    nome_cla = serializers.SerializerMethodField()
    pontos_recebimento = serializers.SerializerMethodField()
    pontos_desafio = serializers.SerializerMethodField()
    pontos_certificacao = serializers.SerializerMethodField()
    pontos_manual = serializers.SerializerMethodField()
    pontos_contrato = serializers.SerializerMethodField()
    pontos_retencao = serializers.SerializerMethodField()
    pontos_totais = serializers.SerializerMethodField()

    class Meta:
        model = Alunos_posicoes_semana
        fields = '__all__'  # Inclui todos os campos do modelo
        extra_fields = ['nome_aluno', 'nome_cla']

    def get_nome_aluno(self, obj):
        return obj.aluno.nome_completo if obj.aluno else None

    def get_nome_cla(self, obj):
        return obj.cla.nome if obj.cla else None

    # Métodos para converter os pontos em inteiros
    def get_pontos_recebimento(self, obj):
        return int(obj.pontos_recebimento) if obj.pontos_recebimento else 0

    def get_pontos_desafio(self, obj):
        return int(obj.pontos_desafio) if obj.pontos_desafio else 0

    def get_pontos_certificacao(self, obj):
        return int(obj.pontos_certificacao) if obj.pontos_certificacao else 0

    def get_pontos_manual(self, obj):
        return int(obj.pontos_manual) if obj.pontos_manual else 0

    def get_pontos_contrato(self, obj):
        return int(obj.pontos_contrato) if obj.pontos_contrato else 0

    def get_pontos_retencao(self, obj):
        return int(obj.pontos_retencao) if obj.pontos_retencao else 0

    def get_pontos_totais(self, obj):
        return int(obj.pontos_totais) if obj.pontos_totais else 0
    
class RankingSemanalClaSerializer(serializers.ModelSerializer):
    nome_cla = serializers.SerializerMethodField()
    pontos_recebimento = serializers.SerializerMethodField()
    pontos_desafio = serializers.SerializerMethodField()
    pontos_certificacao = serializers.SerializerMethodField()
    pontos_manual = serializers.SerializerMethodField()
    pontos_contrato = serializers.SerializerMethodField()
    pontos_retencao = serializers.SerializerMethodField()
    pontos_totais = serializers.SerializerMethodField()

    class Meta:
        model = Mentoria_cla_posicao_semana
        fields = '__all__'  # Inclui todos os campos do modelo
        extra_fields = ['nome_cla']

    def get_nome_cla(self, obj):
        return obj.cla.nome if obj.cla else None

    def get_pontos_recebimento(self, obj):
        return int(obj.pontos_recebimento) if obj.pontos_recebimento else 0

    def get_pontos_desafio(self, obj):
        return int(obj.pontos_desafio) if obj.pontos_desafio else 0

    def get_pontos_certificacao(self, obj):
        return int(obj.pontos_certificacao) if obj.pontos_certificacao else 0

    def get_pontos_manual(self, obj):
        return int(obj.pontos_manual) if obj.pontos_manual else 0

    def get_pontos_contrato(self, obj):
        return int(obj.pontos_contrato) if obj.pontos_contrato else 0

    def get_pontos_retencao(self, obj):
        return int(obj.pontos_retencao) if obj.pontos_retencao else 0

    def get_pontos_totais(self, obj):
        return int(obj.pontos_totais) if obj.pontos_totais else 0


    







