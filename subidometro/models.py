from django.db import models

class Campeonato(models.Model):
    identificacao = models.CharField(max_length=255)
    descricao = models.TextField(null=True, blank=True)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    imagem = models.CharField(max_length=255)
    regra_pdf = models.CharField(max_length=255)
    turma = models.IntegerField(null=True, blank=True)
    ativo = models.BooleanField(default=False)


    def __str__(self):
        return self.identificacao

class Desafios(models.Model):
    titulo = models.CharField(max_length=500, unique=True)
    descricao = models.TextField(null=True, blank=True)
    regras = models.TextField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_fim = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.titulo

class Mentoria_cla(models.Model):
    campeonato = models.ForeignKey("Campeonato", on_delete=models.CASCADE, null=True, blank=True, related_name="campeonato_cla")
    nome = models.CharField(max_length=255)
    descricao = models.TextField(null=True, blank=True)
    sigla = models.CharField(max_length=255, null=True, blank=True)
    rastreador = models.IntegerField(null=True, blank=True)
    rastreador_substituto = models.IntegerField(null=True, blank=True)
    definido = models.IntegerField(null=True, blank=True)
    brasao = models.TextField(null= True, blank=True)

    def __str__(self):
        return self.nome

class Mentoria_cla_pontos(models.Model):
    cla = models.ForeignKey("Mentoria_cla", on_delete=models.CASCADE, null=True, blank=True, related_name='mentoria_cla_pontos_cla')
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, null=True, blank=True, related_name="mentoria_cla_pontos_campeonato")
    pontos = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=255, null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    

class Mentoria_cla_posicao_semana(models.Model):
    cla = models.ForeignKey("Mentoria_cla", on_delete=models.CASCADE, null=True, blank=True, related_name='mentoria_cla_posicoes_semana_cla')
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, null=True, blank=True, related_name="mentoria_cla_posicoes_semana_campeonato")
    semana = models.IntegerField(null=True, blank=True)
    posicao = models.IntegerField(null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    pontos_recebimento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_desafio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_certificacao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_manual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_contrato = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_retencao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_totais = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rastreador = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.cla} - {self.semana} - {self.posicao}"

class Alunos(models.Model):
    nome_completo = models.CharField(max_length=255, null=True, blank=True, db_column="nome_completo")
    nome_social = models.CharField(max_length=255, null=True, blank=True, db_column="nome_social")
    apelido = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    data_criacao = models.DateTimeField(null=True, blank=True, db_column="data_criacao")
    status = models.CharField(max_length=255, null=True, blank=True, default='1')
    hotmart = models.IntegerField(null=True, blank=True)
    termo_aceito = models.IntegerField(null=True, blank=True, db_column="termo_aceito")
    cla = models.ForeignKey("Mentoria_cla", on_delete=models.CASCADE, null=True, blank=True, related_name="aluno_cla")
    nivel = models.IntegerField(null=True, blank=True, default=0)
    aluno_consultor = models.IntegerField(null=True, blank=True, default=0, db_column="aluno_consultor")
    tags_interna = models.CharField(max_length=255, null=True, blank=True, db_column="tags_interna")

    def __str__(self):
        return self.nome_completo

class Alunos_posicoes_semana(models.Model):
    aluno = models.ForeignKey(Alunos, on_delete=models.CASCADE, related_name="alunos_posicoes_semana")
    cla = models.ForeignKey("Mentoria_cla", on_delete=models.CASCADE, null=True, blank=True, related_name="alunos_posicoes_semana_cla")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, null=True, blank=True, related_name="alunos_posicoes_semana_campeonato")
    semana = models.IntegerField(null=True, blank=True)
    posicao = models.IntegerField(null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    pontos_recebimento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_desafio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_certificacao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_manual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_contrato = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_retencao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos_totais = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Aluno {self.aluno.id} - {self.aluno.nome_completo} - {self.posicao} - {self.tipo}"

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
    id = models.BigAutoField(primary_key=True)
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="alunosclientespontosestemesretencao_set")
    cliente = models.ForeignKey(Aluno_clientes, on_delete=models.CASCADE, related_name="alunosclientespontosestemesretencao_set")
    envio = models.ForeignKey("Aluno_envios", on_delete=models.CASCADE, null=True, blank=True, related_name="alunosclientespontosestemesretencao_set") #Novo Campo
    contrato = models.ForeignKey(Aluno_clientes_contratos, on_delete=models.CASCADE, null=True, blank=True, related_name="alunosclientespontosestemesretencao_set") #Novo Campo
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, null=True, blank=True, related_name="campeonatos_clientes")
    data = models.DateField(null=True, blank=True)
    pontos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    qtd_envios = models.IntegerField(null=True, blank=True)
    ids_envios = models.CharField(max_length=5000, null=True, blank=True)
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
    valor_calculado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
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

    pontos = models.DecimalField(max_digits=10, decimal_places=2)
    pontos_previsto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    def __str__(self):
        return f"Envio {self.id} - {self.cliente} - {self.aluno}"

