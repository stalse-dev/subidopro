from django.db import models

class Campeonato(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(null=True, blank=True)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.nome

class Desafios(models.Model):
    titulo = models.CharField(max_length=500, unique=True)
    descricao = models.TextField(null=True, blank=True)
    regras = models.TextField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_fim = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.titulo

class Alunos(models.Model):
    nome_completo = models.CharField(max_length=255, null=True, blank=True, db_column="nome_completo")
    nome_social = models.CharField(max_length=255, null=True, blank=True, db_column="nome_social")
    apelido = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    data_criacao = models.DateTimeField(null=True, blank=True, db_column="data_criacao")
    status = models.CharField(max_length=255, null=True, blank=True, default='1')
    hotmart = models.IntegerField(null=True, blank=True)
    termo_aceito = models.IntegerField(null=True, blank=True, db_column="termo_aceito")
    cla = models.IntegerField(null=True, blank=True, default=0)
    nivel = models.IntegerField(null=True, blank=True, default=0)
    aluno_consultor = models.IntegerField(null=True, blank=True, default=0, db_column="aluno_consultor")
    tags_interna = models.CharField(max_length=255, null=True, blank=True, db_column="tags_interna")

    def __str__(self):
        return self.nome_completo

class Mentoria_cla(models.Model):
    campeonato = models.ForeignKey("Campeonato", on_delete=models.CASCADE, null=True, blank=True, related_name="campeonato_cla")
    nome = models.CharField(max_length=255, unique=True)
    descricao = models.TextField(null=True, blank=True)
    sigla = models.CharField(max_length=255, null=True, blank=True)
    rastreador = models.IntegerField(null=True, blank=True)
    rastreador_substituto = models.IntegerField(null=True, blank=True)
    definido = models.IntegerField(null=True, blank=True)
    brasao = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nome
    
class Aluno_clientes(models.Model):
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, null=True, blank=True, related_name="campeonato_clientes")
    aluno = models.ForeignKey(Alunos, on_delete=models.CASCADE, related_name="envios_aluno")
    titulo = models.CharField(max_length=255, null=True, blank=True)
    estrangeiro = models.IntegerField(null=True, blank=True, default=0)
    tipo_cliente = models.IntegerField(null=True, blank=True) # Valdiar com Inventandus
    tipo_contrato = models.IntegerField(null=True, blank=True) # Valdiar com Inventandus
    sociedade = models.IntegerField(null=True, blank=True, default=0)
    cliente_antes_subidopro = models.IntegerField(null=True, blank=True, default=0)
    documento_antigo = models.CharField(max_length=255, null=True, blank=True)
    documento = models.CharField(max_length=255, null=True, blank=True)
    telefone = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    data_criacao = models.DateTimeField(null=True, blank=True)
    rastreador = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    motivo_invalido = models.IntegerField(null=True, blank=True)
    descricao_invalido = models.TextField(null=True, blank=True)
    pontos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sem_pontuacao = models.IntegerField(null=True, blank=True, default=0)
    rastreador_analise = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.titulo

