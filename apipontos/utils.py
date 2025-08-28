from datetime import date
# from django.db.models import Q # Não necessário se não for usado
from subidometro.models import Campeonato # Certifique-se de que este import está correto

def gera_pontos(valor):
    """
    Calcula pontos com base em um valor.
    """
    valor = float(valor)
    return int((valor // 100) * 10)

def gera_pontos_contrato(valor):
    """
    Calcula pontos específicos para contratos com base em faixas de valor.
    """
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

def calculate_points_and_values_for_entity(data_dict, instance=None):
    """
    Calcula pontos e valores para uma entidade (Aluno_clientes_contratos ou Aluno_envios).
    Esta função é agnóstica ao tipo específico de serializer e lida com dados brutos.

    :param data_dict: Um dicionário de dados (validated_data ou atributos do instance).
    :param instance: A instância do objeto sendo atualizado (opcional).
    :return: Um dicionário com os campos de pontos e valores calculados.
    """
    data_envio = data_dict.get("data", getattr(instance, 'data', date.today()))
    campeonato = data_dict.get("campeonato", getattr(instance, 'campeonato', None))
    contrato = data_dict.get("contrato", getattr(instance, 'contrato', None))
    valor = data_dict.get("valor", getattr(instance, 'valor', 0))

    pontos = 0
    pontos_previsto = 0
    valor_calculado = 0

    # Cálculo padrão de pontos e valor calculado
    if contrato and contrato.tipo_contrato == 2:
        valor_minimo = float(valor) * 0.1
        valor_calculado = valor_minimo
    else:
        valor_calculado = float(valor) # Garante que valor_calculado é um float

    if campeonato and data_envio >= campeonato.data_inicio and contrato and contrato.data_contrato > campeonato.data_inicio:
        if contrato and contrato.tipo_contrato == 2:
            pontos = gera_pontos(valor_minimo)
            pontos_previsto = pontos
        else:
            pontos = gera_pontos(valor)
            pontos_previsto = pontos
    else:
        pontos = 0
        pontos_previsto = 0
        
    return {
        "pontos": pontos,
        "pontos_previsto": pontos_previsto,
        "valor_calculado": valor_calculado,
        "campeonato": campeonato # Retorna o campeonato, caso tenha sido encontrado aqui
    }

def recalculate_contract_related_items(instance, apply_ten_percent_rule):
    """
    Recalcula pontos e valores de envios e contratos relacionados a um Aluno_clientes_contratos,
    com base na regra dos 10%.
    """

    envios = instance.envios_contrato_cl.all() 
    for envio in envios:
        current_envio_valor = float(envio.valor)
        if apply_ten_percent_rule:
            current_envio_valor = current_envio_valor * 0.1
        
        envio.pontos = gera_pontos(current_envio_valor)
        envio.pontos_previsto = envio.pontos
        envio.valor_calculado = current_envio_valor
        envio.save()

    envio_aluno_contrato = instance.contrato_aluno_contrato.first()
    if envio_aluno_contrato:
        envios = instance.envios_contrato_cl.filter(status=3).first()
        if envios:
            pontos_envio = gera_pontos_contrato(float(envios.valor_calculado))
            envio_aluno_contrato.pontos = pontos_envio
            envio_aluno_contrato.valor = float(envios.valor_calculado)
            envio_aluno_contrato.save()