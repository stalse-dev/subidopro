from django.http import JsonResponse
from functools import wraps
import time
from datetime import datetime
from django.utils.http import http_date

def allow_cors(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Se for OPTIONS, retorna uma resposta vazia com os cabeçalhos CORS
        if request.method == "OPTIONS":
            response = JsonResponse({})
        else:
            response = view_func(request, *args, **kwargs)
        
        # Adiciona os cabeçalhos CORS
        response["Access-Control-Allow-Origin"] = "*"  # Ou especifique o domínio, se preferir
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
        return response
    return wrapped_view


def build_standard_response(message="", status=401, tempo_inicio=None):
    """
    Monta uma resposta padronizada com os metadados desejados.

    :param user_data: Dicionário com os dados do usuário (opcional).
    :param message: Mensagem de retorno.
    :param status: Código HTTP da resposta.
    :param tempo_inicio: Timestamp de quando a requisição começou (para calcular tempo de retorno).
    :return: Dicionário com a estrutura padronizada.
    """

    tempo_fim = time.time()
    tempo_retorno = round(tempo_fim - tempo_inicio, 4) if tempo_inicio else None

    info = {
        "status": f"HTTP/1.1 {status} OK",
        "date": http_date(datetime.timestamp(datetime.now())),
        "server": "WSGIServer/0.2 CPython/3.10.2",
        "content-type": "application/json",
        "message-info": message,
        "return_time": f"{str (tempo_retorno)} seconds"
    }

    return info

