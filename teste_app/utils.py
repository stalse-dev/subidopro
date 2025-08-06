import requests
from datetime import date, timedelta
import time
from calculadora_pontos.utils import *
from dateutil.relativedelta import relativedelta
from subidometro.models import *

BASE_URL = "http://127.0.0.1:8000/pontos/"
AUTH_TOKEN = "Token c586814b447778525319c9e4237b52ce74d307c2"

HEADERS = {
    "Authorization": AUTH_TOKEN,
    "Content-Type": "application/json"
}

### POST TEST FUNCTIONS ###

def test_post_campeonato(data_inicio, data_fim):
    url = f"{BASE_URL}campeonato_criar/"
    if data_inicio == None:
        data_inicio = (date.today() - timedelta(days=14)).strftime("%Y-%m-%d")
    if data_fim == None:
        data_fim = (date.today() + timedelta(days=180)).strftime("%Y-%m-%d")

    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    payload = {
        "identificacao": "Campeonato Teste",
        "descricao": "Descrição de teste",
        "data_inicio": data_inicio_str,
        "data_fim": data_fim_str,
        "imagem": "Teste.com",
        "regra_pdf": "Test",
        "turma": 1,
        "ativo": True
    }

    response = requests.post(url, json=payload, headers=HEADERS)
    return response.json().get("id")

def test_post_cla(campeonato_id):
    url = f"{BASE_URL}cla_criar/"
    payload = {
        "campeonato": campeonato_id,
        "nome": "CLA Teste",
        "descricao": "Descrição do CLA de teste",
        "sigla": "CLA"
    }

    response = requests.post(url, json=payload, headers=HEADERS)
    if response.status_code != 201:
        print("❌ Erro ao criar CLA:", response.status_code, response.json())
        return None
    return response.json().get("id")

def test_post_aluno(campeonato_id, cla_id):
    url = f"{BASE_URL}aluno_criar/"
    payload =  { 
        "nome_completo": "João da Silva",
        "email": "joao@teste.com",
        "status": "ACTIVE",
        "nivel": 7,
        "cla": cla_id,
        "campeonato": campeonato_id,
        "data_criacao": str(date.today())
    }

    response = requests.post(url, json=payload, headers=HEADERS)
    return response.json().get("id")

def test_post_cliente(campeonato_id, aluno_id):
    url = f"{BASE_URL}cliente_criar/"
    payload = {
        "titulo": "TESTE CLIENTE BASE",
        "tipo_cliente": 1,
        "tipo_contrato": 2,
        "documento": "12345678901",
        "telefone": "11999999999",
        "email": "cliente1@teste.com",
        "data_criacao": str(date.today()),
        "status": 0,
        "campeonato": campeonato_id,
        "aluno": aluno_id
    }

    response = requests.post(url, json=payload, headers=HEADERS)
    return response.json().get("id")

def test_post_contrato(cliente_id, tipo_contrato=1, data_contrato=str(date.today())):
    url = f"{BASE_URL}contrato_criar/"

    payload = {
        "cliente": cliente_id,
        "tipo_contrato": tipo_contrato,
        "valor_contrato": "1000.00",
        "porcentagem_contrato": 10,
        "data_contrato": data_contrato,
        "data_vencimento": str(date.today() + timedelta(days=365)),
        "data_criacao": str(date.today()),
        "arquivo1": None,
        "status": 0
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    if response.status_code != 201:
        print("❌ Erro ao criar contrato:", response.status_code, response.json())
        return None
    return response.json().get("id")

def test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, data_recebimento, data_cadastro, valor="1000.00"):
    url = f"{BASE_URL}envio_criar/"

    campeonato = Campeonato.objects.filter(id=campeonato_id).first()
    semana = calcular_semana_vigente(campeonato)

    payload = {
        "aluno": aluno_id,
        "cliente": cliente_id,
        "contrato": contrato_id,
        "campeonato": campeonato_id,
        "data": data_recebimento,
        "descricao": "Envio de documento XPTO",
        "valor": valor,
        "arquivo1": 'http://example.com/arquivo1.pdf',
        "data_cadastro": data_cadastro,
        "status": 0,
        "semana": semana
    }


    response = requests.post(url, json=payload, headers=HEADERS)
    if response.status_code != 201:
        print("❌ Erro ao criar envio:", response.status_code, response.json())
        return None
    return response.json().get("id")

