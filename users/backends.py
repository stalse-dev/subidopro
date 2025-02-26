from django.contrib.auth.backends import BaseBackend
from .models import User
import secrets
import re

class UserBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
class TokenBackend(BaseBackend):
    def generate_token():
        """
        Função para gerar um token aleatório de 6 dígitos.
        """
        token = secrets.randbelow(1000000)  # Gera um número aleatório de 0 a 999999
        return f"{token:06d}"
    
    def validar_senha(senha):
        if (len(senha) >= 8 and
            re.search(r'[A-Z]', senha) and
            re.search(r'[0-9]', senha) and
            re.search(r'[!@#$%^&*(),.?":{}|<>]', senha)):
            return True
        return False
    