class Aluno_clientes_contratos(models.Model):
    cliente = models.ForeignKey(Aluno_clientes, on_delete=models.CASCADE, related_name="contratos")
    tipo_contrato = models.IntegerField(null=True, blank=True)
    valor_contrato = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    porcentagem_contrato = models.CharField(max_length=255, null=True, blank=True)
    arquivo1 = models.CharField(max_length=255, null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(default=0)
    data_contrato = models.DateField(null=True, blank=True)
    data_vencimento = models.DateField(null=True, blank=True)
    data_criacao = models.DateTimeField(null=True, blank=True)
    motivo_invalido = models.IntegerField(null=True, blank=True)
    descricao_invalido = models.TextField(null=True, blank=True)
    rastreador_analise = models.IntegerField(null=True, blank=True)
    analise_data = models.DateTimeField(null=True, blank=True)
    camp_anterior = models.IntegerField(default=0)
    id_camp_anterior = models.IntegerField(null=True, blank=True) # Valdiar com Inventandus

class Alunos_clientes_pontos_meses_retencao(models.Model):
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="alunosclientespontosestemesretencao_set")
    cliente = models.ForeignKey(Aluno_clientes, on_delete=models.CASCADE, related_name="alunosclientespontosestemesretencao_set")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, null=True, blank=True, related_name="campeonatos_clientes")
    data = models.DateField(null=True, blank=True)
    pontos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    qtd_envios = models.IntegerField(null=True, blank=True)
    ids_envios = models.CharField(max_length=2000, null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Pontuação {self.id} - {self.cliente} - {self.aluno}"

class Aluno_envios(models.Model):
    campeonato = models.ForeignKey("Campeonato", on_delete=models.CASCADE, null=True, blank=True, related_name="campeonato_envios")
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="envios_aluno_cl")
    cliente = models.ForeignKey(Aluno_clientes, on_delete=models.CASCADE, related_name="envios_cliente_cl")
    contrato = models.ForeignKey(Aluno_clientes_contratos, on_delete=models.CASCADE, related_name="envios_contrato_cl", null=True, blank=True)
    data = models.DateField(null=True, blank=True)
    descricao = models.CharField(max_length=255, null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    arquivo1 = models.CharField(max_length=255, null=True, blank=True)
    arquivo1_motivo = models.IntegerField(null=True, blank=True)
    arquivo1_status = models.IntegerField(null=True, blank=True, default=0)

    data_cadastro = models.DateTimeField(auto_now_add=True)
    rastreador_analise = models.IntegerField(null=True, blank=True)
    data_analise = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    status_motivo = models.IntegerField(null=True, blank=True)
    status_comentario = models.TextField(null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Envio {self.id} - {self.cliente} - {self.aluno}"

class Aluno_desafio(models.Model):
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="aluno_desafios")
    desafio = models.ForeignKey("Desafios", on_delete=models.CASCADE, related_name="aluno_desafio")
    campeonato = models.ForeignKey("Campeonato", on_delete=models.CASCADE, null=True, blank=True, related_name="campeonato_desafio")
    status = models.IntegerField(null=True, blank=True)
    texto = models.TextField(null=True, blank=True)
    data = models.DateField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    rastreador_analise = models.IntegerField(null=True, blank=True)
    data_analise = models.DateTimeField(null=True, blank=True)
    status_motivo = models.IntegerField(null=True, blank=True)
    status_comentario = models.TextField(null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Desafio {self.id} - {self.desafio} - {self.aluno}"

class Aluno_certificacao(models.Model):
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="aluno_certificacoes")
    campeonato = models.ForeignKey("Campeonato", on_delete=models.CASCADE, null=True, blank=True, related_name="campeonato_certificacoes")
    descricao = models.TextField(null=True, blank=True)
    data = models.DateField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    rastreador_analise = models.IntegerField(null=True, blank=True)
    data_analise = models.DateTimeField(null=True, blank=True)
    status_motivo = models.IntegerField(null=True, blank=True)
    status_comentario = models.TextField(null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Certificação {self.id} - {self.aluno} - {self.descricao}"
    
class TipoPontuacao(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(null=True, blank=True)
    nome_tabela = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

class Aluno_pontuacao(models.Model):
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="aluno_pontuacoes")
    tipo_pontuacao = models.ForeignKey("TipoPontuacao", on_delete=models.CASCADE, related_name="tipo_pontuacoes")
    
    # Vínculo opcional com Aluno_envios
    envio = models.ForeignKey("Aluno_envios", on_delete=models.SET_NULL, null=True, blank=True, related_name="pontuacoes_envios")
    
    # Vínculo opcional com Desafios
    desafio = models.ForeignKey("Aluno_desafio", on_delete=models.SET_NULL, null=True, blank=True, related_name="pontuacoes_desafios")

    # Vínculo opcional com Certificações
    certificacao = models.ForeignKey("Aluno_certificacao", on_delete=models.SET_NULL, null=True, blank=True, related_name="pontuacoes_certificacoes")

    descricao = models.CharField(max_length=255, null=True, blank=True)
    pontos = models.DecimalField(max_digits=10, decimal_places=2)
    pontos_previsto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    status_motivo = models.IntegerField(null=True, blank=True)
    status_comentario = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.aluno.nome_completo} - {self.tipo_pontuacao.nome} - {self.pontos} pts"



