from rest_framework import serializers
from alunos.views import cliente
from subidometro.models import *
from django.utils.timezone import make_aware
from datetime import datetime, date
from datetime import timedelta
from django.utils import timezone



class AlunoClientesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_clientes
        fields = ["id", "titulo", "estrangeiro", "tipo_cliente", "tipo_contrato",
                "sociedade", "cliente_antes_subidopro", "documento_antigo", "documento",
                "telefone", "email", "data_criacao",
                "rastreador", "status", "motivo_invalido",
                "descricao_invalido", "sem_pontuacao", "rastreador_analise", "campeonato", "aluno"]
        
    def update(self, instance, validated_data):
        """
        Método para atualizar o objeto Aluno_clientes.
        """
        novo_status = validated_data.get('status')
        instance = super().update(instance, validated_data)

        if novo_status == 2:
            instance.contratos.all().update(status=2)
        
        instance.save()
        return instance

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
        read_only_fields = ["pontos", "pontos_previsto", "valor_calculado"] # Adicione campos calculados como read-only

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

    def _calculate_points_and_values(self, validated_data, instance=None):
        """
        Método auxiliar para calcular pontos e valores, usado tanto em create quanto em update.
        """
        data_envio = validated_data.get("data", getattr(instance, 'data', date.today()))
        campeonato = validated_data.get("campeonato", getattr(instance, 'campeonato', None))
        contrato = validated_data.get("contrato", getattr(instance, 'contrato', None))
        valor = validated_data.get("valor", getattr(instance, 'valor', 0))

        if not campeonato:
            campeonato = Campeonato.objects.filter(ativo=True).first()
            validated_data["campeonato"] = campeonato

        pontos = 0
        pontos_previsto = 0
        valor_calculado = 0

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
            
        validated_data["pontos"] = pontos
        validated_data["pontos_previsto"] = pontos_previsto
        validated_data["valor_calculado"] = valor_calculado
        
        return validated_data

    def create(self, validated_data):
        validated_data = self._calculate_points_and_values(validated_data)
        envio = super().create(validated_data)

        cliente = validated_data.get("cliente")
        campeonato = validated_data.get("campeonato")
        contrato = validated_data.get("contrato")
        aluno = validated_data.get("aluno")
        valor = validated_data.get("valor")

        cliente_cont_envios = cliente.envios_cliente_cl.filter(status=3).count()
        cliente_pontos_contrato = cliente.cliente_aluno_contrato.filter(status=3).count()

        if cliente_cont_envios == 0 and campeonato and cliente_pontos_contrato == 0:
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
                    data=validated_data.get("data"),
                    data_cadastro=validated_data.get("data_cadastro") or make_aware(datetime.now()),
                    pontos=pontos_contrato,
                    status=0
                )
        return envio

    def update(self, instance, validated_data):
        old_status = instance.status
        old_valor = instance.valor
        old_data = instance.data

        instance.status = validated_data.get('status', old_status)
        instance.valor = validated_data.get('valor', old_valor)
        instance.data = validated_data.get('data', old_data)
        instance.descricao = validated_data.get('descricao', instance.descricao)
        instance.arquivo1 = validated_data.get('arquivo1', instance.arquivo1)
        instance.arquivo1_motivo = validated_data.get('arquivo1_motivo', instance.arquivo1_motivo)
        instance.arquivo1_status = validated_data.get('arquivo1_status', instance.arquivo1_status)
        instance.rastreador_analise = validated_data.get('rastreador_analise', instance.rastreador_analise)
        instance.status_motivo = validated_data.get('status_motivo', instance.status_motivo)
        instance.status_comentario = validated_data.get('status_comentario', instance.status_comentario)
        instance.semana = validated_data.get('semana', instance.semana)
        
        instance.aluno = validated_data.get('aluno', instance.aluno)
        instance.cliente = validated_data.get('cliente', instance.cliente)
        instance.contrato = validated_data.get('contrato', instance.contrato)
        instance.campeonato = validated_data.get('campeonato', instance.campeonato)

        validated_data = self._calculate_points_and_values(validated_data, instance=instance)
        instance.pontos = validated_data.get('pontos')
        instance.pontos_previsto = validated_data.get('pontos_previsto')
        instance.valor_calculado = validated_data.get('valor_calculado')
        
        

        if ('valor' in validated_data and validated_data['valor'] != old_valor) or \
           ('data' in validated_data and validated_data['data'] != old_data):

            aluno_contrato_obj = Aluno_contrato.objects.filter(envio=instance).first()

            if aluno_contrato_obj:
                valor_para_contrato = instance.valor
                if instance.contrato and instance.contrato.tipo_contrato == 2:
                    valor_para_contrato = float(instance.valor) * 0.1

                pontos_contrato_atualizados = self.gera_pontos_contrato(valor_para_contrato)
                
                aluno_contrato_obj.valor = valor_para_contrato
                aluno_contrato_obj.pontos = pontos_contrato_atualizados
                aluno_contrato_obj.data = instance.data
                aluno_contrato_obj.save()

        if ('status' in validated_data and validated_data['status'] == 2):
            instance.pontos = 0
            aluno_contrato_obj = Aluno_contrato.objects.filter(cliente=instance.cliente).first()
            cliente_cont_envios = instance.cliente.envios_cliente_cl.filter(status=3).count()
            if cliente_cont_envios == 1 and aluno_contrato_obj:
                aluno_contrato_obj.delete()


        elif ('status' in validated_data and validated_data['status'] == 3):
            instance.pontos = instance.pontos_previsto
            aluno_contrato_obj = Aluno_contrato.objects.filter(envio=instance).first()
            if aluno_contrato_obj:
                aluno_contrato_obj.status = 3
                aluno_contrato_obj.save()


        instance.save()
        return instance

class AlunoDesafioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_desafio
        fields = [
            "id", "aluno", "campeonato", "desafio", "descricao", "texto", 
            "rastreador_analise", "data_cadastro", "data_analise", "status", 
            "status_motivo", "status_comentario", "semana", "pontos", "pontos_previsto"
        ]
        read_only_fields = ["pontos", "pontos_previsto"] 

    def _calculate_points(self, desafio_obj, data_cadastro):
        """
        Função auxiliar para calcular os pontos com base na lógica do desafio e data de cadastro.
        """
        if not desafio_obj.data_inicio or not desafio_obj.data_fim:
            return 0 

        if timezone.is_naive(data_cadastro):
            data_cadastro = timezone.make_aware(data_cadastro, timezone.get_current_timezone())

        dias_desde_inicio = (data_cadastro - desafio_obj.data_inicio).days
        # dias_para_fim = (desafio_obj.data_fim - data_cadastro).days 

        pontos_calculados = 0

        if dias_desde_inicio <= 7 and desafio_obj.pontos_7_dias is not None:
            pontos_calculados = desafio_obj.pontos_7_dias
        elif dias_desde_inicio <= 14 and desafio_obj.pontos_14_dias is not None:
            pontos_calculados = desafio_obj.pontos_14_dias
        elif dias_desde_inicio <= 21 and desafio_obj.pontos_21_dias is not None:
            pontos_calculados = desafio_obj.pontos_21_dias
        else:
            if data_cadastro > desafio_obj.data_fim:
                pontos_calculados = 0
            else:
                pontos_calculados = 0 
        
        return pontos_calculados

    def create(self, validated_data):
        desafio_obj = validated_data.get("desafio")
        
        data_cadastro = validated_data.get("data_cadastro") 
        if not data_cadastro:
            data_cadastro = timezone.now()
            validated_data["data_cadastro"] = data_cadastro

        pontos_calculados = self._calculate_points(desafio_obj, data_cadastro)
        validated_data["pontos"] = pontos_calculados
        validated_data["pontos_previsto"] = pontos_calculados
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        desafio_obj = instance.desafio
        data_cadastro_atualizada = validated_data.get("data_cadastro", instance.data_cadastro)

        should_recalculate = False
        if "data_cadastro" in validated_data or "desafio" in validated_data:
            should_recalculate = True
    

        if should_recalculate:
            pontos_calculados = self._calculate_points(desafio_obj, data_cadastro_atualizada)
            instance.pontos = pontos_calculados
            instance.pontos_previsto = pontos_calculados
            instance.save()
        
        return instance

     
class AlunoCertificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_certificacao
        fields = ["id", "aluno", "campeonato", "descricao", "data_cadastro", "data_analise",
                "status", "status_motivo", "status_comentario", "semana", "pontos"]
        
    def create(self, validated_data):
        validated_data['tipo'] = 3

        return super().create(validated_data)

class AlunoManualSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_certificacao
        fields = ["id", "aluno", "campeonato", "descricao", "data_cadastro", "data_analise",
                "status", "status_motivo", "status_comentario", "semana", "pontos"]
        
    def create(self, validated_data):
        validated_data['tipo'] = 5
        return super().create(validated_data)

