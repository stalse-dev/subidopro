from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from subidometro.models import *
from .test.payload_test import *

class ReceberDadosTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("receber_dados")

    def test_receber_dados_add_alt_del_alterar_cliente(self):
        """Testa se o cliente é adicionado e alterado corretamente usando o ID."""

        payload = payload_cliente_padrao

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
        payload = payload_contrato_padrao

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
        payload = payload_recebimento_padrao

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
            
    def test_receber_dados_pontos_recebimento_sucesso(self):
        """ O intuito deste teste é verificar se o endpoint de receber_dados
            está recebendo Pontos e Recebimento de forma padronizada corretamente. """
        
        client = self.client
        payload = payload_recebimento_padrao

        payload["acao"] = "add"
        payload["registroAtual"]["alunosEnvios"]["valor"] = "1000"
        payload["registroAtual"]["alunosEnvios"]["data"] = "2025-04-08"
        payload["registroAtual"]["alunosClientesContratos"]["tipoContrato"] = "1"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Operação concluída!")

        envio_id = payload["registroAtual"]["alunosEnvios"]["id"]
        envio = Aluno_envios.objects.get(id=envio_id)
        self.assertEqual(envio.id, int(envio_id))
        self.assertEqual(envio.pontos, 100)










    
    
    
   