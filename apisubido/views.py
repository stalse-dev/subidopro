from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from subidometro.models import *
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count, Func, CharField, IntegerField, Max, Q, Case, When
from collections import defaultdict
from .serializers import *

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

        aluno = Alunos.objects.filter(id=aluno_id).first()

        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)


        total_clientes = Aluno_clientes.objects.filter(aluno=aluno, status=1).count()

        mes_mais_ganhou = (
            Aluno_envios.objects
            .filter(aluno=aluno, status=3, semana__gt=0, data__gte=campeonato_ativo.data_inicio)
            .annotate(mes=TruncMonth('data'))
            .values('mes')
            .annotate(total_mes=Sum('valor_calculado'))
            .order_by('-total_mes')
            .first() 
        )

        mes_mais_ganhou_valor = mes_mais_ganhou['total_mes'] if mes_mais_ganhou else 0

        # Buscar faturamento dos envios# Somar Valores de todos os envios que o tipo de contrato seja = 2
        total_valores_envios = Aluno_envios.objects.filter(aluno=aluno, status=3, semana__gt=0, data__gte=campeonato_ativo.data_inicio).aggregate(total=Sum('valor_calculado'))['total'] or 0

        #Buscar faturamento dos campeonatos antigos
        total_valor_camp = Aluno_camp_faturamento_anterior.objects.filter(aluno=aluno).aggregate(total=Sum('valor'))['total'] or 0

        total_total_total = float(total_valores_envios) + float(total_valor_camp)


        pontos_aluno = Alunos_posicoes_semana.objects.filter(
            aluno=aluno,
            campeonato=campeonato_ativo,
            semana=maior_semana
        ).first()

        # Dados do cla do aluno
        pontos_cla = Mentoria_cla_posicao_semana.objects.filter(
            cla=aluno.cla,
            campeonato=campeonato_ativo,
            semana=maior_semana
        ).first()

        subidometro = {
            "posicao": pontos_aluno.posicao if pontos_aluno else None,
            "pontos": pontos_aluno.pontos_totais if pontos_aluno else None,
            "posicao_;cla": pontos_cla.posicao if pontos_cla else None,
            "pontos_cla": pontos_cla.pontos_totais if pontos_cla else None,
        }


        top10_alunos = Alunos_posicoes_semana.objects.filter(
            campeonato=campeonato_ativo, semana=maior_semana
        ).order_by('posicao')[:10]

        top10_cla = top10_cla_qs.filter(semana=maior_semana)[:10]

        serializer_cla = RankClaSerializer(top10_cla, many=True)
        serializer_alunos = RankAlunoSerializer(top10_alunos, many=True)


        
        return Response({
            "campeonato": campeonato_ativo.identificacao,
            "semana": maior_semana,
            "evolucao": {
                "total_clientes": f"{total_clientes} clientes",
                "total_faturamento": f"R$ {total_total_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                "mes_maior_faturamento": f"R$ {mes_mais_ganhou_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),  
            },
            "subidometro": subidometro,
            "placa_campeonato": {
                "alunos_rank": serializer_alunos.data,
                "cla_rank": serializer_cla.data
            }
        })

class RankingSemanalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        # Buscar semana mais recente
        maior_semana_obj = (
            Alunos_posicoes_semana.objects
            .filter(campeonato=campeonato_ativo)
            .order_by('-semana')
            .only('semana')
            .first()
        )
        if not maior_semana_obj:
            return Response({"detail": "Nenhuma semana encontrada."}, status=404)

        semana = maior_semana_obj.semana

        # Buscar ranking com otimização
        rank_alunos = (
            Alunos_posicoes_semana.objects
            .select_related('aluno', 'cla')  # Evita N+1
            .filter(campeonato=campeonato_ativo, semana=semana)
            .order_by('posicao')[:100]
        )

        serializer = RankAlunoDetalhesSerializer(rank_alunos, many=True)
        return Response({
            "campeonato": campeonato_ativo.identificacao,
            "semana": semana,
            "rank_alunos": serializer.data
        })

class ExtratoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, aluno_id):
        aluno = Alunos.objects.filter(id=aluno_id).first()
        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)
        
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()

        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        maior_semana_obj = (Alunos_posicoes_semana.objects.filter(campeonato=campeonato_ativo).order_by('-semana').only('semana').first())

        if not maior_semana_obj:
            return Response({"detail": "Nenhuma semana encontrada."}, status=404)
        
        semana = maior_semana_obj.semana

        pontos_campeonato = Alunos_posicoes_semana.objects.filter(aluno=aluno, campeonato=campeonato_ativo, semana=semana).first()

        if pontos_campeonato:
            pontos_desafio = int(round(pontos_campeonato.pontos_desafio or 0))
            pontos_certificacao = int(round(pontos_campeonato.pontos_certificacao or 0))
            pontos_manual = int(round(pontos_campeonato.pontos_manual or 0))
            pontos_contrato = int(round(pontos_campeonato.pontos_contrato or 0))
            pontos_retencao = int(round(pontos_campeonato.pontos_retencao or 0))
        else:
            pontos_retencao = 0





        envios_data = Aluno_envios.objects.filter(campeonato=campeonato_ativo, aluno=aluno, status=3).order_by('-data_cadastro')
        envios = AlunoEnviosExtratoSerializer(envios_data, semana)

        desafios_data = Aluno_desafio.objects.filter(campeonato=campeonato_ativo, aluno=aluno, status=3).order_by('-data_cadastro')
        desafios = AlunoDesafioExtratoSerializer(desafios_data, semana, pontos_desafio)

        certificacao_data = Aluno_certificacao.objects.filter(campeonato=campeonato_ativo, aluno=aluno, status=3, tipo=3).order_by('-data_cadastro')
        certificacao = AlunoCertificacaoExtratoSerializer(certificacao_data, semana, pontos_certificacao)

        manual_data = Aluno_certificacao.objects.filter(campeonato=campeonato_ativo, aluno=aluno, status=3, tipo=5).order_by('-data_cadastro')
        manual = AlunoManualExtratoSerializer(manual_data, semana, pontos_manual)

        contratos_data = Aluno_contrato.objects.filter(aluno=aluno, pontos__gt=0, campeonato=campeonato_ativo, status=3).order_by('-data_cadastro')
        contratos = AlunoContratoExtratoSerializer(contratos_data, pontos_contrato)

        retencao = Alunos_clientes_pontos_meses_retencao.objects.filter(aluno=aluno, campeonato=campeonato_ativo).order_by('-data')
        retencao = AlunosRetencaoExtratoSerializer(retencao, pontos_retencao)


        return Response({
            "campeonato": campeonato_ativo.identificacao,
            "semana": semana,
            "envios": envios,
            "desafios": desafios,
            "certificacoes": certificacao,
            "manuais": manual,
            "contratos": contratos,
            "retencao": retencao
        })

class ClientesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, aluno_id):
        aluno = Alunos.objects.filter(id=aluno_id).first()
        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)

        clientes_data = Aluno_clientes.objects.filter(aluno=aluno).order_by('-data_criacao')

        clientes = ClientesSerializer(clientes_data)

        return Response(
            {
                "total_clientes": clientes.count(),
                "clientes": clientes
            }
        )

class MeusEnviosAPIView(APIView):
    #permission_classes = [IsAuthenticated]

    def get(self, request, aluno_id):
        aluno = Alunos.objects.filter(id=aluno_id).first()
        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)
        
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        maior_semana_obj = (Alunos_posicoes_semana.objects.filter(campeonato=campeonato_ativo).order_by('-semana').only('semana').first())
        if not maior_semana_obj:
            return Response({"detail": "Nenhuma semana encontrada."}, status=404)
        semana = maior_semana_obj.semana
        proximo_semana = semana + 1
        envios_da_semana = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato_ativo, semana=proximo_semana).count()

        envios_data = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato_ativo, data_cadastro__gte=campeonato_ativo.data_inicio).order_by('-data_cadastro')
        envios = MeusEnviosSerializer(envios_data, campeonato_ativo.data_inicio)


        return Response(
            {
                "total_envios": envios_da_semana,
                "envios": envios
            }
        )


