from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from subidometro.models import *
from .test.payload_test import *
from django.utils import timezone
from datetime import timedelta
from dateutil import parser
import random
import copy

def criar_dados_fake():
    campeonatos = []
    for data in payload_campeonato_padrao:
        campeonato, _ = Campeonato.objects.update_or_create(
            id=int(data['id']),
            defaults={
                "identificacao": data.get('identificacao', ''),
                "descricao": data.get('descricao', ''),
                "data_inicio": parser.parse(data['data_inicio']).date(),
                "data_fim": parser.parse(data['data_fim']).date(),
                "imagem": data.get('imagem', ''),
                "regra_pdf": data.get('regra_pdf', ''),
                "turma": data.get('turma'),
                "ativo": data.get('ativo', True),
            }
        )
        campeonatos.append(campeonato)

    # Criar Desafios
    for data in payload_desafios_padrao:
        Desafios.objects.update_or_create(
            id=int(data['id']),
            defaults={
                "titulo": data.get('titulo', ''),
                "descricao": data.get('descricao', ''),
                "regras": data.get('regras', ''),
                "status": data.get('status', 0),
                "data_inicio": parser.parse(data['data_inicio']).date(),
                "data_fim": parser.parse(data['data_fim']).date(),
            }
        )

    # Criar Clã
    campeonato_padrao = campeonatos[0] if campeonatos else None
    cla, _ = Mentoria_cla.objects.update_or_create(
        id=1,
        defaults={
            "campeonato": campeonato_padrao,
            "nome": "CLA DE TESTE",
            "descricao": "Descrição do CLA DE TESTE",
            "sigla": "CLA",
            "rastreador": "222",
            "rastreador_substituto": "222",
            "definido": "1",
            "brasao": "https://example.com/brasao.png"
        }
    )

    # Criar Aluno
    Alunos.objects.update_or_create(
        id=6109,
        defaults={
            "nome_completo": "Gabriel Rodrigues",
            "nome_social": "Gabriel",
            "apelido": "Gabi",
            "email": "gabriel@example.com",
            "data_criacao": timezone.now(),
            "status": "1",
            "hotmart": 123456,
            "termo_aceito": True,
            "cla": cla,
            "nivel": 1,
            "aluno_consultor": False,
            "tags_interna": "Tag de teste"
        }
    )

    print("✅ Dados fake criados com sucesso.")

