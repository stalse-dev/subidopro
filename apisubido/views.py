from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from subidometro.models import *
from .serializers import *

class ProtectedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        identificador = getattr(user, 'email', None) or getattr(user, 'id', 'ID desconhecido')
        return Response({"message": f"Olá, {identificador}. Esta rota está protegida!"})

class HomeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, aluno_id):
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()

        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        top10_cla_qs = Mentoria_cla_posicao_semana.objects.filter(
            campeonato=campeonato_ativo
        ).order_by('-semana', 'posicao')

        maior_semana_obj = top10_cla_qs.first()
        
        if not maior_semana_obj:
            return Response({"detail": "Nenhuma semana encontrada para o campeonato ativo."}, status=404)
    
        maior_semana = maior_semana_obj.semana


        top10_alunos = Alunos_posicoes_semana.objects.filter(
            campeonato=campeonato_ativo, semana=maior_semana
        ).order_by('posicao')[:10]

        top10_cla = top10_cla_qs.filter(semana=maior_semana)[:10]

        serializer_cla = RankClaSerializer(top10_cla, many=True)
        serializer_alunos = RankAlunoSerializer(top10_alunos, many=True)

        return Response({
            "campeonato": campeonato_ativo.identificacao,
            "semana": maior_semana,
            "alunos_rank": serializer_alunos.data,
            "cla_rank": serializer_cla.data
        })
