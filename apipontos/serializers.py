from rest_framework import serializers
from alunos.views import cliente
from subidometro.models import *
from django.utils.timezone import make_aware
from datetime import datetime, date



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
        fields = ["id", "aluno", "cliente", "contrato", "campeonato", "data", "descricao", "valor", "arquivo1", "arquivo1_motivo", "arquivo1_status",
                "data_cadastro", "rastreador_analise", "status", "status_motivo", "status_comentario", "semana"]
        
    def gera_pontos(self, valor):
        valor = float(valor)
        return int((valor // 100) * 10)

    def gera_pontos_contrato(self, valor):
        if valor >= 0 and valor < 1000:
            return 60
        elif valor >= 1000 and valor < 3000:
            return 480
        elif valor >= 3000 and valor < 5000:
            return 1080
        elif valor >= 5000 and valor < 9000:
            return 1920
        elif valor >= 9000:
            return 2460
        else:
            return 0
        
    def create(self, validated_data):
        data_envio = validated_data.get("data") or date.today()
        campeonato = validated_data.get("campeonato")
        contrato = validated_data.get("contrato")
        cliente = validated_data.get("cliente")
        aluno = validated_data.get("aluno")
        valor = validated_data.get("valor") or 0

        if not campeonato:
            campeonato = Campeonato.objects.filter(ativo=True).first()
            validated_data["campeonato"] = campeonato

        pontos = 0
        pontos_previsto = 0

        # Cálculo padrão de pontos
        if contrato and contrato.tipo_contrato == 2:
            valor_minimo = float(valor) * 0.1
            valor_calculado = valor_minimo
        else:
            valor_calculado = valor

        if campeonato and data_envio >= campeonato.data_inicio:
            if contrato and contrato.tipo_contrato == 2:
                pontos = self.gera_pontos(valor_minimo)
                pontos_previsto = pontos
            else:
                pontos = self.gera_pontos(valor)
                pontos_previsto = pontos
        else:
            pontos = 0
            pontos_previsto = 0

        # Adiciona campos calculados
        validated_data["pontos"] = pontos
        validated_data["pontos_previsto"] = pontos_previsto
        validated_data["valor_calculado"] = valor_calculado

        envio = super().create(validated_data)

        contagem_contratos = cliente.cliente_aluno_contrato.count()

        if contagem_contratos == 0 and campeonato:
            data_limite = campeonato.data_inicio
            if cliente.data_criacao and cliente.data_criacao.date() > data_limite:
                if contrato.tipo_contrato == 2:
                    valor_final = float(valor) * 0.1
                    pontos_contrato = self.gera_pontos_contrato(valor_final)
                    contrato.valor_contrato = valor_final
                    contrato.save()
                else:
                    valor_final = float(valor)
                    pontos_contrato = self.gera_pontos_contrato(valor_final)

                Aluno_contrato.objects.create(
                    campeonato=campeonato,
                    aluno=aluno,
                    cliente=cliente,
                    contrato=contrato,
                    envio=envio,
                    descricao=validated_data.get("descricao"),
                    valor=valor,
                    data=data_envio,
                    data_cadastro=validated_data.get("data_cadastro") or make_aware(datetime.now()),
                    pontos=pontos_contrato,
                    status=0
                )

        return envio

