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
            "thiago@stalse.com",
            "gabriel@stalse.com",
        ]

        password = "permaneo@123"

        for email in users_data:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_superuser(email=email, name="Admin", password=password)
                self.stdout.write(self.style.SUCCESS(f'Usuário {email} criado com sucesso!'))
            else:
                self.stdout.write(self.style.WARNING(f'Usuário {email} já existe!'))
