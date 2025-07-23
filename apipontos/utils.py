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

    if not campeonato:
        campeonato = Campeonato.objects.filter(ativo=True).first()
        # Se você precisa que 'campeonato' seja setado no validated_data,
        # você precisará passá-lo de volta ou modificar o dicionário de entrada.
        # Para esta função utilitária, vamos apenas usá-lo para o cálculo.

    pontos = 0
    pontos_previsto = 0
    valor_calculado = 0

    # Cálculo padrão de pontos e valor calculado
    if contrato and contrato.tipo_contrato == 2:
        valor_minimo = float(valor) * 0.1
        valor_calculado = valor_minimo
    else:
        valor_calculado = float(valor) # Garante que valor_calculado é um float

    if campeonato and data_envio >= campeonato.data_inicio:
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
    # Lógica para envios relacionados ao contrato
    # Mantemos o filtro status=3 pois Aluno_envios (envios_contrato_cl) possui campo status.
    envios = instance.envios_contrato_cl.filter(status=3) 
    for envio in envios:
        # ATENÇÃO: Se 'envio.valor' deve ser o valor original, você precisará de um campo 'valor_original'
        # no modelo Aluno_envios, e usá-lo aqui.
        current_envio_valor = float(envio.valor)
        if apply_ten_percent_rule:
            current_envio_valor = current_envio_valor * 0.1
        
        envio.pontos = gera_pontos(current_envio_valor)
        envio.pontos_previsto = envio.pontos
        envio.valor_calculado = current_envio_valor
        envio.save()
    
    # Lógica para o contrato de retenção (AlunoClientesPontosEsteMesRetencao)
    # REMOVIDO: O filtro `status=3` daqui, pois o erro indica que este modelo não tem campo 'status'.
    # Se você precisa de algum filtro aqui, deve usar um dos campos disponíveis na lista do erro.
    contrato_retencao = instance.alunosclientespontosestemesretencao_set.first() 
    if contrato_retencao:
        # Aqui, estamos usando 'contrato_retencao.valor_contrato' como o valor de base
        # É fundamental que este campo represente o valor correto para a pontuação do contrato.
        valor_para_contrato_pontos = float(contrato_retencao.valor_contrato)
        if apply_ten_percent_rule:
            # Se a regra dos 10% se aplica ao valor_contrato em si, ajuste aqui.
            valor_para_contrato_pontos = valor_para_contrato_pontos * 0.1 
        
        contrato_retencao.pontos = gera_pontos_contrato(valor_para_contrato_pontos)
        contrato_retencao.pontos_previsto = contrato_retencao.pontos # Assumindo que pontos_previsto é igual a pontos aqui
        contrato_retencao.save()