### DELETE TEST FUNCTIONS ###

def test_delete_campeonato(campeonato_id):
    url = f"{BASE_URL}campeonato_detalhes/{campeonato_id}/"
    response = requests.delete(url, headers=HEADERS)
    print("🔹 DELETE - Excluir Campeonato")
    print(response.status_code)

def test_delete_cla(cla_id):
    url = f"{BASE_URL}cla_detalhes/{cla_id}/"
    response = requests.delete(url, headers=HEADERS)
    print("🔹 DELETE - Excluir CLA")
    print(response.status_code)

def test_delete_aluno(aluno_id):
    url = f"{BASE_URL}aluno_detalhes/{aluno_id}/"
    response = requests.delete(url, headers=HEADERS)
    print("🔹 DELETE - Excluir Aluno")
    print(response.status_code)

def test_delete_cliente(cliente_id):
    url = f"{BASE_URL}cliente_detalhes/{cliente_id}/"
    response = requests.delete(url, headers=HEADERS)
    print("🔹 DELETE - Excluir Cliente")
    print(response.status_code)

def test_delete_contrato(contrato_id):
    url = f"{BASE_URL}contrato_detalhes/{contrato_id}/"
    response = requests.delete(url, headers=HEADERS)
    print("🔹 DELETE - Excluir Contrato")
    print(response.status_code)

def test_delete_envio(envio_id):
    url = f"{BASE_URL}envio_detalhes/{envio_id}/"
    response = requests.delete(url, headers=HEADERS)
    print("🔹 DELETE - Excluir Envio")
    print(response.status_code)

### PATCH TEST FUNCTIONS ###

def test_patch_cliente(cliente_id, status):
    url = f"{BASE_URL}cliente_detalhes/{cliente_id}/"
    payload = {
        "status": status
    }
    response = requests.patch(url, json=payload, headers=HEADERS)
    print("🔹 PATCH - Atualizar Cliente")
    return response.json() if response.status_code == 200 else None

def test_patch_contrato(contrato_id, tipo_contrato, status=1):
    url = f"{BASE_URL}contrato_detalhes/{contrato_id}/"
    payload = {
        "tipo_contrato": tipo_contrato,
        "status": status
    }
    response = requests.patch(url, json=payload, headers=HEADERS)
    print("🔹 PATCH - Atualizar Contrato")
    return response.json() if response.status_code == 200 else None

def test_patch_envio(envio_id, status):
    url = f"{BASE_URL}envio_detalhes/{envio_id}/"
    payload = {
        "status": status
    }

    response = requests.patch(url, json=payload, headers=HEADERS)
    print("🔹 PATCH - Atualizar Envio")
    return response.json() if response.status_code == 200 else None

### GET TEST FUNCTIONS ###

def test_get_envio(envio_id):
    url = f"{BASE_URL}envio_detalhes/{envio_id}/"
    response = requests.get(url, headers=HEADERS)
    print("🔹 GET - Detalhes do Envio")
    return response.json() if response.status_code == 200 else None

### MICRO TEST FUNCTIONS ###

def test_aprove_envio(campeonato_id, aluno_id, cliente_id, contrato_id):
    print(" ➡️  Criando envio para ser aprovado...")
    envio_id = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "1000.00")
    print(f"🔹 Envio criado com ID: {envio_id}\n")
    test_patch_envio(envio_id, 3)
    pontos_json = test_get_envio(envio_id)
    valor_calculado = pontos_json.get('valor_calculado')
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 100.0:
        print("🔹 Pontos recebidos corretamente: 100")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False

    if float(valor_calculado) == 1000.0:
        print("🔹 Valor calculado recebido corretamente: 1000.0")
    else:
        print(f"❌ Valor calculado recebido incorretamente: {valor_calculado}")
        return False

    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if not pontos_cliente:
        print("❌ Não foi possível encontrar pontos do cliente.")
        return False
    else:
        if pontos_cliente.pontos == 480.0:
            print("🔹 Pontos do cliente recebidos corretamente: 480")
        else:
            print(f"❌ Pontos do cliente recebidos incorretamente: {pontos_cliente.pontos}")

    test_delete_envio(envio_id)

    print("✅  Teste de aprovação de envio concluído.")
    return True

