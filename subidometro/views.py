from django.shortcuts import render
from django.db import connection
from datetime import datetime
from users.models import *
from datetime import date

def index(request):
    return render(request, 'home.html')

def atualizaPontosLimitesMesesEnvios(request):
    sql_query = """
        SELECT
            alunosenvios."vinculoAluno" AS "idAluno",
            alunos."nomeCompleto",
            alunos.email,
            TO_CHAR(alunosenvios."data", 'YYYY-MM') AS "mesAno",
            COUNT(*) AS "totalEnvios",
            SUM(alunosenvios.valor) AS "totalFaturamento",
            SUM(alunosenvios.pontos) AS "totalPontos",
            SUM(alunosenvios."pontosPreenchidos") AS "totalPontosPreenchidos",
            MAX(alunosenvios."data") AS "ultimaDataEnvio",
            STRING_AGG(alunosenvios.id::TEXT, ',') AS "idsEnvios",
            STRING_AGG(alunosenvios.id::TEXT || '|' || alunosenvios.pontos::TEXT, ',') AS "idsEnviosComPontos"
        FROM
            alunosenvios
        INNER JOIN alunos ON alunos.id = alunosenvios."vinculoAluno"
        WHERE
            alunosenvios.tipo = 2
            AND alunosenvios."status" = 3
            AND alunosenvios.semana > 0
            AND alunosenvios."data" >= '2024-09-01'
        GROUP BY
            alunosenvios."vinculoAluno", "mesAno", alunos."nomeCompleto", alunos.email
        HAVING
            SUM(alunosenvios.pontos) > 3000
        ORDER BY
            alunosenvios."vinculoAluno" ASC, "mesAno" ASC, "totalPontos" DESC;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        results = cursor.fetchall()

    data = []
    for row in results:
        ultrapassou_pontos = row[6] > 3000
        ids_envios_com_pontos = row[10].split(",")
        # Processamento dos pontos
        limite = 3000
        total = 0
        ajustado = []
        zerados = []

        for item in ids_envios_com_pontos:
            id_envio, pontos_envio = item.split("|")
            pontos_envio = int(pontos_envio)

            if total + pontos_envio > limite:
                pontos_restantes = limite - total
                ajustado.append((id_envio, pontos_restantes))
                total += pontos_restantes
                break
            else:
                ajustado.append((id_envio, pontos_envio))
                total += pontos_envio

        # # Atualizar banco de dados
        # with connection.cursor() as cursor:
        #     for id_envio, pontos in ajustado:
        #         cursor.execute("UPDATE alunosenvios SET pontos = %s WHERE id = %s", [pontos, id_envio])

        data.append({
            "idAluno": row[0],
            "nomeCompleto": row[1],
            "email": row[2],
            "mesAno": row[3],
            "totalEnvios": row[4],
            "totalFaturamento": row[5],
            "totalPontos": row[6],
            "totalPontosPreenchidos": row[7],
            "ultimaDataEnvio": row[8],
            "ultrapassouPontos": ultrapassou_pontos,
            "ajustado": ajustado
        })

    return render(request, "atualizaPontosLimitesMesesEnvios.html", {"data": data})

def gera_pontos_clientes(valor):
    if 0 <= valor < 1000:
        return 60
    elif 1000 <= valor < 3000:
        return 480
    elif 3000 <= valor < 5000:
        return 1080
    elif 5000 <= valor < 9000:
        return 1920
    elif valor >= 9000:
        return 2460
    return 0

def gera_pontos_retencao(pontos):
    pontos_map = {60: 40, 480: 320, 1080: 720, 1920: 1280, 2460: 1640}
    return pontos_map.get(pontos, 0)

def calculoRetencaoClientes(request):
    sql_query = """
        SELECT
            ac.id AS "idCliente",
            acc.id AS "idContrato",
            acc."valorContrato" AS "valorContrato",
            acc."tipoContrato" AS "tipoContrato",
            acc."porcentagemContrato" AS "porcentagemContrato",
            acc."dataVencimento" AS "dataVencimentoContrato",
            ae.valor AS "valorEnvio",
            ac.aluno AS "idAluno",
            ac.pontos AS "pontosCliente",
            COUNT(DISTINCT TO_CHAR(ae.data, 'YYYY-MM')) AS "totalEnvios",
            STRING_AGG(
                CONCAT(ae.id, '|', ae.valor, '|', ae.pontos, '|', ae.data),
                ',' 
            ) AS registros
        FROM
            alunosclientes ac
            INNER JOIN alunosenvios ae ON ae."vinculoCliente" = ac.id
            INNER JOIN (
                SELECT cliente, MAX("dataContrato") AS "dataContrato"
                FROM alunosclientescontratos
                WHERE status = 1
                GROUP BY cliente
            ) contratoRecente ON contratoRecente.cliente = ac.id
            INNER JOIN alunosclientescontratos acc ON 
                acc.cliente = contratoRecente.cliente
                AND acc."dataContrato" = contratoRecente."dataContrato"
        WHERE
            ae.status = 3 
            AND ae.tipo = 2 
            AND ac.status = 1 
            AND ae.data BETWEEN '2024-09-01' AND CURRENT_DATE
            AND acc.status = 1 
            AND ae.semana > 0
        GROUP BY
            ac.id,
            acc.id,                 -- Adicionei aqui
            acc."valorContrato",
            acc."tipoContrato",
            acc."porcentagemContrato",
            acc."dataVencimento",
            ae.valor,
            ac.aluno,
            ac.pontos
        HAVING
            COUNT(DISTINCT TO_CHAR(ae.data, 'YYYY-MM')) > 1
        ORDER BY
            COUNT(DISTINCT TO_CHAR(ae.data, 'YYYY-MM')) DESC;
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        clientes = [dict(zip(columns, row)) for row in cursor.fetchall()]

    
    resultados = []
    for cliente in clientes:
        if cliente["totalEnvios"] > 0:
            if int(cliente["tipoContrato"]) == 2 and int(cliente["porcentagemContrato"]) > 0:
                valor_inicial = int(cliente["valorEnvio"])
                porcentagem = int(cliente["porcentagemContrato"])
                valor_final = valor_inicial - (valor_inicial * (porcentagem / 100))
                valor_comissao = valor_inicial - valor_final
                cliente["valorEnvio"] = round(valor_comissao, 2)
                cliente["pontosCliente"] = gera_pontos_clientes(cliente["valorEnvio"])
            else:
                if cliente["valorContrato"] is None:
                    cliente["pontosCliente"] = gera_pontos_clientes(cliente["valorEnvio"])
                else:
                    cliente["pontosCliente"] = gera_pontos_clientes(cliente["valorContrato"])

            pontos_retencao = gera_pontos_retencao(cliente["pontosCliente"])

            resultados.append({
                "idCliente": cliente["idCliente"],
                "idContrato": cliente["idContrato"],
                "dataVencimentoContrato": cliente["dataVencimentoContrato"],
                "pontosGerados": cliente["pontosCliente"],
                "totalEnvios": cliente["totalEnvios"],
                "registros": cliente["registros"],
                "valorEnvio": cliente["valorEnvio"],
                "pontosRetencao": pontos_retencao,
            })

    return render(request, "calculoRetencaoClientes.html", {"data": resultados})

