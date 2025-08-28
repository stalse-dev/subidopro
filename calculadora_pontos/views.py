from django.shortcuts import render, HttpResponse, redirect
from django.utils import timezone
from subidometro.models import *
from django.db.models import OuterRef, Subquery, F, Count, Sum, Exists
from django.db.models.functions import TruncMonth
from datetime import date, datetime
from .utils import *
from collections import defaultdict

def BalanceamentoView(request):
    resultado = calcula_balanceamento()

    return render(request, 'Balanceamento/balanceamento.html', {
        'pontuacoes': resultado['pontuacoes'],
        'pontos_modificados': resultado['pontos_modificados'],
    })

def RetencaoView(request):
    executar_calculo_retencao_retroativo()
    return HttpResponse(f"Retenção calculada com sucesso! Data: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")

def RankingView(request):
    executar_calculo_retencao_rank()
    return HttpResponse("Ranking calculado com sucesso!")