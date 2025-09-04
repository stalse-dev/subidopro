from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from subidometro.models import *
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count, Func, CharField, IntegerField, Max, Q, Case, When
from rest_framework import status
from collections import defaultdict
from .serializers import *

class HomeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, aluno_id):
        aluno = Alunos.objects.filter(id=aluno_id).first()
        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)
        
        campeonato_ativo = aluno.campeonato

        #campeonato_ativo = Campeonato.objects.filter(ativo=True).first()

        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        top10_cla_qs = Mentoria_cla_posicao_semana.objects.filter(
            campeonato=campeonato_ativo
        ).order_by('-semana', 'posicao')

        maior_semana_obj = top10_cla_qs.first()
        
        if maior_semana_obj: maior_semana = maior_semana_obj.semana
        else: maior_semana = 0


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
    serializer_class = RankAlunoDetalhesSerializer

    def get(self, request, campeonato_id):
        campeonato_ativo = Campeonato.objects.filter(id=campeonato_id, ativo=True).first()
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

class RankingClaAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RankClaDetalhesSerializer

    def get(self, request, campeonato_id):
        campeonato_ativo = Campeonato.objects.filter(id=campeonato_id, ativo=True).first()
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
            Mentoria_cla_posicao_semana.objects
            .select_related('cla')
            .filter(campeonato=campeonato_ativo, semana=semana)
            .order_by('posicao')[:100]
        )

        serializer = RankClaDetalhesSerializer(rank_alunos, many=True)
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
        
        campeonato_ativo = aluno.campeonato
        
        #campeonato_ativo = Campeonato.objects.filter(ativo=True).first()

        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        maior_semana_obj = (Alunos_posicoes_semana.objects.filter(campeonato=campeonato_ativo).order_by('-semana').only('semana').first())

        if maior_semana_obj: semana = maior_semana_obj.semana
        else: semana = 0

        pontos_campeonato = Alunos_posicoes_semana.objects.filter(aluno=aluno, campeonato=campeonato_ativo, semana=semana).first()

        if pontos_campeonato:
            pontos_desafio = int(round(pontos_campeonato.pontos_desafio or 0))
            pontos_certificacao = int(round(pontos_campeonato.pontos_certificacao or 0))
            pontos_manual = int(round(pontos_campeonato.pontos_manual or 0))
            pontos_contrato = int(round(pontos_campeonato.pontos_contrato or 0))
            pontos_retencao = int(round(pontos_campeonato.pontos_retencao or 0))
        else:
            pontos_desafio = 0
            pontos_certificacao = 0
            pontos_manual = 0
            pontos_contrato = 0
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
    serializer_class = ClientesSerializer

    def get(self, request, aluno_id):
        aluno = Alunos.objects.filter(id=aluno_id).first()
        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)

        clientes_data = Aluno_clientes.objects.filter(aluno=aluno).order_by('-data_criacao')

        if not clientes_data:
            return Response({"detail": "Nenhum cliente encontrado."}, status=404)

        clientes = ClientesSerializer(clientes_data)

        return Response(
            {
                "total_clientes": clientes_data.count(),
                "clientes": clientes
            }
        )

class MeusEnviosAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, aluno_id):
        aluno = Alunos.objects.filter(id=aluno_id).first()
        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)
        
        campeonato_ativo = aluno.campeonato
        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        maior_semana_obj = (Alunos_posicoes_semana.objects.filter(campeonato=campeonato_ativo).order_by('-semana').only('semana').first())
        if maior_semana_obj: semana = maior_semana_obj.semana
        else: semana = 0

        proximo_semana = semana + 1
        envios_da_semana = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato_ativo, semana=proximo_semana).count()

        envios_data = Aluno_envios.objects.filter(aluno=aluno, campeonato=campeonato_ativo, data_cadastro__gte=campeonato_ativo.data_inicio).order_by('-data_cadastro')
        envios = MeusEnviosSerializer(envios_data, campeonato_ativo.data_inicio)


        return Response(
            {
                "campeonato": campeonato_ativo.identificacao,
                "semana": semana,
                "total_envios": envios_da_semana,
                "envios": envios
            }
        )

class SubdometroAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, aluno_id):
        aluno = Alunos.objects.filter(id=aluno_id).first()
        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)

        campeonato_ativo = aluno.campeonato
        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        maior_semana_obj = (Alunos_posicoes_semana.objects.filter(campeonato=campeonato_ativo).order_by('-semana').only('semana').first())
        if maior_semana_obj: semana = maior_semana_obj.semana
        else: semana = 0

        data_int = datetime.strptime('2024-09-01', '%Y-%m-%d').date()

        clientes = Aluno_clientes.objects.filter(aluno=aluno, status=1)
        total_valores_envios = Aluno_envios.objects.filter(aluno=aluno, status=3, semana__gt=0, data__gte=data_int).aggregate(total=Sum('valor_calculado'))['total'] or 0
        total_valor_camp = Aluno_camp_faturamento_anterior.objects.filter(aluno=aluno).aggregate(total=Sum('valor'))['total'] or 0
        soma_total_faturamento = float(total_valores_envios) + float(total_valor_camp)
        mes_mais_ganhou = (
            Aluno_envios.objects
            .filter(aluno=aluno, status=3, semana__gt=0, data__gte=data_int)
            .annotate(mes=TruncMonth('data'))  # Agrupa por mês
            .values('mes')  # Seleciona apenas o mês
            .annotate(total_mes=Sum('valor_calculado'))  # Soma os valores por mês
            .order_by('-total_mes')  # Ordena do maior para o menor
            .first()  # Pega o primeiro, que é o maior
        )
        mes_mais_ganhou_valor = mes_mais_ganhou['total_mes'] if mes_mais_ganhou else 0

        todos_ganhos_mes = Aluno_envios.objects.filter(aluno=aluno, status=3, semana__gt=0, data__gte=data_int).order_by('-data')
        evolucao_ganhos_por_mes = EvolucaoMesSerializer(todos_ganhos_mes)


        subdometro_data = Alunos_Subidometro.objects.filter(aluno=aluno, campeonato=campeonato_ativo).order_by('semana')
        evolucao_ganhos_por_semana = EvolucaoSemanaSerializer(subdometro_data, semana)

        return Response({
            "campeonato": campeonato_ativo.identificacao,
            "semana": semana,
            "evolucao_aluno": {
                "total_clientes": clientes.count(),
                "total_faturamento": f"R$ {soma_total_faturamento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                "mes_maior_faturamento": f"R$ {mes_mais_ganhou_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            },
            "evolucao_ganhos_por_mes": evolucao_ganhos_por_mes,
            "evolucao_ganhos_por_semana": evolucao_ganhos_por_semana,
        })

class DetalhesClientesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlunoClientesSerializer

    def get(self, request, cliente_id):
        cliente = Aluno_clientes.objects.filter(id=cliente_id).first()
        if not cliente:
            return Response({"detail": "Cliente não encontrado."}, status=404)

        tipo_cliente = "Pessoa Física" if cliente.tipo_cliente == 1 else "Pessoa Jurídica"
        status = "Aprovado" if cliente.status == 1 else "Inativo"

        contratos = ContratosSerializer(cliente.contratos.all())

        envios = EnviosSerializer(cliente.envios_cliente_cl.all())

        response_data = {
            'cliente': {
                'id': str(cliente.id),
                'titulo': cliente.titulo,
                'tipo': tipo_cliente,
                'documento': cliente.documento,
                'status': status,
                'data_criacao': cliente.data_criacao.strftime('%d/%m/%Y %H:%M:%S'),
                'total_contratos': cliente.contratos.count(),
                'total_envios': cliente.envios_cliente_cl.count(),

            },
            'contratos': contratos,
            "envios": envios
        }

        return Response(response_data)
        
class MeuClaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, aluno_id):
        aluno = Alunos.objects.filter(id=aluno_id).first()
        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)
        
        campeonato_ativo = aluno.campeonato
        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        maior_semana_obj = (Alunos_posicoes_semana.objects.filter(campeonato=campeonato_ativo).order_by('-semana').only('semana').first())
        if maior_semana_obj: semana = maior_semana_obj.semana
        else: semana = 0

        cla = aluno.cla
        if cla.id == 0:
            return Response({"detail": "CLA não encontrado para este aluno."}, status=404)

        if not cla:
            return Response({"detail": "CLA não encontrado para este aluno."}, status=404)

        cla_data = {
            "id": str(cla.id),
            "titulo": cla.nome,
            "sigla": cla.sigla or "",
            "qtdAlunos": str(cla.aluno_cla.count())
        }

        #data_int = datetime.strptime('2024-09-01', '%Y-%m-%d').date()
        data_int = campeonato_ativo.data_inicio
        alunos = AlunosListClaSerializer(cla.aluno_cla.filter(status='ACTIVE'), campeonato_ativo, data_int, semana)

        return Response({
            "campeonato": campeonato_ativo.identificacao,
            "semana": semana,
            "cla": cla_data,
            "alunos": alunos
        })

class PontosSemanaisAlunoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, aluno_id):
        aluno = Alunos.objects.filter(id=aluno_id).first()
        if not aluno:
            return Response({"detail": "Aluno não encontrado."}, status=404)

        campeonato_ativo = aluno.campeonato
        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        posicoes = (
            Alunos_posicoes_semana.objects
            .filter(aluno=aluno, campeonato=campeonato_ativo)
            .order_by("semana")
        )

        resultado = []
        posicao_anterior = None

        for registro in posicoes:
            delta = None
            tendencia = None

            if posicao_anterior is not None:
                delta = posicao_anterior - registro.posicao if registro.posicao is not None else None
                if delta is not None:
                    if delta > 0:
                        tendencia = "subiu"
                    elif delta < 0:
                        tendencia = "desceu"
                    else:
                        tendencia = "manteve"
            
            resultado.append({
                "semana": registro.semana,
                "posicao": registro.posicao,
                "delta": delta,
                "tendencia": tendencia,
                "pontos_recebimento": int(registro.pontos_recebimento),
                "pontos_desafio": int(registro.pontos_desafio),
                "pontos_certificacao": int(registro.pontos_certificacao),
                "pontos_manual": int(registro.pontos_manual),
                "pontos_contrato": int(registro.pontos_contrato),
                "pontos_retencao": int(registro.pontos_retencao),
                "pontos_totais": int(registro.pontos_totais),
                "data": registro.data,
            })

            posicao_anterior = registro.posicao

        return Response(resultado)

class PontosSemanaisClaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, cla_id):
        cla = Mentoria_cla.objects.filter(id=cla_id).first()
        if not cla:
            return Response({"detail": "CLA não encontrado."}, status=404)

        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
        if not campeonato_ativo:
            return Response({"detail": "Nenhum campeonato ativo encontrado."}, status=404)

        posicoes = (
            Mentoria_cla_posicao_semana.objects
            .filter(cla=cla, campeonato=campeonato_ativo)
            .order_by("semana")
        )

        resultado = []
        posicao_anterior = None

        for registro in posicoes:
            delta = None
            tendencia = None

            if posicao_anterior is not None:
                delta = posicao_anterior - registro.posicao if registro.posicao is not None else None
                if delta is not None:
                    if delta > 0:
                        tendencia = "subiu"
                    elif delta < 0:
                        tendencia = "desceu"
                    else:
                        tendencia = "manteve"
            
            resultado.append({
                "semana": registro.semana,
                "posicao": registro.posicao,
                "delta": delta,
                "tendencia": tendencia,
                "pontos_recebimento": int(registro.pontos_recebimento),
                "pontos_desafio": int(registro.pontos_desafio),
                "pontos_certificacao": int(registro.pontos_certificacao),
                "pontos_manual": int(registro.pontos_manual),
                "pontos_contrato": int(registro.pontos_contrato),
                "pontos_retencao": int(registro.pontos_retencao),
                "pontos_totais": int(registro.pontos_totais),
                "data": registro.data,
            })

            posicao_anterior = registro.posicao

        return Response(resultado)