class Aluno_desafio(models.Model):
    campeonato = models.ForeignKey("Campeonato", on_delete=models.CASCADE, null=True, blank=True, related_name="campeonato_desafio")
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="aluno_desafios")
    desafio = models.ForeignKey("Desafios", on_delete=models.CASCADE, related_name="aluno_desafio")
    
    descricao = models.CharField(max_length=255, null=True, blank=True)
    texto = models.TextField(null=True, blank=True)
    data = models.DateField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    rastreador_analise = models.IntegerField(null=True, blank=True)
    data_analise = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    status_motivo = models.IntegerField(null=True, blank=True)
    status_comentario = models.TextField(null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)

    
    pontos = models.DecimalField(max_digits=10, decimal_places=2)
    pontos_previsto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Desafio {self.id} - {self.desafio} - {self.aluno}"

class Aluno_certificacao(models.Model):
    campeonato = models.ForeignKey("Campeonato", on_delete=models.CASCADE, null=True, blank=True, related_name="campeonato_certificacoes")
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="aluno_certificacoes")
    descricao = models.TextField(null=True, blank=True)
    data = models.DateField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    rastreador_analise = models.IntegerField(null=True, blank=True)
    data_analise = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    status_motivo = models.IntegerField(null=True, blank=True)
    status_comentario = models.TextField(null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)


    pontos = models.DecimalField(max_digits=10, decimal_places=2)
    pontos_previsto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Certificação {self.id} - {self.aluno} - {self.descricao}"
    
class Alunos_Subidometro(models.Model):
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="alunos_subidometro")
    campeonato = models.ForeignKey("Campeonato", on_delete=models.CASCADE, null=True, blank=True, related_name="alunos_subidometro_campeonato")
    cla = models.ForeignKey("Mentoria_cla", on_delete=models.CASCADE, null=True, blank=True, related_name="alunos_subidometro_cla")
    semana = models.IntegerField(null=True, blank=True)
    nivel = models.IntegerField(null=True, blank=True)
    nivel_motivo = models.IntegerField(null=True, blank=True)
    nivel_comentario = models.TextField(null=True, blank=True)
    envios = models.IntegerField(null=True, blank=True)
    cliente = models.IntegerField(null=True, blank=True)
    faturamento = models.IntegerField(null=True, blank=True)
    faturamento_valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pontuacao_geral = models.IntegerField(null=True, blank=True)
    pontuacao_cla = models.IntegerField(null=True, blank=True)
    rastreador = models.IntegerField(null=True, blank=True)
    data = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    status_aluno = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"{self.aluno.nome_completo} - {self.campeonato.identificacao}"

class Aluno_contrato(models.Model):
    campeonato = models.ForeignKey("Campeonato", on_delete=models.CASCADE, null=True, blank=True, related_name="campeonato_aluno_contrato")
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="aluno_aluno_contrato")
    cliente = models.ForeignKey(Aluno_clientes, on_delete=models.CASCADE, related_name="cliente_aluno_contrato")
    contrato = models.ForeignKey(Aluno_clientes_contratos, on_delete=models.CASCADE, related_name="contrato_aluno_contrato", null=True, blank=True)
    envio = models.ForeignKey(Aluno_envios, on_delete=models.CASCADE, related_name="envio_aluno_contrato", null=True, blank=True)


    descricao = models.CharField(max_length=255, null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data = models.DateField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    status = models.IntegerField(null=True, blank=True, default=0)

    pontos = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.aluno.nome_completo} - {self.pontos}"
    
class Aluno_camp_faturamento_anterior(models.Model):
    aluno = models.ForeignKey("Alunos", on_delete=models.CASCADE, related_name="aluno_camp_faturamento_anterior")
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    campeonato_turma = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.aluno.nome_completo} - {self.valor} - {self.campeonato_turma}"
    
class Mentoria_lista_niveis(models.Model):
    titulo = models.CharField(max_length=255, null=True, blank=True)
    estrela = models.IntegerField(default=1, null=True, blank=True)
    cor = models.CharField(max_length=255, null=True, blank=True)
    ordem = models.IntegerField(null=True, blank=True)
    checklist = models.TextField(null=True, blank=True)
    ultimo_nivel = models.IntegerField(default=0, null=True, blank=True)
    nivel_grupo = models.IntegerField(null=True, blank=True)
    id_circle = models.CharField(max_length=255, null=True, blank=True)
    id_intercom = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.titulo or f"Nível {self.id}"
    