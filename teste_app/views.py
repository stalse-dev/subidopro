# teste_app/views.py
from django.http import JsonResponse
from subidometro.models import *
import requests
from .utils import *

def TestViewEnvioAprove(request):
    response = test_aprove_envio()
    return JsonResponse(response)

def teste(request):
    response = teste_all_pontos()
    # date_now = str(date.today())
    # #cliente_id = test_post_envio(13, 2, 6, 6, date_now)
    # cliente = test_patch_envio(14, 3)
    # cliente = test_get_envio(14)
    # print(cliente.get('pontos'))


    return JsonResponse({
        "resposta": True
    })
