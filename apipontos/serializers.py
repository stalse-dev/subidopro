from rest_framework import serializers
from alunos.views import cliente
from subidometro.models import *
from django.utils.timezone import make_aware
from datetime import datetime, date
from datetime import timedelta
from django.utils import timezone
from .utils import *
from django.db import transaction


class CampeonatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campeonato
        fields = [
            "id", "identificacao", "descricao", "data_inicio", "data_fim", "imagem", "regra_pdf", "turma", "ativo"
        ]
        read_only_fields = ["id"]

class AlunoClientesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_clientes
        fields = [
            "id", "titulo", "estrangeiro", "tipo_cliente", "tipo_contrato",
            "sociedade", "cliente_antes_subidopro", "documento_antigo", "documento",
            "telefone", "email", "data_criacao",
            "rastreador", "status", "motivo_invalido",
            "descricao_invalido", "sem_pontuacao", "rastreador_analise", "campeonato", "aluno"
        ]
        
    def update(self, instance, validated_data):
        novo_status = validated_data.get('status')
        instance = super().update(instance, validated_data)

        if novo_status == 2:
            instance.contratos.all().update(status=2)
            instance.envios_cliente_cl.all().update(status=2)
            instance.envios_cliente_cl.all().update(pontos=0)
            instance.alunosclientespontosestemesretencao_set.all().delete()
            instance.cliente_aluno_contrato.all().delete()

        return instance

class AlunoClientesContratosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_clientes_contratos
        fields = [
            "id", "cliente", "tipo_contrato", "valor_contrato", 
            "porcentagem_contrato", "data_contrato", "data_vencimento", 
            "data_criacao", "arquivo1", "status", 
            "motivo_invalido", "descricao_invalido", "rastreador_analise", "analise_data"
        ]
    
    def update(self, instance, validated_data):
        old_tipo_contrato = instance.tipo_contrato
        novo_status = validated_data.get('status')

        instance = super().update(instance, validated_data)

        novo_tipo_contrato = validated_data.get('tipo_contrato', instance.tipo_contrato)

        if novo_status == 2:
            instance.envios_contrato_cl.all().update(status=2)
            instance.envios_contrato_cl.all().update(pontos=0)
            instance.alunosclientespontosestemesretencao_set.all().delete()
            instance.contrato_aluno_contrato.all().delete()

        if old_tipo_contrato != novo_tipo_contrato:
            recalculate_contract_related_items(instance, novo_tipo_contrato == 2)
        
        return instance

class AlunoEnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno_envios
        fields = ["id", "aluno", "cliente", "contrato", "campeonato", "data", "descricao", "valor", "arquivo1", "arquivo1_motivo", "arquivo1_status",
                  "data_cadastro", "rastreador_analise", "status", "status_motivo", "status_comentario", "semana", "pontos", "pontos_previsto", "valor_calculado"]
        read_only_fields = ["pontos", "pontos_previsto", "valor_calculado"]

    def create(self, validated_data):
        calculated_data = calculate_points_and_values_for_entity(validated_data)
        validated_data.update(calculated_data)
        
        envio = super().create(validated_data)

        cliente = validated_data.get("cliente")
        campeonato = validated_data.get("campeonato")
        contrato = validated_data.get("contrato")
        aluno = validated_data.get("aluno")
        valor = validated_data.get("valor")

        cliente_pontos_contrato = cliente.cliente_aluno_contrato.count()

        if campeonato and cliente_pontos_contrato == 0:
            data_limite = campeonato.data_inicio
            if cliente.data_criacao and cliente.data_criacao.date() > data_limite and contrato.data_contrato and contrato.data_contrato > data_limite:
                valor_final_contrato = float(valor)
                if contrato.tipo_contrato == 2:
                    valor_final_contrato = valor_final_contrato * 0.1
                    contrato.valor_contrato = valor_final_contrato
                    contrato.save()
                
                pontos_contrato = gera_pontos_contrato(valor_final_contrato)
                data_envio = validated_data.get("data")
                print(f"Data de envio: {data_envio}, Data campeonato: {campeonato.data_inicio}")
                if campeonato and data_envio >= campeonato.data_inicio:
                    Aluno_contrato.objects.create(
                        campeonato=campeonato,
                        aluno=aluno,
                        cliente=cliente,
                        contrato=contrato,
                        envio=envio,
                        descricao=validated_data.get("descricao"),
                        valor=valor_final_contrato,
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

        calculated_data = calculate_points_and_values_for_entity(validated_data, instance=instance)
        
        instance.pontos = calculated_data.get('pontos')
        instance.pontos_previsto = calculated_data.get('pontos_previsto')
        instance.valor_calculado = calculated_data.get('valor_calculado')

        if ('valor' in validated_data and validated_data['valor'] != old_valor) or \
           ('data' in validated_data and validated_data['data'] != old_data):

            aluno_contrato_obj = Aluno_contrato.objects.filter(envio=instance).first()

            if aluno_contrato_obj:
                valor_para_contrato = instance.valor
                if instance.contrato and instance.contrato.tipo_contrato == 2:
                    valor_para_contrato = float(instance.valor) * 0.1

                pontos_contrato_atualizados = gera_pontos_contrato(valor_para_contrato)
                
                aluno_contrato_obj.valor = valor_para_contrato
                aluno_contrato_obj.pontos = pontos_contrato_atualizados
                aluno_contrato_obj.data = instance.data
                aluno_contrato_obj.save()

        if 'status' in validated_data and validated_data['status'] == 2:
            instance.pontos = 0
            aluno_contrato_obj = Aluno_contrato.objects.filter(cliente=instance.cliente).first()
            
            cliente_cont_envios_ativos = instance.cliente.envios_cliente_cl.filter(status=3).exclude(pk=instance.pk).count()
            
            if cliente_cont_envios_ativos == 0 and aluno_contrato_obj:
                aluno_contrato_obj.delete()

        elif 'status' in validated_data and validated_data['status'] == 3:
            instance.pontos = instance.pontos_previsto
            aluno_contrato_obj = Aluno_contrato.objects.filter(envio=instance).first()
            if aluno_contrato_obj:
                aluno_contrato_obj.status = 3
                aluno_contrato_obj.save()

        instance.save()
        return instance

class DesafioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Desafios
        fields = [
            "id", "titulo", "descricao", "data_inicio", "data_fim", 
            "pontos_7_dias", "pontos_14_dias", "pontos_21_dias", 
            "status"
        ]
        read_only_fields = ["id", "data_cadastro"]

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

        print(f"Calculando pontos para desafio: {desafio_obj.titulo}, dias desde início: {dias_desde_inicio}, data cadastro: {data_cadastro}")

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

class AlunoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alunos
        fields = ["id", "nome_completo", "email", "status", "nivel", "cla", "campeonato", "data_criacao"]
        read_only_fields = ["id", "data_criacao"]

    def _ativar_participacao(self, aluno: Alunos, campeonato_id: int):
        """
        Garante que existe uma participação (aluno, campeonato) ativa.
        Se já existir e estiver inativa, reativa (ativo=True, data_saida=None).
        """
        part, created = ParticipacaoCampeonato.objects.get_or_create(
            aluno=aluno,
            campeonato_id=campeonato_id,
            defaults={"ativo": True},
        )
        if not created and (not part.ativo or part.data_saida):
            part.ativo = True
            part.data_saida = None
            # Se quiser resetar a data_entrada a cada reativação, descomente:
            # part.data_entrada = timezone.now()
            part.save(update_fields=["ativo", "data_saida"])  # adicione "data_entrada" se for resetar

    def _fechar_participacao_antiga(self, aluno: Alunos, old_camp_id: int):
        """
        Fecha a participação ativa do campeonato anterior, se existir.
        """
        if not old_camp_id:
            return
        ParticipacaoCampeonato.objects.filter(
            aluno=aluno,
            campeonato_id=old_camp_id,
            ativo=True
        ).update(ativo=False, data_saida=timezone.now())

    @transaction.atomic
    def create(self, validated_data):
        aluno = super().create(validated_data)
        if aluno.campeonato_id:
            self._ativar_participacao(aluno, aluno.campeonato_id)
        return aluno

    @transaction.atomic
    def update(self, instance, validated_data):
        old_camp_id = instance.campeonato_id  # antes de aplicar update
        aluno = super().update(instance, validated_data)
        new_camp_id = aluno.campeonato_id

        print(f"Atualizando participação do aluno {aluno.id} de {old_camp_id} para {new_camp_id}")

        if old_camp_id != new_camp_id:
            # fechamos a anterior (se havia)
            self._fechar_participacao_antiga(aluno, old_camp_id)
            # ativamos (ou criamos) a nova (se houver)
            if new_camp_id:
                self._ativar_participacao(aluno, new_camp_id)

        return aluno

class ClaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentoria_cla
        fields = ["id", "campeonato", "nome", "descricao", "sigla"]
        read_only_fields = ["id"]