def calculoRankingSemanaAluno_s(request):
    with connection.cursor() as cursor:
        # Inserindo registros na tabela de logs
        cursor.execute("SELECT * FROM alunosPosicoesSemana")
        posicoes = cursor.fetchall()

        for posicao in posicoes:
            aluno = posicao[1] if posicao[1] else "0"  # Assumindo que 'aluno' está na posição correta
            cla = posicao[2] if posicao[2] else "0"    # Assumindo que 'cla' está na posição correta
            semana, posicao, tipo, data, pontos = posicao[3:8]  # Ajuste conforme o esquema real
            
            # Obtendo o campeonato vigente (ajuste conforme necessário)
            cursor.execute("SELECT id FROM campeonatos WHERE vigente = TRUE")
            campeonato_vigente = cursor.fetchone()
            campeonato_id = campeonato_vigente[0] if campeonato_vigente else None
            
            if campeonato_id:
                cursor.execute("""
                    INSERT INTO alunosPosicoesSemanaLogs (aluno, cla, semana, posicao, tipo, data, pontos, campeonato)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [aluno, cla, semana, posicao, tipo, data, pontos, campeonato_id])

        # Atualizar `alunosEnvios` para a semana específica
        semana_subidometro = 1  # Defina essa variável corretamente
        cursor.execute("""
            UPDATE alunosEnvios 
            SET status = 2, statusMotivo = 63 
            WHERE semana = %s AND status < 2
        """, [semana_subidometro])

        # Remover ranking de alunos
        cursor.execute("DELETE FROM alunosPosicoesSemana")

        # Obter alunos e seus respectivos `cla`
        cursor.execute("SELECT id, cla FROM alunos")
        alunos = cursor.fetchall()
    return render(request, "calculoRankingSemanaAluno.html", {})

def calculoRankingSemanaAluno(request):
    campeonato_id = 5
    semana_subidometro_anterior = 10  # Substitua pelo valor correto
    
    with connection.cursor() as cursor:
        query_posicoes_alunos = """
            WITH
                lista AS (
                SELECT
                    alunos."id",
                    (
                    SELECT
                    COALESCE(SUM("pontos"), 0)
                    FROM
                    alunosenvios
                    WHERE
                    alunos."id" = alunosenvios."vinculoAluno"
                    AND alunosenvios."campeonato" = %s
                    AND alunosenvios."status" = 3
                    AND alunosenvios."semana" <> 0 ) AS "totalPontos",
                    (
                    SELECT
                    COALESCE(SUM("pontos"), 0)
                    FROM
                    alunosclientes
                    WHERE
                    alunos."id" = alunosclientes."aluno"
                    AND alunosclientes."campeonato" = %s
                    AND alunosclientes."status" = 1
                    AND alunosclientes."pontos" > 0 ) AS "totalPontosClientes",
                    (
                    SELECT
                    COALESCE(SUM("pontos"), 0)
                    FROM
                    alunosclientespontosmesesretencao
                    WHERE
                    alunos."id" = alunosclientespontosmesesretencao."aluno"
                    AND alunosclientespontosmesesretencao."campeonato" = %s
                    AND alunosclientespontosmesesretencao."pontos" > 0 ) AS "totalPontosClientesRetencao"
                FROM
                    alunos
                INNER JOIN
                    mentoriacla
                ON
                    mentoriacla."id" = alunos."cla"
                WHERE
                    ( alunos."status" IN ('ACTIVE',
                        'APPROVED',
                        'COMPLETE')
                    OR alunos."dataExpiracao" >= CURRENT_DATE
                    OR (alunos."dataExpiracao7Dias" IS NOT NULL
                        AND alunos."dataExpiracao7Dias" >= CURRENT_DATE) )
                    AND alunos."nivel" < 16
                    AND mentoriacla."definido" = 1)
                SELECT
                lista.*,
                (COALESCE(lista."totalPontos", 0) + COALESCE(lista."totalPontosClientes", 0) + COALESCE(lista."totalPontosClientesRetencao", 0)) AS "totalPontosFinal",
                DENSE_RANK() OVER (ORDER BY (COALESCE(lista."totalPontos", 0) + COALESCE(lista."totalPontosClientes", 0) + COALESCE(lista."totalPontosClientesRetencao", 0)) DESC) AS "rank"
                FROM
                lista
                ORDER BY
                "rank" ASC;
        """
        cursor.execute(query_posicoes_alunos, [campeonato_id, campeonato_id, campeonato_id])
        posicoes_alunos = cursor.fetchall()

    # Inserção no banco de dados
    for contador, posicao in enumerate(posicoes_alunos, start=1):
        aluno_id = posicao[0]  # Substitua pelos índices corretos da consulta
        total_pontos_final = posicao[-2]
        rank = posicao[-1]

        # # Inserção em alunosPosicoesSemana
        # AlunoPosicaoSemana.objects.create(
        #     aluno_id=aluno_id,
        #     cla_id=0,  # Substitua pelo cla correto se necessário
        #     semana=semana_subidometro_anterior,
        #     posicao=rank,
        #     tipo=1,
        #     data=date.today(),
        #     pontos=total_pontos_final,
        # )

    # Atualização de posições para tipo 2
    tipo_2_posicoes = AlunoPosicaoSemana.objects.filter(tipo=2).order_by('pontos')
    for rank, posicao in enumerate(tipo_2_posicoes, start=1):
        print(posicao)
        # posicao.posicao = rank
        # posicao.save()

    # Soma de pontos para cla
    # pontos_cla_arr = {}
    # tipo_1_posicoes = AlunoPosicaoSemana.objects.filter(tipo=1)
    # for row in tipo_1_posicoes:
    #     pontos_cla_arr.setdefault(row.cla_id, []).append(row.pontos)

    # for cla_id, pontos in pontos_cla_arr.items():
    #     if cla_id > 0:
    #         soma_pontos = sum(pontos)
    #         print(cla_id, soma_pontos)
            # AlunoPosicaoSemana.objects.create(
            #     aluno_id=0,
            #     cla_id=cla_id,
            #     semana=semana_subidometro_anterior,
            #     posicao=0,
            #     tipo=2,
            #     data=date.today(),
            #     pontos=soma_pontos,
            # )

    # Atualização de posições novamente
    tipo_2_posicoes = AlunoPosicaoSemana.objects.filter(tipo=2).order_by('pontos')
    for rank, posicao in enumerate(tipo_2_posicoes, start=1):
        print(posicao)
        # posicao.posicao = rank
        # posicao.save()

    
    # Preparando o resultado final
    resultados = []
    for posicao in posicoes_alunos:
        aluno_id = posicao[0]
        total_pontos_final = posicao[-2]
        rank = posicao[-1]

        # Obtendo os detalhes do aluno com base no aluno_id
        aluno = Aluno.objects.get(id=aluno_id)
        
        resultados.append({
            "idAluno": aluno.id,
            "nomeCompleto": aluno.nomeCompleto,
            "apelido": aluno.apelido,
            "email": aluno.email,
            "totalPontosFinal": total_pontos_final,
            "rank": rank
        })

    return render(request, "calculoRankingSemanaAluno.html", {"data": resultados})  

