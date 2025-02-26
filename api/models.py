from django.db import models
from django.utils.timezone import now

class Log(models.Model):
    STATUS_CHOICES = [
        ('sucesso', 'Sucesso'),
        ('erro', 'Erro'),
    ]

    acao = models.CharField(max_length=10)  # add, alt, del
    tabela = models.CharField(max_length=50)
    dados_anteriores = models.JSONField(null=True, blank=True)
    dados_novos = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sucesso')
    erro = models.TextField(null=True, blank=True)  # Para armazenar a mensagem de erro, se houver
    criado_em = models.DateTimeField(default=now)
    dados_geral = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.acao} - {self.tabela} - {self.status} - {self.criado_em}"


