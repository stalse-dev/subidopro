from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import timedelta
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, name=None, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, name=name, password=password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(('email address'), unique=True)
    name = models.CharField(('full name'), max_length=150, default='default_name_here')
    is_staff = models.BooleanField(('staff status'), default=False)
    is_active = models.BooleanField(('active'), default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

class Aluno(models.Model):
    id = models.AutoField(primary_key=True)
    nomeCompleto = models.CharField(max_length=255, null=True, blank=True, db_column="nomeCompleto")
    nomeSocial = models.CharField(max_length=255, null=True, blank=True, db_column="nomeSocial")
    apelido = models.CharField(max_length=255, null=True, blank=True)
    emailCircle = models.EmailField(max_length=255, null=True, blank=True, db_column="emailCircle")
    email = models.EmailField(max_length=255, null=True, blank=True)
    csenha = models.CharField(max_length=255, null=True, blank=True)
    senha = models.CharField(max_length=255, null=True, blank=True)
    hash = models.CharField(max_length=255, null=True, blank=True)
    ucode = models.CharField(max_length=255, null=True, blank=True)
    subscriberCode = models.CharField(max_length=255, null=True, blank=True, db_column="subscriberCode")
    dataCriacao = models.DateTimeField(null=True, blank=True, db_column="dataCriacao")
    status = models.CharField(max_length=255, null=True, blank=True, default='1')
    statusWebhook = models.CharField(max_length=255, null=True, blank=True, db_column="statusWebhook")
    hotmart = models.IntegerField(null=True, blank=True)
    dataExpiracao = models.DateField(null=True, blank=True, db_column="dataExpiracao")
    dataExpiracao7Dias = models.DateField(null=True, blank=True, db_column="dataExpiracao7Dias")
    termoAceito = models.IntegerField(null=True, blank=True, db_column="termoAceito")
    termoAceitoData = models.DateTimeField(null=True, blank=True, db_column="termoAceitoData")
    dataVerificacaoHotmart = models.DateTimeField(null=True, blank=True, db_column="dataVerificacaoHotmart")
    idProduto = models.CharField(max_length=255, null=True, blank=True, db_column="idProduto")
    cla = models.IntegerField(null=True, blank=True, default=0)
    nivel = models.IntegerField(null=True, blank=True, default=0)
    alunoConsultor = models.IntegerField(null=True, blank=True, default=0, db_column="alunoConsultor")
    observacao = models.TextField(null=True, blank=True)
    hashUserAcessoDesktop = models.CharField(max_length=255, null=True, blank=True, db_column="hashUserAcessoDesktop")
    hashUserAcessoMobile = models.CharField(max_length=255, null=True, blank=True, db_column="hashUserAcessoMobile")
    campAnterior = models.IntegerField(null=True, blank=True, default=0, db_column="campAnterior")
    tagsInterna = models.CharField(max_length=255, null=True, blank=True, db_column="tagsInterna")
    ultimaVisita = models.DateField(null=True, blank=True, db_column="ultimaVisita")
    idIntercom = models.CharField(max_length=255, null=True, blank=True, db_column="idIntercom")

    class Meta:
        db_table = "alunos"

    def __str__(self):
        return self.nome_completo or "Aluno Sem Nome"

class AlunoEnvio(models.Model):
    id = models.AutoField(primary_key=True)
    campeonato = models.IntegerField(null=True, blank=True)
    # vinculoAluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="envios")
    vinculoAluno = models.IntegerField(null=True, blank=True)
    vinculoCliente = models.IntegerField(null=True, blank=True)
    vinculoContrato = models.IntegerField(null=True, blank=True, default=0)
    data = models.DateField(null=True, blank=True)
    descricao = models.CharField(max_length=255, null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    numeroNota = models.CharField(max_length=255, null=True, blank=True)
    arquivo1 = models.CharField(max_length=255, null=True, blank=True)
    arquivo1Motivo = models.IntegerField(null=True, blank=True)
    arquivo1Status = models.IntegerField(null=True, blank=True, default=0)
    arquivo2 = models.CharField(max_length=255, null=True, blank=True)
    arquivo2Motivo = models.IntegerField(null=True, blank=True)
    arquivo2Status = models.IntegerField(null=True, blank=True, default=0)
    texto = models.TextField(null=True, blank=True)
    textoMotivo = models.IntegerField(null=True, blank=True)
    textoStatus = models.IntegerField(null=True, blank=True)
    pontos = models.IntegerField(null=True, blank=True, default=0)
    pontoCreditado = models.IntegerField(null=True, blank=True, default=0)
    pontosPreenchidos = models.IntegerField(null=True, blank=True, default=0)
    pontosReais = models.IntegerField(null=True, blank=True, default=0)
    desafio = models.IntegerField(null=True, blank=True, default=0)
    dataCadastro = models.DateTimeField(null=True, blank=True)
    rastreadorAnalise = models.IntegerField(null=True, blank=True)
    dataAnalise = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    statusMotivo = models.IntegerField(null=True, blank=True)
    statusComentario = models.TextField(null=True, blank=True)
    statusAlteradoForcado = models.IntegerField(null=True, blank=True, default=0)
    tagExcecao = models.CharField(max_length=255, null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    envioNivelInicial = models.IntegerField(null=True, blank=True, default=0)
    tipo = models.IntegerField(null=True, blank=True)
    tipoManual = models.IntegerField(null=True, blank=True)
    envioSociedade = models.IntegerField(null=True, blank=True, default=0)
    vinculoCertificacao = models.IntegerField(null=True, blank=True)
    vinculoCertificacaoProva = models.IntegerField(null=True, blank=True)
    nivelAtualSemana = models.IntegerField(null=True, blank=True)
    comentarioObservacoes = models.BinaryField(null=True, blank=True)
    comentarioArquivo = models.CharField(max_length=255, null=True, blank=True)
    statusAuditoria = models.IntegerField(null=True, blank=True, default=0)

    class Meta:
        db_table = "alunosenvios"

    def __str__(self):
        return f"Envio {self.id} - {self.descricao or 'Sem descrição'}"

class AlunoCliente(models.Model):
    id = models.AutoField(primary_key=True)
    campeonato = models.IntegerField(null=True, blank=True)
    aluno = models.IntegerField(null=True, blank=True)
    titulo = models.CharField(max_length=255, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)
    estrangeiro = models.IntegerField(null=True, blank=True, default=0)
    tipoCliente = models.IntegerField(null=True, blank=True)
    tipoContrato = models.IntegerField(null=True, blank=True)
    sociedade = models.IntegerField(null=True, blank=True)
    porcentagemContrato = models.CharField(max_length=255, null=True, blank=True)
    valorContrato = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vinculoEnvioCliente = models.IntegerField(null=True, blank=True)
    dataContrato = models.DateField(null=True, blank=True)
    clienteAntesSubidoPro = models.IntegerField(null=True, blank=True)
    documentoANTIGO = models.CharField(max_length=255, null=True, blank=True)
    documento = models.CharField(max_length=255, null=True, blank=True)
    telefone = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    dataCriacao = models.DateTimeField(null=True, blank=True)
    rastreador = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    motivoInvalido = models.IntegerField(null=True, blank=True)
    descricaoInvalido = models.TextField(null=True, blank=True)
    semPontuacao = models.IntegerField(null=True, blank=True, default=0)
    rastreadorAnalise = models.IntegerField(null=True, blank=True)
    analiseData = models.DateTimeField(null=True, blank=True)
    pontos = models.IntegerField(null=True, blank=True, default=0)
    semana = models.IntegerField(null=True, blank=True)
    campAnterior = models.IntegerField(null=True, blank=True, default=0)
    idCampAnterior = models.IntegerField(null=True, blank=True)
    statusAuditoria = models.IntegerField(null=True, blank=True, default=0)

    class Meta:
        db_table = "alunosclientes"

    def __str__(self):
        return self.titulo or "Aluno Cliente Sem Titulo"
    
class AlunoClienteContrato(models.Model):
    id = models.AutoField(primary_key=True)
    campeonato = models.IntegerField(null=True, blank=True)
    aluno = models.IntegerField(null=True, blank=True)
    cliente = models.IntegerField(null=True, blank=True)
    tipoContrato = models.IntegerField(null=True, blank=True)
    valorContrato = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    porcentagemContrato = models.CharField(max_length=255, null=True, blank=True)
    arquivo1 = models.CharField(max_length=255, null=True, blank=True)
    arquivo1S3 = models.IntegerField(null=True, blank=True, default=0)
    arquivo2 = models.CharField(max_length=255, null=True, blank=True)
    arquivo2S3 = models.IntegerField(null=True, blank=True, default=0)
    semana = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True, default=0)
    dataContrato = models.DateField(null=True, blank=True)
    dataVencimento = models.DateField(null=True, blank=True)
    dataCriacao = models.DateTimeField(null=True, blank=True)
    motivoInvalido = models.IntegerField(null=True, blank=True)
    descricaoInvalido = models.TextField(null=True, blank=True)
    rastreadorAnalise = models.IntegerField(null=True, blank=True)
    analiseData = models.DateTimeField(null=True, blank=True)
    campAnterior = models.IntegerField(null=True, blank=True, default=0)
    idCampAnterior = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "alunosclientescontratos"

    def __str__(self):
        return f"Contrato {self.id} - {self.cliente}"
    
class AlunoPosicaoSemana(models.Model):
    id = models.AutoField(primary_key=True)
    aluno = models.IntegerField(null=True, blank=True)
    cla = models.IntegerField(null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    posicao = models.IntegerField(null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)
    data = models.DateTimeField(null=True, blank=True)
    pontos = models.IntegerField(null=True, blank=True)
    campeonato = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "alunosposicoessemana"

    def __str__(self):
        return f"Posição {self.posicao} - Semana {self.semana} - Aluno {self.aluno}"

class AlunoPosicaoSemanaLog(models.Model):
    id = models.AutoField(primary_key=True)
    aluno = models.IntegerField(null=True, blank=True)
    cla = models.IntegerField(null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    posicao = models.IntegerField(null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)
    data = models.DateTimeField(null=True, blank=True)
    pontos = models.IntegerField(null=True, blank=True)
    campeonato = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "alunosposicoessemanaLogs"

    def __str__(self):
        return f"Log {self.id} - Aluno {self.aluno} - Semana {self.semana}"

class MentoriaCla(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255, null=True, blank=True)
    sigla = models.CharField(max_length=10, null=True, blank=True)
    rastreador = models.IntegerField(null=True, blank=True, default=0)
    rastreadorSubstituto = models.IntegerField(null=True, blank=True, default=0)
    definido = models.IntegerField(null=True, blank=True, default=0)
    descricao = models.TextField(null=True, blank=True)
    brasao = models.TextField(null=True, blank=True)
    whatsapp = models.TextField(null=True, blank=True)
    campeonato = models.IntegerField(null=True, blank=True)
    idIntercom = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "mentoriacla"

    def __str__(self):
        return self.nome or "Mentoria CLA"
    
class alunosClientesPontosMesesRetencao(models.Model):
    id = models.IntegerField(primary_key=True)
    aluno = models.IntegerField(null=True, blank=True)
    cliente = models.IntegerField(null=True, blank=True)
    campeonato = models.IntegerField(null=True, blank=True)
    data = models.DateField(null=True, blank=True)
    pontos = models.IntegerField(null=True, blank=True)
    qtdEnvios = models.IntegerField(null=True, blank=True)
    idsEnvios = models.TextField(null=True, blank=True)
    semana = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = "alunosclientespontosmesesretencao"
    
    def __str__(self):
        return self.id
    