def test_reprove_envio(campeonato_id, aluno_id, cliente_id, contrato_id):
    print(" ➡️  Reprovando envio...")
    envio_id = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "10000.00")
    print(f"🔹 Envio criado com ID: {envio_id}\n")
    test_patch_envio(envio_id, 2)
    pontos_json = test_get_envio(envio_id)
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 0.0:
        print("🔹 Pontos recebidos corretamente: 0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")

    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if pontos_cliente:
        print("❌ Reprovação não deveria ter pontos do cliente.")
        return False
    
    test_delete_envio(envio_id)
    print("✅  Teste de reprovação de envio concluído.")
    return True

def test_aprove_contrato_coproducao_envio(campeonato_id, aluno_id, cliente_id):
    contrato_id = test_post_contrato(cliente_id, 2)
    if not contrato_id:
        print("❌ Não foi possível criar contrato para testar.")
        return False
    print(" ➡️  Criando envio para ser aprovado...")
    envio_id = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "20000.00")
    print(f"🔹 Envio criado com ID: {envio_id}\n")
    test_patch_envio(envio_id, 3)
    pontos_json = test_get_envio(envio_id)
    valor_calculado = pontos_json.get('valor_calculado')
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 200.0:
        print("🔹 Pontos recebidos corretamente: 200")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False

    if float(valor_calculado) == 2000.0:
        print("🔹 Valor calculado recebido corretamente: 2000.0")
    else:
        print(f"❌ Valor calculado recebido incorretamente: {valor_calculado}")
        return False

    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if not pontos_cliente:
        print("❌ Não foi possível encontrar pontos do cliente.")
        return False
    else:
        if pontos_cliente.pontos == 480.0:
            print("🔹 Pontos do cliente recebidos corretamente: 480")
        else:
            print(f"❌ Pontos do cliente recebidos incorretamente: {pontos_cliente.pontos}")

    test_delete_envio(envio_id)
    print("✅  Teste de aprovação de envio concluído.")
    return True

def test_reprove_data_envio(campeonato_id, aluno_id, cliente_id, contrato_id):
    print(" ➡️  Reprovando envio com data de recebimento inválida...")
    campeonato = Campeonato.objects.filter(id=campeonato_id).first()
    data_recbimento = campeonato.data_inicio - relativedelta(days=1)
    envio_id = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(data_recbimento), str(date.today()), "10000.00")
    print(f"🔹 Envio criado com ID: {envio_id}\n")
    test_patch_envio(envio_id, 3)
    pontos_json = test_get_envio(envio_id)
    pontos = pontos_json.get('pontos')
    valor_calculado = pontos_json.get('valor_calculado')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 0.0:
        print("🔹 Pontos recebidos corretamente: 0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")

    if float(valor_calculado) == 10000:
        print("🔹 Valor calculado recebido corretamente: 10000")
    else:
        print(f"❌ Valor calculado recebido incorretamente: {valor_calculado}")

    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if pontos_cliente:
        print("❌ Reprovação não deveria ter pontos do cliente.")
        return False

    test_delete_envio(envio_id)
    print("✅  Teste de reprovação de envio concluído.")
    return True

