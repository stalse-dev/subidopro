import requests
from datetime import date, timedelta
import time
from calculadora_pontos.utils import *
from dateutil.relativedelta import relativedelta

BASE_URL = "http://127.0.0.1:8000/pontos/"
AUTH_TOKEN = "Token fdf2b70fc9e5c203f3259586b943686d937c0fba"

HEADERS = {
    "Authorization": AUTH_TOKEN,
    "Content-Type": "application/json"
}

### POST TEST FUNCTIONS ###

def test_post_campeonato():
    url = f"{BASE_URL}campeonato_criar/"
    data_inicio = (date.today() - timedelta(days=14)).strftime("%Y-%m-%d")
    data_fim = (date.today() + timedelta(days=180)).strftime("%Y-%m-%d")
    payload = {
        "identificacao": "Campeonato Teste",
        "descricao": "Descrição de teste",
        "data_inicio": data_inicio,
        "data_fim": data_fim,
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

def test_post_contrato(cliente_id):
    url = f"{BASE_URL}contrato_criar/"
    payload = {
        "cliente": cliente_id,
        "tipo_contrato": 1,
        "valor_contrato": "1000.00",
        "porcentagem_contrato": 10,
        "data_contrato": str(date.today()),
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

def test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, data_recebimento):
    url = f"{BASE_URL}envio_criar/"
    semana = calcular_semana_vigente(campeonato_id)
    payload = {
        "aluno": aluno_id,
        "cliente": cliente_id,
        "contrato": contrato_id,
        "campeonato": campeonato_id,
        "data": data_recebimento,
        "descricao": "Envio de documento XPTO",
        "valor": "1000.00",
        "arquivo1": 'http://example.com/arquivo1.pdf',
        "data_cadastro": data_recebimento,
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

### GET, PUT, PATCH TEST FUNCTIONS ###

def test_get_cliente(cliente_id):
    url = f"{BASE_URL}cliente_detalhes/{cliente_id}/"
    response = requests.get(url, headers=HEADERS)

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = response.text

    print(response.status_code, data)

def test_put_cliente(cliente_id):
    url = f"{BASE_URL}cliente_detalhes/{cliente_id}/"
    payload = {
        "titulo": "Cliente Teste Atualizado",
        "tipo_cliente": 2,
        "tipo_contrato": 1,
        "documento": "99988877766",
        "telefone": "11988887777",
        "email": "clienteatualizado@teste.com",
        "data_criacao": str(date.today()),
        "status": 0,
        "campeonato": 1,
        "aluno": 1
    }

    response = requests.put(url, json=payload, headers=HEADERS)
    print("🔹 PUT - Atualizar Cliente")
    print(response.status_code, response.json())

def test_patch_cliente(cliente_id):
    url = f"{BASE_URL}cliente_detalhes/{cliente_id}/"
    payload = {
        "status": 1
    }

    response = requests.patch(url, json=payload, headers=HEADERS)
    print("🔹 PATCH - Atualizar Cliente")
    print(response.status_code, response.json())

    
def teste_all_pontos():
    print("\n🚀 Iniciando testes de pontos...\n")

    campeonato_id = test_post_campeonato()
    if not campeonato_id:
        print("❌ Não foi possível criar campeonato para testar.")
        return False
    print(f"🔹 Campeonato criado com ID: {campeonato_id}\n")
    time.sleep(1)

    cla_id = test_post_cla(campeonato_id)
    if not cla_id:
        print("❌ Não foi possível criar CLA para testar.")
        return False
    print(f"🔹 CLA criado com ID: {cla_id}\n")
    time.sleep(1)

    aluno_id = test_post_aluno(campeonato_id, cla_id)
    if not aluno_id:
        print("❌ Não foi possível criar aluno para testar.")
        return False
    print(f"🔹 Aluno criado com ID: {aluno_id}\n")
    time.sleep(1)

    cliente_id = test_post_cliente(campeonato_id, aluno_id)
    if not cliente_id:
        print("❌ Não foi possível criar cliente para testar.")
        return False
    print(f"🔹 Cliente criado com ID: {cliente_id}\n")
    time.sleep(1) 

    contrato_id = test_post_contrato(cliente_id)
    if not contrato_id:
        print("❌ Não foi possível criar contrato para testar.")
        return False
    print(f"🔹 Contrato criado com ID: {contrato_id}\n")
    time.sleep(1)

    envio_id = test_post_envio(campeonato_id, aluno_id, cliente_id, contrato_id, str(date.today()))
    if not envio_id:
        print("❌ Não foi possível criar envio para testar.")
        return False
    print(f"🔹 Envio criado com ID: {envio_id}\n")
    time.sleep(1)

    # data_recebimento = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    # for i in range(1, 5):
    #     data_recebimento = (date.today() + timedelta(mon)).strftime("%Y-%m-%d")


    test_delete_contrato(contrato_id)
    test_delete_cliente(cliente_id)
    test_delete_aluno(aluno_id)
    test_delete_cla(cla_id)
    test_delete_campeonato(campeonato_id)

    print("\n✅ Testes de pontos concluídos.\n")
    return True