# teste_app/views.py
from django.http import JsonResponse
from subidometro.models import *
import requests
from .utils import *

def teste(request):
    response = teste_all_pontos()

    return JsonResponse({
        "resposta": response
    })