def test_reprove_data_contrato(campeonato_id, aluno_id, cliente_id):
    print(" ➡️  Reprovando envio com data de contrato inválida...")
    campeonato = Campeonato.objects.filter(id=campeonato_id).first()
    data_invalida = campeonato.data_inicio - relativedelta(months=1)
    contrato_id = test_post_contrato(cliente_id, 1, str(data_invalida))
    if not contrato_id:
        print("❌ Não foi possível criar contrato para testar.")
        return False

    envio_id = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "30000.00")

    print(f"🔹 Envio criado com ID: {envio_id}\n")

    test_patch_envio(envio_id, 3)

    pontos_json = test_get_envio(envio_id)
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 0:
        print("🔹 Pontos recebidos corretamente: 0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False
    
    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if pontos_cliente:
        print("❌ Reprovação não deveria ter pontos do cliente.")
        return False

    #test_delete_envio(envio_id)
    print("✅  Teste de reprovação de envio concluído.")
    return True

def test_update_contrato(campeonato_id, aluno_id, cliente_id):
    print(" ➡️  Criando envio para testar atualização de contrato...")
    contrato_id = test_post_contrato(cliente_id, 1)
    if not contrato_id:
        print("❌ Não foi possível criar contrato para testar.")
        return False
    print(f"🔹 Contrato criado com ID: {contrato_id}\n")

    envio_id = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "30000.00")

    print(f"🔹 Envio criado com ID: {envio_id}\n")

    test_patch_envio(envio_id, 3)

    pontos_json = test_get_envio(envio_id)
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 3000.0:
        print("🔹 Pontos recebidos corretamente: 3000.0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False
    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if not pontos_cliente:
        print("❌ Não foi possível encontrar pontos do cliente.")
        return False
    else:
        if pontos_cliente.pontos == 2460.0:
            print("🔹 Pontos do cliente recebidos corretamente: 2460")
        else:
            print(f"❌ Pontos do cliente recebidos incorretamente: {pontos_cliente.pontos}")

    test_patch_contrato(contrato_id, 2)

    pontos_json = test_get_envio(envio_id)
    pontos = pontos_json.get('pontos')
    valor_calculado = pontos_json.get('valor_calculado')
    print(f" 🔹 Pontos recebidos após atualização do contrato: {pontos}")

    if float(valor_calculado) == 3000.0:
        print("🔹 Valor calculado recebido corretamente após atualização do contrato: 3000")
    else:
        print(f"❌ Valor calculado recebido incorretamente após atualização do contrato: {valor_calculado}")

    if float(pontos) == 300.0:
        print("🔹 Pontos recebidos corretamente após atualização do contrato: 300")
    else:
        print(f"❌ Pontos recebidos incorretamente após atualização do contrato: {pontos}")
        return False
    
    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if not pontos_cliente:
        print("❌ Não foi possível encontrar pontos do cliente.")
        return False
    else:
        if pontos_cliente.pontos == 1080.0:
            print("🔹 Pontos do cliente recebidos corretamente após atualização do contrato: 1080")
        else:
            print(f"❌ Pontos do cliente recebidos incorretamente após atualização do contrato: {pontos_cliente.pontos}")

    test_delete_contrato(contrato_id)
    print("✅  Teste de atualização de contrato concluído.")
    return True

def test_invalid_cliente(campeonato_id, aluno_id):
    print(" ➡️  Criando envio com cliente inválido...")

    cliente_id = test_post_cliente(campeonato_id, aluno_id)
    if not cliente_id:
        print("❌ Não foi possível criar cliente para testar.")
        return False
    print(f"🔹 Cliente criado com ID: {cliente_id}\n")

    contrato_id = test_post_contrato(cliente_id, 1)
    if not contrato_id:
        print("❌ Não foi possível criar contrato para testar.")
        return False
    print(f"🔹 Contrato criado com ID: {contrato_id}\n")

    envio_id = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "1500.00")
    if not envio_id:
        print("❌ Não foi possível criar envio para testar.")
        return False
    
    print(f"🔹 Envio criado com ID: {envio_id}\n")

    test_patch_envio(envio_id, 3)
    pontos_json = test_get_envio(envio_id)
    valor_calculado = pontos_json.get('valor_calculado')
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 150.0:
        print("🔹 Pontos recebidos corretamente: 150")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False
    
    if float(valor_calculado) == 1500.0:
        print("🔹 Valor calculado recebido corretamente: 1500.0")
    else:
        print(f"❌ Valor calculado recebido incorretamente: {valor_calculado}")
        return False
    
    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if not pontos_cliente:
        print("❌ Não foi possível encontrar pontos do cliente.")
        return False
    else:
        if pontos_cliente.pontos == 480.0:
            print("🔹 Pontos do cliente recebidos corretamente: 480")
        else:
            print(f"❌ Pontos do cliente recebidos incorretamente: {pontos_cliente.pontos}")
    
    test_patch_cliente(cliente_id, 2)

    time.sleep(1)

    pontos_json = test_get_envio(envio_id)

    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos após inativar cliente: {pontos}, tipo: {type(pontos)}")

    if float(pontos) == 0.0:
        print("🔹 Pontos recebidos corretamente após inativar cliente: 0")
    else:
        print(f"❌ Pontos recebidos incorretamente após inativar cliente: {pontos}")
        return False  
    
    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if pontos_cliente:
        print("❌ Reprovação não deveria ter pontos do cliente.")
        return False

    print("✅  Teste de inativação de cliente concluído.")
    test_delete_envio(envio_id)
    return True

