from django.core.management.base import BaseCommand
from users.models import User

class Command(BaseCommand):
    help = 'Cria usuários administradores automaticamente'

    def handle(self, *args, **kwargs):
        users_data = [
            "flavio.mattos@grupopermaneo.com.br",
            "anacarolina.souza@subidopro.com.br",
            "andre.nikolopoulos@grupopermaneo.com.br",
            "bruna.souza@subidopro.com.br",
            "priscila.gargiulo@grupopermaneo.com.br",
            "lia.piazza@subidopro.com.br",
            "gabrielle.rocha@subidopro.com.br",
            "mariana.campos@grupopermaneo.com.br",
            "producao@inventandus.com.br",
            "thiago@stalse.com",
            "gabriel@stalse.com",
            "anacarolina.souza@grupopermaneo.com.br",
            "anaraira.soares@subidopro.com.br",
            "anderson.silva@subidopro.com.br",
            "bruna.pelegrini@subidopro.com.br",
            "cinthia.iervolino@subidopro.com.br",
            "eduarda.melo@subidopro.com.br",
            "eduardo.lima@subidopro.com.br",
            "fabiana.souza@subidopro.com.br",
            "gabriela.paiva@subidopro.com.br",
            "gabriela.santos@subidopro.com.br",
            "gisele.ferreira@subidopro.com.br",
            "jonathan.faria@subidopro.com.br",
            "lais.cordeiro@subidopro.com.br",
            "lucas.pedroso@subidopro.com.br",
            "maria.santos@subidopro.com.br",
            "nathalya.ribeiro@subidopro.com.br",
            "priscila.silva@subidopro.com.br",
            "raissa.feitosa@subidopro.com.br",
            "renata.luz@subidopro.com.br",
            "taynara.santiago@subidopro.com.br",
            "valeria.souza@subidopro.com.br",
            "victoria.assis@subidopro.com.br",
            "vivian.antonio@subidopro.com.br"
        ]

        superuser_emails = [
            "gabrielle.rocha@subidopro.com.br", 
            "bruna.souza@subidopro.com.br",
            "priscila.gargiulo@grupopermaneo.com.br",
            "anacarolina.souza@grupopermaneo.com.br",
            "andre.nikolopoulos@grupopermaneo.com.br",
            "thiago@stalse.com",
            "gabriel@stalse.com",
            "producao@inventandus.com.br",
            "mariana.campos@grupopermaneo.com.br",
            "flavio.mattos@grupopermaneo.com.br",
        ]

        password = "permaneo@123"

        for email in users_data:
            if not User.objects.filter(email=email).exists():
                nome = email.split('@')[0].replace('.', ' ').title()
                if email in superuser_emails:
                    user = User.objects.create_superuser(email=email, name=nome, password=password)
                else:
                    user = User.objects.create_user(email=email, name=nome, password=password)
                self.stdout.write(self.style.SUCCESS(f'Usuário {email} criado com sucesso!'))
            else:
                self.stdout.write(self.style.WARNING(f'Usuário {email} já existe!'))
