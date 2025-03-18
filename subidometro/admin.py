from django.contrib import admin
from .models import *

admin.site.register(Alunos)
admin.site.register(Aluno_clientes)
admin.site.register(Aluno_clientes_contratos)
admin.site.register(Aluno_envios)
admin.site.register(Desafios)

#admin.site.register(TipoPontuacao)

admin.site.register(Campeonato)
admin.site.register(Mentoria_cla)
admin.site.register(Mentoria_cla_posicao_semana)
admin.site.register(Alunos_posicoes_semana)
admin.site.register(Alunos_clientes_pontos_meses_retencao)


#admin.site.register(Aluno_pontuacao)
admin.site.register(Aluno_desafio)
admin.site.register(Aluno_certificacao)
admin.site.register(Aluno_contrato)
admin.site.register(Alunos_Subidometro)