def test_invalid_contrato(campeonato_id, aluno_id):
    print(" ➡️  Criando envio com contrato inválido...")

    cliente_id = test_post_cliente(campeonato_id, aluno_id)
    if not cliente_id:
        print("❌ Não foi possível criar cliente para testar.")
        return False
    print(f"🔹 Cliente criado com ID: {cliente_id}\n")

    contrato_id = test_post_contrato(cliente_id, 1)
    if not contrato_id:
        print("❌ Não foi possível criar contrato para testar.")
        return False
    print(f"🔹 Contrato criado com ID: {contrato_id}\n")

    envio_id = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "1500.00")
    if not envio_id:
        print("❌ Não foi possível criar envio para testar.")
        return False
    
    print(f"🔹 Envio criado com ID: {envio_id}\n")

    test_patch_envio(envio_id, 3)
    pontos_json = test_get_envio(envio_id)
    valor_calculado = pontos_json.get('valor_calculado')
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 150.0:
        print("🔹 Pontos recebidos corretamente: 150")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False
    
    if float(valor_calculado) == 1500.0:
        print("🔹 Valor calculado recebido corretamente: 1500.0")
    else:
        print(f"❌ Valor calculado recebido incorretamente: {valor_calculado}")
        return False
    
    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if not pontos_cliente:
        print("❌ Não foi possível encontrar pontos do cliente.")
        return False
    else:
        if pontos_cliente.pontos == 480.0:
            print("🔹 Pontos do cliente recebidos corretamente: 480")
        else:
            print(f"❌ Pontos do cliente recebidos incorretamente: {pontos_cliente.pontos}")
    
    test_patch_contrato(contrato_id, 1, 2)

    time.sleep(1)

    pontos_json = test_get_envio(envio_id)

    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos após inativar cliente: {pontos}, tipo: {type(pontos)}")

    if float(pontos) == 0.0:
        print("🔹 Pontos recebidos corretamente após inativar cliente: 0")
    else:
        print(f"❌ Pontos recebidos incorretamente após inativar cliente: {pontos}")
        return False  
    
    pontos_cliente = Aluno_contrato.objects.filter(cliente__id=cliente_id).first()
    if pontos_cliente:
        print("❌ Reprovação não deveria ter pontos do cliente.")
        return False
    
    print("✅  Teste de inativação de contrato concluído.")
    test_delete_envio(envio_id)
    return True

