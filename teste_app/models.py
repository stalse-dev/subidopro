from django.db import models

class TestEnvioLog(models.Model):
    STATUS_CHOICES = [
        ("sucesso", "Sucesso"),
        ("erro", "Erro"),
    ]

    TEST_CHOICES = [
        ("aprovacao_envio_valor_fixo", "Aprovação de Envio de Valor Fixo"),
        ("aprovacao_envio_coproducao", "Aprovação de Envio de Coprodução"),
    ]
    
    rota = models.CharField(max_length=255)
    json_entrada = models.JSONField(null=True, blank=True)
    json_saida = models.JSONField(null=True, blank=True)
    teste = models.CharField(max_length=100, choices=TEST_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    mensagem = models.TextField()
    detalhes = models.JSONField(null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "test_envio_log"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"[{self.status.upper()}] {self.criado_em:%Y-%m-%d %H:%M:%S}"