class RecebimentoTest(TransactionTestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("receber_dados")
        criar_dados_fake()

    def test_receber_dados_add_alt_del_alterar_cliente(self):
        """Testa se o cliente é adicionado e alterado corretamente usando o ID."""

        payload = copy.deepcopy(payload_cliente_padrao)

        # 1. Enviar o primeiro payload para adicionar
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        id_cliente = payload["registroAtual"]["alunosClientes"]["id"]
        
        # 2. Verificar se foi criado
        cliente = Aluno_clientes.objects.get(id=id_cliente)

        payload["acao"] = "alt"
        payload["registroAtual"]["alunosClientes"]["titulo"] = "ALTERADO - GABRIEL"
        payload["registroAtual"]["alunosClientes"]["status"] = "1"


        # 4. Enviar alteração
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # 5. Verificar se foi alterado
        cliente.refresh_from_db()

        # 6. Garantir alterações com assert
        self.assertEqual(cliente.status, 1)
        self.assertEqual(cliente.titulo, "ALTERADO - GABRIEL")

        payload["acao"] = "del"

        # 7. Deletar cliente
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # 8. Verificar se foi deletado
        with self.assertRaises(Aluno_clientes.DoesNotExist):
            Aluno_clientes.objects.get(id=id_cliente)

    def test_receber_dados_add_alt_del_alterar_contrato(self):
        """Testa se o contrato é adicionado, alterado e deletado corretamente."""

        #Add o contrato
        payload = copy.deepcopy(payload_contrato_padrao)

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        contrato_id = payload["registroAtual"]["alunosClientesContratos"]["id"]
        
        contrato = Aluno_clientes_contratos.objects.get(id=contrato_id)

        payload["acao"] = "alt"
        payload["registroAtual"]["alunosClientesContratos"]["status"] = "1"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # 5. Verificar se foi alterado
        contrato.refresh_from_db()

        self.assertEqual(contrato.status, 1)

        # 7. Deletar contrato
        payload["acao"] = "del"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # 8. Verificar se foi deletado
        with self.assertRaises(Aluno_clientes_contratos.DoesNotExist):
            Aluno_clientes_contratos.objects.get(id=contrato_id)

    def test_receber_dados_add_alt_del_cliente_contrato_recebimento_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Clientes, Contratos e Recebimento de forma padronizada corretamente. """
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)

        url = reverse("receber_dados")
        response = client.post(url, payload, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # Verifica se o cliente foi criado
        cliente_id = payload["registroAtual"]["alunosClientes"]["id"]
        cliente = Aluno_clientes.objects.get(id=cliente_id)
        self.assertEqual(cliente.id, int(cliente_id))

        # Verifica se o contrato foi criado
        contrato_id = payload["registroAtual"]["alunosClientesContratos"]["id"]
        contrato = Aluno_clientes_contratos.objects.get(id=contrato_id)
        self.assertEqual(contrato.id, int(contrato_id))

        # Verifica se o envio foi criado
        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)
        self.assertEqual(envio.id, int(envio_id))


        #Alterar o Receberimento
        payload["acao"] = "alt"
        payload["registroAtual"]["alunosEnvios"]["status"] = "3"
        payload["registroAtual"]["alunosEnvios"]["descricao"] = "ALTERADO - RECEBIMENTO"

        # 4. Enviar alteração
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # 5. Verificar se foi alterado
        envio.refresh_from_db()
        self.assertEqual(envio.status, 3)
        self.assertEqual(envio.descricao, "ALTERADO - RECEBIMENTO")

        # 7. Deletar cliente
        payload["acao"] = "del"
        payload["tabela"] = "alunosEnvios"


        self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # 8. Verificar se foi deletado
        with self.assertRaises(Aluno_envios.DoesNotExist):
            Aluno_envios.objects.get(id=envio_id)
            
    def test_receber_dados_pontos_FIXO_recebimento_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos e Recebimento de forma padronizada corretamente. """
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "1000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 1000)
        self.assertEqual(envio.pontos, 100)


        # Deletar o recebimento
        payload_del = payload
        payload_del["acao"] = "del"
        payload_del["tabela"] = "alunosEnvios"


        self.client.post(self.url, payload_del, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # 8. Verificar se foi deletado
        with self.assertRaises(Aluno_envios.DoesNotExist):
            Aluno_envios.objects.get(id=envio_id)

    def test_receber_dados_pontos_COPRODUCAO_recebimento_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos e Recebimento de forma padronizada corretamente. """
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "1000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "2"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 100)
        self.assertEqual(envio.pontos, 10)

        # Deletar o recebimento
        payload_del = payload
        payload_del["acao"] = "del"
        payload_del["tabela"] = "alunosEnvios"


        self.client.post(self.url, payload_del, format="json")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["message"], "Operação concluída!")

        # 8. Verificar se foi deletado
        with self.assertRaises(Aluno_envios.DoesNotExist):
            Aluno_envios.objects.get(id=envio_id)

    def test_receber_dados_pontos_VARIAVEL_recebimento_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos e Recebimento de forma padronizada corretamente. """
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)

        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "1500"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-05-10"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "3"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 1500)
        self.assertEqual(envio.pontos, 150)

        # Deletar o recebimento
        payload_del = payload
        payload_del["acao"] = "del"
        payload_del["tabela"] = "alunosEnvios"


        self.client.post(self.url, payload_del, format="json")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["message"], "Operação concluída!")

        # 8. Verificar se foi deletado
        with self.assertRaises(Aluno_envios.DoesNotExist):
            Aluno_envios.objects.get(id=envio_id)

    def test_receber_dados_pontos_DATA_RECEBIMENTO_recebimento_zerar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está zerando os pontos de recebimentos com data menor que inicio
            do campeonato 01/03/2025."""
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "2000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-02-28"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 2000)
        self.assertEqual(envio.pontos, 0)

    def test_receber_dados_pontos_TIPO_CONTRATO_recebimento_aleterar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está alterando os pontos de recebimentos com tipo de contrato 2."""
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "2000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 2000)
        self.assertEqual(envio.pontos, 200)

        # Aleterar o recebimento
        payload["acao"] = "alt"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "2"
        payload["registroAtual"]["alunosEnvios"]["valor"] = "2000"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")
        

        envio.refresh_from_db()

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 200)
        self.assertEqual(envio.pontos, 20)

        # Aleterar o recebimento
        payload["acao"] = "alt"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"
        payload["registroAtual"]["alunosEnvios"]["valor"] = "2000"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")
        

        envio.refresh_from_db()

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 2000)
        self.assertEqual(envio.pontos, 200)

    def test_receber_dados_pontos_INVALIDAR_ENVIO_recebimento_zerar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está zerando os pontos ao alterar o status do recebimento para 2."""
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "2000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 2000)
        self.assertEqual(envio.pontos, 200)

        # Alterar o recebimento
        payload["acao"] = "alt"
        payload["registroAtual"]["alunosEnvios"]["status"] = "2"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")
        

        envio.refresh_from_db()

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.pontos, 0)

    def test_receber_dados_pontos_INVALIDAR_CONTRATO_recebimento_zerar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está zerando os pontos ao alterar o status do contrato para 2."""
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "2000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        contrato_id = payload["registroAtual"]["alunosClientesContratos"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 2000)
        self.assertEqual(envio.pontos, 200)

        # Alterar o recebimento
        payload["acao"] = "alt"
        payload["tabela"] = "alunosClientesContratos"
        payload["registroAtual"]["alunosClientesContratos"]["status"] = "2"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")
        

        contrato = Aluno_clientes_contratos.objects.get(id=contrato_id)


        envio.refresh_from_db()

        self.assertEqual(contrato.id, int(contrato_id))
        self.assertEqual(contrato.status, 2)
        self.assertEqual(envio.id, int(envio_id))

        self.assertEqual(envio.status, 2)

    def test_receber_dados_pontos_INVALIDAR_CLIENTE_recebimento_zerar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está zerando os pontos ao alterar o status do cliente para 2."""
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "2000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        contrato_id = payload["registroAtual"]["alunosClientesContratos"]["id"]
        cliente_id = payload["registroAtual"]["alunosClientes"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 2000)
        self.assertEqual(envio.pontos, 200)

        # Alterar o recebimento
        payload["acao"] = "alt"
        payload["tabela"] = "alunosClientes"
        payload["registroAtual"]["alunosClientes"]["status"] = "2"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")
        

        cliente = Aluno_clientes.objects.get(id=cliente_id)
        contrato = Aluno_clientes_contratos.objects.get(id=contrato_id)


        envio.refresh_from_db()

        self.assertEqual(cliente.id, int(cliente_id))
        self.assertEqual(cliente.status, 2)
        self.assertEqual(contrato.id, int(contrato_id))
        self.assertEqual(contrato.status, 2)
        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.status, 2)

    def test_receber_dados_pontos_ALTERAR_PONTOS_MANUAL_contrato_aleterar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está alterando os pontos de recebimentos com tipo de contrato 2."""
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "15000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "2"
        


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 1500)
        self.assertEqual(envio.pontos, 150)

        # Alterar o recebimento
        payload["acao"] = "alt"
        payload["tabela"] = "alunosEnvios"
        payload["registroAtual"]["alunosEnvios"]["acaoRastreador"] = True
        payload["registroAtual"]["alunosEnvios"]["pontos"] = "888"
        payload["registroAtual"]["alunosEnvios"]["valor"] = "15000"
        payload["registroAtual"]["alunosEnvios"]["pontosPreenchidos"] = "888"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")
        

        envio.refresh_from_db()

        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.valor_calculado, 1500)
        self.assertEqual(envio.pontos, 888)
    