def test_balancemanto(campeonato_id, aluno_id):
    print(" ➡️  Criando envio para testar balanço de pontos...")

    cliente_id = test_post_cliente(campeonato_id, aluno_id)
    if not cliente_id:
        print("❌ Não foi possível criar cliente para testar.")
        return False
    print(f"🔹 Cliente criado com ID: {cliente_id}\n")

    contrato_id = test_post_contrato(cliente_id, 1)
    if not contrato_id:
        print("❌ Não foi possível criar contrato para testar.")
        return False
    print(f"🔹 Contrato criado com ID: {contrato_id}\n")

    envio_id_01 = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "10000.00")

    if not envio_id_01:
        print("❌ Não foi possível criar envio para testar.")
        return False
    print(f"🔹 Envio criado com ID: {envio_id_01}\n")

    time.sleep(1)
    test_patch_envio(envio_id_01, 3)

    pontos_json = test_get_envio(envio_id_01)
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")

    if float(pontos) == 1000.0:
        print("🔹 Pontos recebidos corretamente: 1000.0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False

    envio_id_02 = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "15000.00")
    
    if not envio_id_02:
        print("❌ Não foi possível criar envio para testar.")
        return False
    
    time.sleep(1)
    print(f"🔹 Envio criado com ID: {envio_id_02}\n")

    test_patch_envio(envio_id_02, 3)

    pontos_json = test_get_envio(envio_id_02)
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 1500.0:
        print("🔹 Pontos recebidos corretamente: 1500.0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False
    
    time.sleep(1)
    envio_id_03 = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()), str(date.today()), "20000.00")
    if not envio_id_03:
        print("❌ Não foi possível criar envio para testar.")
        return False

    print(f"🔹 Envio criado com ID: {envio_id_03}\n")

    test_patch_envio(envio_id_03, 3)

    pontos_json = test_get_envio(envio_id_03)
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 2000.0:
        print("🔹 Pontos recebidos corretamente: 2000.0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False
    
    total_aprovado_qs = Aluno_envios.objects.filter(
        aluno_id=aluno_id,
        status=3,
        campeonato__id=campeonato_id
    ).aggregate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )

    if total_aprovado_qs.get('total') == 4500.0:
        print("🔹 Total de pontos aprovados corretamente: 4500.0")
    else:
        print(f"❌ Total de pontos aprovados incorretamente: {total_aprovado_qs.get('total')}")
        return False
    
    time.sleep(1)
    calcula_balanceamento()
    time.sleep(1)

    print("🔹 Balanceamento de pontos calculado com sucesso.")

    total_aprovado_qs = Aluno_envios.objects.filter(
        aluno_id=aluno_id,
        status=3,
        campeonato__id=campeonato_id
    ).aggregate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )

    if total_aprovado_qs.get('total') == 3000.0:
        print("🔹 Total de pontos aprovados corretamente: 3000.0")
    else:
        print(f"❌ Total de pontos aprovados incorretamente: {total_aprovado_qs.get('total')}")
        return False

    print("✅  Teste de balanceamento de pontos concluído.")

