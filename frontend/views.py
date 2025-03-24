from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from subidometro.models import *
from .serializers import AlunosPosicoesSemanaSerializer
from subidometro.utils import *
from math import ceil

class AlunosPosicoesSemanaPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        total_pages = ceil(total_items / self.page_size)
        page = self.page.number

        # Obtém campeonato e semana vigente
        campeonato, _ = calcular_semana_vigente()

        # Busca todas as semanas distintas disponíveis no banco
        semanas_disponiveis = (
            Alunos_posicoes_semana.objects
            .filter(campeonato=campeonato)
            .values_list("semana", flat=True)
            .distinct()
        )

        # Formata as semanas no dicionário esperado
        semanas = {str(semana): f"Semana {semana}" for semana in semanas_disponiveis}

        return Response({
            "count": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
            "pagination": {
                "first": 1,
                "last": total_pages,
                "has_previous": page > 1,
                "has_next": page < total_pages,
                "pages": list(range(1, total_pages + 1))[:5]
            },
            "semanas_disponiveis": semanas  # Adicionando as semanas existentes
        })

class SemanaVigenteMixin:
    def get_semana_vigente_queryset(self, queryset):
        campeonato, semana = calcular_semana_vigente()
        return queryset.filter(semana=semana, campeonato=campeonato)

class AlunosPosicoesSemanaListView(generics.ListAPIView):
    serializer_class = AlunosPosicoesSemanaSerializer
    pagination_class = AlunosPosicoesSemanaPagination

    def get_queryset(self):
        # Obtém os parâmetros da requisição
        request = self.request
        nome_email = request.GET.get("q")  # Filtro por nome ou email
        semana_param = request.GET.get("semana")  # Filtro por semana

        # Obtém campeonato e semana vigente
        campeonato, semana_vigente = calcular_semana_vigente()

        # Se o usuário passar uma semana, usamos ela. Caso contrário, usamos a vigente.
        semana = int(semana_param) if semana_param and semana_param.isdigit() else semana_vigente

        # Base da query
        queryset = Alunos_posicoes_semana.objects.filter(semana=semana, campeonato=campeonato).order_by("posicao")

        # Aplica filtro por nome ou email, se fornecido
        if nome_email:
            queryset = queryset.filter(
                Q(aluno__nome_completo__icontains=nome_email) | 
                Q(aluno__email__icontains=nome_email)
            )

        return queryset