class ClienteTest(TransactionTestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("receber_dados")
        criar_dados_fake()

    def test_receber_dados_pontos_FIXO_contrato_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos e Contrato de forma padronizada corretamente. """
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "1000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # Busca o contrato
        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        contrato_aluno = Aluno_contrato.objects.get(envio_id=envio_id)

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 0)


        payload["acao"] = "alt"
        payload["tabela"] = "alunosEnvios"
        payload["registroAtual"]["alunosEnvios"]["status"] = "3"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        contrato_aluno.refresh_from_db()

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 3)
        self.assertEqual(contrato_aluno.pontos, 480)

    def test_receber_dados_pontos_COPRODUCAO_contrato_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos e Contrato de forma padronizada corretamente. """
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "3000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "2"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # Busca o contrato
        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        contrato_aluno = Aluno_contrato.objects.get(envio_id=envio_id)

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 0)


        payload["acao"] = "alt"
        payload["tabela"] = "alunosEnvios"
        payload["registroAtual"]["alunosEnvios"]["status"] = "3"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        contrato_aluno.refresh_from_db()

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 3)
        self.assertEqual(contrato_aluno.pontos, 60)

    def test_receber_dados_pontos_DATA_CLIENTE_contrato_zerar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
        está zerando Pontos e Contrato de a cordo a data do cliente for menor que 01/03/2025."""
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "1000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientes"]["dataCriacao"] = "2025-02-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # Busca o contrato

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        
        with self.assertRaises(Aluno_contrato.DoesNotExist):
            Aluno_contrato.objects.get(envio_id=envio_id)

    def test_receber_dados_pontos_INVALIDAR_CONTRATO_contrato_alterar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está alterando os pontos de recebimentos com tipo de contrato 2."""
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "5000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "2"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        # Busca o contrato
        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        contrato_aluno = Aluno_contrato.objects.get(envio_id=envio_id)

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 0)



        payload_alt_envio = payload

        payload_alt_envio["acao"] = "alt"
        payload_alt_envio["tabela"] = "alunosEnvios"
        payload_alt_envio["registroAtual"]["alunosEnvios"]["valor"] = "5000"
        payload_alt_envio["registroAtual"]["alunosEnvios"]["status"] = "3"


        response = self.client.post(self.url, payload_alt_envio, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        contrato_aluno.refresh_from_db()
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 3)
        self.assertEqual(contrato_aluno.pontos, 60)
        self.assertEqual(envio.pontos, 50)

        payload_alt_contrato = payload
        
        payload_alt_contrato["acao"] = "alt"
        payload_alt_contrato["tabela"] = "alunosClientesContratos"
        payload_alt_contrato["registroAtual"]["alunosClientesContratos"]["status"] = "2"


        response = self.client.post(self.url, payload_alt_contrato, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        contrato_aluno.refresh_from_db()
        envio.refresh_from_db()

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 2)
        self.assertEqual(envio.pontos, 0)
        self.assertEqual(envio.status, 2)

    def test_receber_dados_pontos_INVALIDAR_CLIENTE_contrato_alterar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
        está alterando os pontos de recebimentos com tipo de contrato 2."""
        
        client = self.client
        payload = copy.deepcopy(payload_recebimento_padrao)


        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "10000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"


        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        contrato_aluno = Aluno_contrato.objects.get(envio_id=envio_id)

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 0)



        payload_alt_envio = payload

        payload_alt_envio["acao"] = "alt"
        payload_alt_envio["tabela"] = "alunosEnvios"
        payload_alt_envio["registroAtual"]["alunosEnvios"]["valor"] = "10000"
        payload_alt_envio["registroAtual"]["alunosEnvios"]["status"] = "3" 

        response = self.client.post(self.url, payload_alt_envio, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        contrato_aluno.refresh_from_db()
        envio = Aluno_envios.objects.get(id=envio_id)

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 3)
        self.assertEqual(contrato_aluno.pontos, 2460)
        self.assertEqual(envio.pontos, 1000)

        payload_alt_cliente = payload


        payload_alt_cliente["acao"] = "alt"
        payload_alt_cliente["tabela"] = "alunosClientes"
        payload_alt_cliente["registroAtual"]["alunosClientes"]["status"] = "2"

        response = self.client.post(self.url, payload_alt_cliente, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        contrato_aluno.refresh_from_db()
        envio.refresh_from_db()

        self.assertEqual(contrato_aluno.envio_id, int(envio_id))
        self.assertEqual(contrato_aluno.status, 2)
        self.assertEqual(envio.pontos, 0)
        self.assertEqual(envio.status, 2)

class DesafioTest(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("receber_dados")
        criar_dados_fake()

    def test_receber_dados_pontos_desafio_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos de Desafio de forma padronizada corretamente. """
        client = self.client
        payload = copy.deepcopy(payload_desafio_padrao)

        #desafrio = Desafios.objects.create(id=163, titulo="DESAFIO TESTE", descricao="DESAFIO TESTE", data_inicio="2025-03-01", data_fim="2025-04-01")
    
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        desafio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        desafio = Aluno_desafio.objects.get(id=desafio_id)

        self.assertEqual(desafio.id, int(desafio_id))
        self.assertEqual(desafio.desafio.titulo, "Teste de Desafio fake 1")
        self.assertEqual(desafio.pontos, 300)
        
    def test_receber_dados_pontos_desafio_aprovar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos de Desafio de forma padronizada corretamente. """
        client = self.client
        payload = copy.deepcopy(payload_desafio_padrao)

        #desafrio = Desafios.objects.create(id=163, titulo="DESAFIO TESTE", descricao="DESAFIO TESTE", data_inicio="2025-03-01", data_fim="2025-04-01")
    
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        desafio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        desafio = Aluno_desafio.objects.get(id=desafio_id)

        self.assertEqual(desafio.id, int(desafio_id))
        self.assertEqual(desafio.desafio.titulo, "Teste de Desafio fake 1")
        self.assertEqual(desafio.pontos, 300)
        self.assertEqual(desafio.status, 0)

        #Aprovar o desafio
        payload["acao"] = "alt"
        payload["registroAtual"]["alunosEnvios"]["status"] = "3"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        desafio.refresh_from_db()
        self.assertEqual(desafio.id, int(desafio_id))
        self.assertEqual(desafio.desafio.titulo, "Teste de Desafio fake 1")
        self.assertEqual(desafio.pontos, 300)
        self.assertEqual(desafio.status, 3)

    def test_receber_dados_pontos_desafio_reprovar(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos de Desafio de forma padronizada corretamente. """
        client = self.client
        payload = copy.deepcopy(payload_desafio_padrao)

        #desafrio = Desafios.objects.create(id=163, titulo="DESAFIO TESTE", descricao="DESAFIO TESTE", data_inicio="2025-03-01", data_fim="2025-04-01")
    
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        desafio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        desafio = Aluno_desafio.objects.get(id=desafio_id)

        self.assertEqual(desafio.id, int(desafio_id))
        self.assertEqual(desafio.desafio.titulo, "Teste de Desafio fake 1")
        self.assertEqual(desafio.pontos, 300)
        self.assertEqual(desafio.status, 0)

        #Reprovar o desafio
        payload["acao"] = "alt"
        payload["registroAtual"]["alunosEnvios"]["status"] = "2"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        desafio.refresh_from_db()
        self.assertEqual(desafio.id, int(desafio_id))
        self.assertEqual(desafio.desafio.titulo, "Teste de Desafio fake 1")
        self.assertEqual(desafio.status, 2)    