def test_retencao():
    print("\n🚀 Iniciando testes de retenção...\n")

    inicio_campeonato = timezone.now().date() - relativedelta(months=3)
    fim_campeonato = inicio_campeonato + relativedelta(months=7)

    print("Inicio do campeonato:", inicio_campeonato)
    print("Fim do campeonato:", fim_campeonato)

    campeonato_id = test_post_campeonato(inicio_campeonato, fim_campeonato)
    if not campeonato_id:
        print("❌ Não foi possível criar campeonato para testar.")
        return False
    print(f"🔹 Campeonato criado com ID: {campeonato_id}\n")

    cla_id = test_post_cla(campeonato_id)
    if not cla_id:
        print("❌ Não foi possível criar CLA para testar.")
        return False
    print(f"🔹 CLA criado com ID: {cla_id}\n")

    aluno_id = test_post_aluno(campeonato_id, cla_id)
    if not aluno_id:
        print("❌ Não foi possível criar aluno para testar.")
        return False
    print(f"🔹 Aluno criado com ID: {aluno_id}\n")

    campeonato = Campeonato.objects.filter(id=campeonato_id).first()
    if not campeonato:
        print("❌ Campeonato não encontrado.")
        return False
    data_inicio = campeonato.data_inicio

    cliente_id = test_post_cliente(campeonato_id, aluno_id)
    if not cliente_id:
        print("❌ Não foi possível criar cliente para testar.")
        return False
    print(f"🔹 Cliente criado com ID: {cliente_id}\n")

    mes_anterior = data_inicio - relativedelta(months=2)
    
    print("❌❌❌❌❌ mes anterior:", mes_anterior.strftime('%Y-%m'))

    contrato_id = test_post_contrato(cliente_id, 1)
    if not contrato_id:
        print("❌ Não foi possível criar contrato para testar.")
        return False
    print(f"🔹 Contrato criado com ID: {contrato_id}\n")


    mes_primeiro = data_inicio + relativedelta(days=1)
    mes_segundo = data_inicio + relativedelta(months=1)
    mes_terceiro = data_inicio + relativedelta(months=2)
    mes_quarto = data_inicio + relativedelta(months=3)

    print(f"🔹 Meses de teste: {mes_primeiro.strftime('%Y-%m')}, {mes_segundo.strftime('%Y-%m')}, {mes_terceiro.strftime('%Y-%m')}, {mes_quarto.strftime('%Y-%m')}\n")

    envio_id_primeiro_mes = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(mes_primeiro), str(mes_primeiro), "1000.00")

    if not envio_id_primeiro_mes:
        print("❌ Não foi possível criar envio para testar.")
        return False
    print(f"🔹 Envio criado com ID: {envio_id_primeiro_mes}\n")

    time.sleep(1)
    test_patch_envio(envio_id_primeiro_mes, 3)
    pontos_json = test_get_envio(envio_id_primeiro_mes)
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")

    if float(pontos) == 100.0:
        print("🔹 Pontos recebidos corretamente primeiro mês: 100.0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False

    envio_id_segundo_mes = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(mes_segundo), str(mes_segundo), "1000.00")

    if not envio_id_segundo_mes:
        print("❌ Não foi possível criar envio para testar.")
        return False
    print(f"🔹 Envio criado com ID: {envio_id_segundo_mes}\n")

    time.sleep(1)
    test_patch_envio(envio_id_segundo_mes, 3)
    pontos_json = test_get_envio(envio_id_segundo_mes)
    pontos = pontos_json.get('pontos')
    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")

    if float(pontos) == 100.0:
        print("🔹 Pontos recebidos corretamente segundo mês: 100.0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False

    envio_id_terceiro_mes = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(mes_terceiro), str(mes_terceiro), "1000.00")

    if not envio_id_terceiro_mes:
        print("❌ Não foi possível criar envio para testar.")
        return False
    print(f"🔹 Envio criado com ID: {envio_id_terceiro_mes}\n")

    time.sleep(1)
    test_patch_envio(envio_id_terceiro_mes, 3)
    pontos_json = test_get_envio(envio_id_terceiro_mes)
    pontos = pontos_json.get('pontos')

    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 100.0:
        print("🔹 Pontos recebidos corretamente terceiro mês: 100.0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False
    

    envio_id_quarto_mes = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(mes_quarto), str(mes_quarto), "1000.00")
    if not envio_id_quarto_mes:
        print("❌ Não foi possível criar envio para testar.")
        return False
    
    print(f"🔹 Envio criado com ID: {envio_id_quarto_mes}\n")
    time.sleep(1)
    test_patch_envio(envio_id_quarto_mes, 3)
    pontos_json = test_get_envio(envio_id_quarto_mes)
    pontos = pontos_json.get('pontos')

    print(f" 🔹 Pontos recebidos: {pontos}, tipo: {type(pontos)}")
    if float(pontos) == 100.0:
        print("🔹 Pontos recebidos corretamente terceiro mês: 100.0")
    else:
        print(f"❌ Pontos recebidos incorretamente: {pontos}")
        return False

    campeonato = Campeonato.objects.filter(id=campeonato_id).first()

    data_atual_loop = campeonato.data_inicio
    hoje = timezone.now().date()

    while data_atual_loop <= hoje:
        data_referencia_para_calculo = data_atual_loop.replace(day=1)

        print(f"\n--- Processando retenção para o mês de {data_referencia_para_calculo.strftime('%Y-%m')} ---")

        clientes_retidos = calculo_retencao(data_referencia_para_calculo, campeonato)

        if clientes_retidos:
            print(f"Detalhes das retenções para {data_referencia_para_calculo.strftime('%Y-%m')}:")
            for item in clientes_retidos:
                print(f"  Aluno ID: {item['aluno_id']}, Cliente ID: {item['cliente_id']}, Envio ID: {item['envio_id']}, Pontos: {item['pontos_retencao']}")
        else:
            print(f"Nenhuma retenção processada para {data_referencia_para_calculo.strftime('%Y-%m')}.")

        proximo_mes = (data_atual_loop.replace(day=1) + timedelta(days=32)).replace(day=1)
        data_atual_loop = proximo_mes

    pontos_retencao = Alunos_clientes_pontos_meses_retencao.objects.filter(
        aluno_id=aluno_id,
        campeonato_id=campeonato_id
    ).aggregate(
        total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )
    print(f"\n🔹 Total de pontos de retenção para o aluno {aluno_id} no campeonato {campeonato_id}: {pontos_retencao.get('total')}")
    if pontos_retencao.get('total') == 960.0:
        print("🔹 Pontos de retenção calculados corretamente: 960.0")
    else:
        print(f"❌ Pontos de retenção calculados incorretamente: {pontos_retencao.get('total')}")
        return False
    
    test_delete_campeonato(campeonato_id)

    print("✅  Teste de retenção concluído.")


