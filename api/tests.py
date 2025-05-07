from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from subidometro.models import *
from .test.payload_test import *
import copy

class ReceberDadosTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("receber_dados")


    ### RECEBIMENTO ###

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

    ### cliente ###

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





        

        


















    
    
    
   