class CertificacaoTest(TransactionTestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("receber_dados")
        criar_dados_fake()

    def test_receber_dados_pontos_certificacao_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos de Certificação de forma padronizada corretamente. """
        client = self.client
        payload = copy.deepcopy(payload_certificacao_padrao)

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")


        certificacao_id = payload["registroAtual"]["alunosEnvios"]["id"]
        certificacao = Aluno_certificacao.objects.get(id=certificacao_id)
        self.assertEqual(certificacao.id, int(certificacao_id))
        self.assertEqual(certificacao.pontos, 777)
        self.assertEqual(certificacao.status, 3)

class BalanceamentoTest(TransactionTestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("receber_dados")
        self.url_balanceamento = reverse("calcula_balanceamento_func")
        criar_dados_fake()

    def test_receber_dados_pontos_balanceamento_sucesso(self):
        """ O intuito deste teste é balancear todos os pontos para 3000. """
        client = self.client
        payload_01 = copy.deepcopy(payload_recebimento_padrao)

        payload_01["acao"] = "add"
        payload_01["registroAtual"]["alunosEnvios"]["id"] = "0001"
        payload_01["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "10000"
        payload_01["registroAtual"]["alunosEnvios"]["valor"] = "10000"
        payload_01["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"

        aluno_id = payload_01["registroAtual"]["alunosEnvios"]["vinculoAluno"]
        campeonato_id = payload_01["registroAtual"]["alunosEnvios"]["campeonato"]

        response = self.client.post(self.url, payload_01, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id_01 = payload_01["registroAtual"]["alunosEnvios"]["id"]
        envio_01 = Aluno_envios.objects.get(id=envio_id_01)
        self.assertEqual(envio_01.id, int(envio_id_01))
        self.assertEqual(envio_01.valor_calculado, 10000)
        self.assertEqual(envio_01.pontos, 1000)

        payload_01["acao"] = "alt"
        payload_01["tabela"] = "alunosEnvios"
        payload_01["registroAtual"]["alunosEnvios"]["status"] = "3"

        response = self.client.post(self.url, payload_01, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_01.refresh_from_db()

        self.assertEqual(envio_01.id, int(envio_id_01))
        self.assertEqual(envio_01.valor_calculado, 10000)
        self.assertEqual(envio_01.pontos, 1000)
        self.assertEqual(envio_01.status, 3)

        payload_02 = copy.deepcopy(payload_recebimento_padrao)

        payload_02["acao"] = "add"
        payload_02["registroAtual"]["alunosEnvios"]["id"] = "0002"
        payload_02["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "15000"
        payload_02["registroAtual"]["alunosEnvios"]["valor"] = "15000"
        payload_02["registroAtual"]["alunosEnvios"]["data"] = "2025-04-15"

        response = self.client.post(self.url, payload_02, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id_02 = payload_02["registroAtual"]["alunosEnvios"]["id"]
        envio_02 = Aluno_envios.objects.get(id=envio_id_02)
        self.assertEqual(envio_02.id, int(envio_id_02))
        self.assertEqual(envio_02.valor_calculado, 15000)
        self.assertEqual(envio_02.pontos, 1500)

        payload_02["acao"] = "alt"
        payload_02["tabela"] = "alunosEnvios"
        payload_02["registroAtual"]["alunosEnvios"]["status"] = "3"

        response = self.client.post(self.url, payload_02, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_02.refresh_from_db()
        self.assertEqual(envio_02.id, int(envio_id_02))
        self.assertEqual(envio_02.valor_calculado, 15000)
        self.assertEqual(envio_02.pontos, 1500)
        self.assertEqual(envio_02.status, 3)

        payload_03 = copy.deepcopy(payload_recebimento_padrao)

        payload_03["acao"] = "add"
        payload_03["registroAtual"]["alunosEnvios"]["id"] = "0003"
        payload_03["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "20000"
        payload_03["registroAtual"]["alunosEnvios"]["valor"] = "20000"
        payload_03["registroAtual"]["alunosEnvios"]["data"] = "2025-04-20"

        response = self.client.post(self.url, payload_03, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id_03 = payload_03["registroAtual"]["alunosEnvios"]["id"]
        envio_03 = Aluno_envios.objects.get(id=envio_id_03)

        self.assertEqual(envio_03.id, int(envio_id_03))
        self.assertEqual(envio_03.valor_calculado, 20000)
        self.assertEqual(envio_03.pontos, 2000)

        payload_03["acao"] = "alt"
        payload_03["tabela"] = "alunosEnvios"
        payload_03["registroAtual"]["alunosEnvios"]["status"] = "3"

        response = self.client.post(self.url, payload_03, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_03.refresh_from_db()

        self.assertEqual(envio_03.id, int(envio_id_03))
        self.assertEqual(envio_03.valor_calculado, 20000)
        self.assertEqual(envio_03.pontos, 2000)
        self.assertEqual(envio_03.status, 3)

        total_aprovado_qs = Aluno_envios.objects.filter(
            aluno_id=aluno_id,
            status=3,
            campeonato__id=campeonato_id
        ).aggregate(
            total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )

        total_aprovado = total_aprovado_qs["total"]

        self.assertEqual(total_aprovado, 4500)

        response = self.client.get(self.url_balanceamento, format="json")
        self.assertEqual(response.status_code, 200)

        total_aprovado_qs = Aluno_envios.objects.filter(
            aluno_id=aluno_id,
            status=3,
            campeonato__id=campeonato_id
        ).aggregate(
            total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )

        total_aprovado = total_aprovado_qs["total"]

        self.assertEqual(total_aprovado, 3000)

        envio_01.refresh_from_db()
        envio_02.refresh_from_db()
        envio_03.refresh_from_db()


        self.assertEqual(envio_01.pontos, 1000)
        self.assertEqual(envio_02.pontos, 1500)
        self.assertEqual(envio_03.pontos, 500)

        payload_04 = copy.deepcopy(payload_recebimento_padrao)

        payload_04["acao"] = "add"
        payload_04["registroAtual"]["alunosEnvios"]["id"] = "0004"
        payload_04["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "5000"
        payload_04["registroAtual"]["alunosEnvios"]["valor"] = "5000"
        payload_04["registroAtual"]["alunosEnvios"]["data"] = "2025-04-25"

        response = self.client.post(self.url, payload_04, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id_04 = payload_04["registroAtual"]["alunosEnvios"]["id"]
        envio_04 = Aluno_envios.objects.get(id=envio_id_04)
        self.assertEqual(envio_04.id, int(envio_id_04))
        self.assertEqual(envio_04.valor_calculado, 5000)
        self.assertEqual(envio_04.pontos, 500)

        payload_04["acao"] = "alt"
        payload_04["tabela"] = "alunosEnvios"
        payload_04["registroAtual"]["alunosEnvios"]["status"] = "3"

        response = self.client.post(self.url, payload_04, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        total_aprovado_qs = Aluno_envios.objects.filter(
            aluno_id=aluno_id,
            status=3,
            campeonato__id=campeonato_id
        ).aggregate(
            total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )

        total_aprovado = total_aprovado_qs["total"]

        self.assertEqual(total_aprovado, 3500)

        response = self.client.get(self.url_balanceamento, format="json")
        self.assertEqual(response.status_code, 200)

        total_aprovado_qs = Aluno_envios.objects.filter(
            aluno_id=aluno_id,
            status=3,
            campeonato__id=campeonato_id
        ).aggregate(
            total=Coalesce(Sum('pontos', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )

        total_aprovado = total_aprovado_qs["total"]

        self.assertEqual(total_aprovado, 3000)

        envio_01.refresh_from_db()
        envio_02.refresh_from_db()
        envio_03.refresh_from_db()
        envio_04.refresh_from_db()

        self.assertEqual(envio_01.pontos, 1000)
        self.assertEqual(envio_02.pontos, 1500)
        self.assertEqual(envio_03.pontos, 500)
        self.assertEqual(envio_04.pontos, 0)

class RetencaoTest(TransactionTestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("receber_dados")
        self.url_retencao = reverse("calculo_retencao_func")
        criar_dados_fake()

    def test_receber_dados_pontos_retencao_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos de Retenção de forma padronizada corretamente. """
        client = self.client
        payload_01 = copy.deepcopy(payload_recebimento_padrao)

        payload_01["acao"] = "add"
        payload_01["registroAtual"]["alunosEnvios"]["id"] = "0001"
        payload_01["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "3000"
        payload_01["registroAtual"]["alunosEnvios"]["valor"] = "3000"
        payload_01["registroAtual"]["alunosEnvios"]["data"] = "2025-04-16"

        aluno_id = payload_01["registroAtual"]["alunosEnvios"]["vinculoAluno"]
        campeonato_id = payload_01["registroAtual"]["alunosEnvios"]["campeonato"]

        response = self.client.post(self.url, payload_01, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id_01 = payload_01["registroAtual"]["alunosEnvios"]["id"]
        envio_01 = Aluno_envios.objects.get(id=envio_id_01)
        self.assertEqual(envio_01.id, int(envio_id_01))
        self.assertEqual(envio_01.valor_calculado, 3000)
        self.assertEqual(envio_01.pontos, 300)

        payload_01["acao"] = "alt"
        payload_01["tabela"] = "alunosEnvios"
        payload_01["registroAtual"]["alunosEnvios"]["status"] = "3"

        response = self.client.post(self.url, payload_01, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_01.refresh_from_db()

        self.assertEqual(envio_01.id, int(envio_id_01))
        self.assertEqual(envio_01.valor_calculado, 3000)
        self.assertEqual(envio_01.pontos, 300)

        payload_02 = copy.deepcopy(payload_recebimento_padrao)
        payload_02["acao"] = "add"
        payload_02["registroAtual"]["alunosEnvios"]["id"] = "0002"
        payload_02["registroAtual"]["alunosEnvios"]["valorPreenchido"] = "3000"
        payload_02["registroAtual"]["alunosEnvios"]["valor"] = "3000"
        payload_02["registroAtual"]["alunosEnvios"]["data"] = "2025-05-10"

        response = self.client.post(self.url, payload_02, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id_02 = payload_02["registroAtual"]["alunosEnvios"]["id"]
        envio_02 = Aluno_envios.objects.get(id=envio_id_02)
        self.assertEqual(envio_02.id, int(envio_id_02))
        self.assertEqual(envio_02.valor_calculado, 3000)
        self.assertEqual(envio_02.pontos, 300)
        self.assertEqual(envio_02.status, 0)

        payload_02["acao"] = "alt"
        payload_02["tabela"] = "alunosEnvios"
        payload_02["registroAtual"]["alunosEnvios"]["status"] = "3"
        response = self.client.post(self.url, payload_02, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_02.refresh_from_db()

        self.assertEqual(envio_02.id, int(envio_id_02))
        self.assertEqual(envio_02.valor_calculado, 3000)
        self.assertEqual(envio_02.pontos, 300)
        self.assertEqual(envio_02.status, 3)


        #Vericiar se Retenção existe
        retencao = Alunos_clientes_pontos_meses_retencao.objects.filter(
            aluno_id=aluno_id,
            cliente=envio_02.cliente,
            campeonato__id=campeonato_id
        ).all()
        self.assertEqual(len(retencao), 0)

        response = self.client.get(self.url_retencao, format="json")
        self.assertEqual(response.status_code, 200)

        #Vericiar se Retenção existe
        retencao = Alunos_clientes_pontos_meses_retencao.objects.filter(
            aluno_id=aluno_id,
            cliente=envio_02.cliente,
            campeonato__id=campeonato_id
        ).all()

        self.assertEqual(len(retencao), 1)



















    
    
    
   