### TEST ALL PONTOS FUNCTION ###

def teste_all_pontos():
    # print("\n🚀 Iniciando testes de pontos...\n")

    # campeonato_id = test_post_campeonato()
    # if not campeonato_id:
    #     print("❌ Não foi possível criar campeonato para testar.")
    #     return False
    # print(f"🔹 Campeonato criado com ID: {campeonato_id}\n")

    # cla_id = test_post_cla(campeonato_id)
    # if not cla_id:
    #     print("❌ Não foi possível criar CLA para testar.")
    #     return False
    # print(f"🔹 CLA criado com ID: {cla_id}\n")

    # aluno_id = test_post_aluno(campeonato_id, cla_id)
    # if not aluno_id:
    #     print("❌ Não foi possível criar aluno para testar.")
    #     return False
    # print(f"🔹 Aluno criado com ID: {aluno_id}\n")

    # cliente_id = test_post_cliente(campeonato_id, aluno_id)
    # if not cliente_id:
    #     print("❌ Não foi possível criar cliente para testar.")
    #     return False
    # print(f"🔹 Cliente criado com ID: {cliente_id}\n")

    # contrato_id = test_post_contrato(cliente_id, 1)
    # if not contrato_id:
    #     print("❌ Não foi possível criar contrato para testar.")
    #     return False
    # print(f"🔹 Contrato criado com ID: {contrato_id}\n")
    

    # print("Todos Ids:")
    # print(f"campeonato_id={campeonato_id}")
    # print(f"cla_id={cla_id}")
    # print(f"aluno_id={aluno_id}")
    # print(f"cliente_id={cliente_id}")
    # print(f"contrato_id={contrato_id}")

    print("🔥🔥 Criando envio para testar todas possibilidades...🔥🔥")

    # time.sleep(1)
    # test_reprove_data_envio(campeonato_id, aluno_id, cliente_id, contrato_id)
    # time.sleep(1)
    # test_aprove_envio(campeonato_id, aluno_id, cliente_id, contrato_id)
    # time.sleep(1)
    # test_reprove_envio(campeonato_id, aluno_id, cliente_id, contrato_id)
    # time.sleep(1)
    # test_reprove_data_contrato(campeonato_id, aluno_id, cliente_id)
    # time.sleep(1)
    # test_update_contrato(campeonato_id, aluno_id, cliente_id)
    # time.sleep(1)
    # test_aprove_contrato_coproducao_envio(campeonato_id, aluno_id, cliente_id)
    # time.sleep(1)
    # test_invalid_cliente(campeonato_id, aluno_id)
    # time.sleep(1)
    # test_invalid_contrato(campeonato_id, aluno_id)
    # time.sleep(1)
    # test_balancemanto(campeonato_id, aluno_id)
    # time.sleep(1)
    # test_retencao()
    # time.sleep(1)

    # test_delete_contrato(contrato_id)
    # test_delete_cliente(cliente_id)
    # test_delete_aluno(aluno_id)
    # test_delete_cla(cla_id)
    # test_delete_campeonato(campeonato_id)

    print("\n✅ Testes de pontos concluídos.\n")
    return True