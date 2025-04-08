from rest_framework import serializers
from subidometro.models import *
from django.db.models import Max

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
    
class AlunoEnviosSerializer(serializers.ModelSerializer):
    tipo_contrato = serializers.IntegerField(source="contrato.tipo_contrato", read_only=True)
    cliente = serializers.CharField(source="cliente.nome", read_only=True)
    cliente_id = serializers.IntegerField(source="cliente.id", read_only=True)
    class Meta:
        model = Aluno_envios
        fields = [
            'id', 'campeonato', 'cliente', 'cliente_id', 'contrato', 'data', 'descricao', 'tipo_contrato',
            'valor', 'valor_calculado', 'arquivo1', 'arquivo1_status', 
            'data_cadastro', 'status', 'status_motivo', 'status_comentario', 
            'semana', 'tipo', 'pontos', 'pontos_previsto'
        ]

class AlunoDesafioSerializer(serializers.ModelSerializer):
    descricao = serializers.CharField(source="desafio.titulo", read_only=True)
    class Meta:
        model = Aluno_desafio
        fields = '__all__'

class AlunoCertificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_certificacao
        fields = '__all__'

class NivelDetalhesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentoria_lista_niveis
        fields = '__all__'

class AlunoPosicoesSemanaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alunos_posicoes_semana
        fields = '__all__'

class AlunoDetailsSerializer(serializers.ModelSerializer):
    nivel_detalhes = serializers.SerializerMethodField()
    pontuacoes_semanais_aluno = serializers.SerializerMethodField()
    recebimentos = AlunoEnviosSerializer(source="envios_aluno_cl", many=True, read_only=True)
    desafios = AlunoDesafioSerializer(source="aluno_desafios", many=True, read_only=True)
    certificacoes = AlunoCertificacaoSerializer(source="certificacoes_aluno", many=True, read_only=True)


    class Meta:
        model = Alunos
        fields = '__all__'

    def get_nivel_detalhes(self, obj):
        if obj.nivel:
            nivel = Mentoria_lista_niveis.objects.filter(id=obj.nivel).first()
            return NivelDetalhesSerializer(nivel).data if nivel else None
        return None
    
    def get_pontuacoes_semanais_aluno(self, obj):
        # Pega o maior campeonato relacionado ao aluno
        max_campeonato = obj.alunos_posicoes_semana.aggregate(Max('campeonato'))['campeonato__max']
        
        if max_campeonato is not None:
            # Agora dentro do campeonato, pega a maior semana
            max_semana = obj.alunos_posicoes_semana.filter(campeonato=max_campeonato).aggregate(Max('semana'))['semana__max']
            
            if max_semana is not None:
                # Busca os registros filtrados por maior campeonato e maior semana
                pontuacoes = obj.alunos_posicoes_semana.filter(
                    campeonato=max_campeonato,
                    semana=max_semana
                )
                return AlunoPosicoesSemanaSerializer(pontuacoes, many=True).data

        return []

class AlunoSerializer(serializers.ModelSerializer):
    nivel_detalhes = serializers.SerializerMethodField()
    pontuacoes_semanais_aluno = serializers.SerializerMethodField()

    class Meta:
        model = Alunos
        fields = ['id', 'nome_completo', 'apelido', 'email', 'nivel_detalhes', 'pontuacoes_semanais_aluno']

    def get_nivel_detalhes(self, obj):
        if obj.nivel:
            nivel = Mentoria_lista_niveis.objects.filter(id=obj.nivel).first()
            return NivelDetalhesSerializer(nivel).data if nivel else None
        return None

    def get_pontuacoes_semanais_aluno(self, obj):
        # Pega o maior campeonato relacionado ao aluno
        max_campeonato = obj.alunos_posicoes_semana.aggregate(Max('campeonato'))['campeonato__max']
        
        if max_campeonato is not None:
            # Agora dentro do campeonato, pega a maior semana
            max_semana = obj.alunos_posicoes_semana.filter(campeonato=max_campeonato).aggregate(Max('semana'))['semana__max']
            
            if max_semana is not None:
                # Busca os registros filtrados por maior campeonato e maior semana
                pontuacoes = obj.alunos_posicoes_semana.filter(
                    campeonato=max_campeonato,
                    semana=max_semana
                )
                return AlunoPosicoesSemanaSerializer(pontuacoes, many=True).data

        return []

class ClaPosicaoSemanaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentoria_cla_posicao_semana
        fields = [
            'semana', 'posicao', 'pontos_recebimento', 'pontos_desafio',
            'pontos_certificacao', 'pontos_manual', 'pontos_contrato',
            'pontos_retencao', 'pontos_totais'
        ]

class ClaDetailSerializer(serializers.ModelSerializer):
    alunos = AlunoSerializer(source='aluno_cla', many=True, read_only=True)
    pontuacoes_semanais = serializers.SerializerMethodField()

    class Meta:
        model = Mentoria_cla
        fields = '__all__'

    def get_pontuacoes_semanais(self, obj):
        # Busca o valor máximo da semana para o clã atual
        max_semana = obj.mentoria_cla_posicoes_semana_cla.aggregate(Max('semana'))['semana__max']
        
        if max_semana is not None:
            # Filtra apenas os dados da semana com maior número
            dados = obj.mentoria_cla_posicoes_semana_cla.filter(semana=max_semana)
            return ClaPosicaoSemanaSerializer(dados, many=True).data
        return []



