<?
require_once($_SERVER['DOCUMENT_ROOT']."/configCamp3.php");


if($_GET['tipo'] == "atualizaPontosLimitesMesesEnvios"){
	$lista = $con->selectList("
	SELECT
		alunosEnvios.vinculoAluno AS idAluno,
        alunos.nomeCompleto,
        alunos.email,
		DATE_FORMAT(alunosEnvios.data, '%Y-%m') AS mesAno,
		COUNT(*) AS totalEnvios,
		SUM(alunosEnvios.valor) AS totalFaturamento,
		SUM(alunosEnvios.pontos) AS totalPontos,
		SUM(alunosEnvios.pontosPreenchidos) AS totalPontosPreenchidos,
		alunosEnvios.data AS data,
		MAX(alunosEnvios.data) AS ultimaDataEnvio,
			GROUP_CONCAT(alunosEnvios.id) AS idsEnvios,
			GROUP_CONCAT(alunosEnvios.id, '|', alunosEnvios.pontos) AS idsEnviosComPontos
	FROM
		alunosEnvios
			INNER JOIN alunos ON alunos.id = alunosEnvios.vinculoAluno
	WHERE
		alunosEnvios.tipo = 2
		AND alunosEnvios.`status` = 3
		AND alunosEnvios.semana > 0
		AND alunosEnvios.`data` >= '2024-09-01'
	GROUP BY
		alunosEnvios.vinculoAluno, mesAno
	HAVING
    	totalPontos > 3000
	ORDER BY
		alunosEnvios.vinculoAluno ASC, mesAno ASC,totalPontos DESC
	");
	//dump($lista);
	foreach($lista as $row){
		$ultrapassouPontos = 0;
		$enviosPontosArr = array();
		
		if( $row['totalPontos'] > 3000 ){
			$ultrapassouPontos = 1;			
			echo "PASSOU DE 3000<br>";
			echo "PASSOU DE 3000<br>";
			echo "TOTAL DE FATURAMENTO: R$ ".number_format($row['totalFaturamento'], 2, ',', '.')."<br>";
			echo "TOTAL DE ENVIOS: ".$row['totalEnvios']."<br>";
			echo "TOTAL DE PONTOS PREENCHIDOS: ".$row['totalPontosPreenchidos']."<br>";
			echo "TOTAL DE PONTOS: ".$row['totalPontos']."<br>";
			$enviosPontosArr = explode(",", $row['idsEnviosComPontos']);
			
			if( $row['totalPontosPreenchidos'] > $row['totalPontos'] ){}
			
			echo "SEM AJUSTE DE BALANÇO NOS PONTOS<br>";
			dump($enviosPontosArr);
			echo "<br>";
			
			$limite = 3000;
			$total = 0;
			$ajustado = array();
			$pontosSomaArr = array();
			$zerados = array(); // Array para armazenar os ids que serão zerados

			foreach ($enviosPontosArr as $item) {
				list($idEnvio, $pontosEnvio) = explode('|', $item);
				$pontosEnvio = (int)$pontosEnvio;

				if ($total + $pontosEnvio > $limite) {
					// Ajustar o último valor para não ultrapassar o limite
					$pontosRestantes = $limite - $total;
					$ajustado[] = "$idEnvio|$pontosRestantes";
					$pontosSomaArr[] = $pontosRestantes;
					$total += $pontosRestantes;

					// Todos os envios restantes serão zerados
					// Itera os envios restantes e coloca no array de zerados
					$indexAtual = array_search($item, $enviosPontosArr);
					for ($i = $indexAtual + 1; $i < count($enviosPontosArr); $i++) {
						list($idRestante, ) = explode('|', $enviosPontosArr[$i]);
						$zerados[] = "$idRestante|0";
					}
					break; // Parar o loop pois atingiu o limite
				} else {
					$ajustado[] = "$idEnvio|$pontosEnvio";
					$pontosSomaArr[] = $pontosEnvio;
					$total += $pontosEnvio;
				}
			}
			echo "SOMA DO BALANÇO DE PONTOS: ".array_sum($pontosSomaArr)."<br>";
			
			echo "<br><br><br>";
				
			echo "COM AJUSTE DE BALANÇO NOS PONTOS<br>";
			dump($ajustado);

			
			echo "<br>AJUSTE DE PONTOS:<br>";
			if( count($ajustado) > 0){
				foreach($ajustado as $rowAjustado){
					$rowAjustadoArr = explode("|", $rowAjustado);
					$sql = "UPDATE alunosEnvios SET pontos = '".$rowAjustadoArr[1]."' WHERE id = ".$rowAjustadoArr[0];
					echo $sql."<br>";
					//$con->query($sql);
					if($_GET['processarUpdate'] == 1){
						
					}
				}
			}

			
			echo "<br>ZERADOS<br>";
			dump($zerados);
			
			echo "<br>ZERAR PONTOS:<br>";
			if( count($zerados) > 0){
				foreach($zerados as $rowAjustado){
					$rowAjustadoArr = explode("|", $rowAjustado);
					$sql = "UPDATE alunosEnvios SET pontos = '".$rowAjustadoArr[1]."' WHERE id = ".$rowAjustadoArr[0];
					echo $sql."<br>";
					//$con->query($sql);
					if($_GET['processarUpdate'] == 1){
						
					}
				}
			}			
			
		}else{
			echo "ESTÁ OK DENTRO DO MÊS<br>";
		}
		
		echo "<br>";
		echo "<hr>";
	}
	
	if($_GET['processarUpdate'] == 1){
		//ENVIA E-MAIL E DEPOIS MOSTRA A DIV
		$assunto = "Cron Semanal | Balanceamento de Pontos - Subido PRO";
		$nomeDestinatario = "Produção Inventandus";
		$emailDestinatario = 'producao@inventandus.com.br';

		$multiplosDestinatarios[] = array( 'nome' => 'Flavio Mattos', 'email' => 'flavio.mattos@grupopermaneo.com.br' );
		$multiplosDestinatarios[] = array( 'nome' => 'Mariana Campos', 'email' => 'mariana.campos@grupopermaneo.com.br' );

		$emailResposta = $emailSuporte; $nomeResposta = 'Subido PRO';
		$message = my_file_get_contents("https://subidopro.com.br/painel3.0/aluno/emails/cronSemanalBalanceamento.php");
		if(is_array($arrMensagemEmail)){
			$mensagemArrStr = implode("<br>", $arrMensagemEmail);
		}else{
			$mensagemArrStr = "";
		}
		$message = str_replace("[DADOSPERSONALIZADOS]", $mensagemArrStr, $message );
		include($_SERVER["DOCUMENT_ROOT"]."/config/configPhpmailer.php");	
		//ENVIA E-MAIL E DEPOIS MOSTRA A DIV
	}
	exit;
}


if($_GET['tipo'] == "calculoRetencaoClientes"){

	function geraPontosClientes($valor){
		if ($valor >= 0 && $valor < 1000) {
			return "60";
		} elseif ($valor >= 1000 && $valor < 3000) {
			return "480";
		} elseif ($valor >= 3000 && $valor < 5000) {
			return "1080";
		} elseif ($valor >= 5000 && $valor < 9000) {
			return "1920";
		} elseif ($valor >= 9000) {
			return "2460";
		} else {
			return "0";
		}
	}
	
	function geraPontosRetencao($pontos){
		switch ($pontos) {
			case 60: $pontosFinal = "40"; break;
			case 480: $pontosFinal = "320"; break;
			case 1080: $pontosFinal = "720"; break;
			case 1920: $pontosFinal = "1280"; break;
			case 2460: $pontosFinal = "1640"; break;
		}
		return $pontosFinal;
	}
	
	$sql = "
	SELECT
		alunosClientes.id AS idCliente,
		alunosClientesContratos.id AS idContrato,
		alunosClientesContratos.valorContrato AS valorContrato,
		alunosClientesContratos.tipoContrato AS tipoContrato,
		alunosClientesContratos.porcentagemContrato AS porcentagemContrato,
		alunosClientesContratos.dataVencimento AS dataVencimentoContrato,
		alunosEnvios.valor AS valorEnvio,
		alunosClientes.aluno AS idAluno,
		alunosClientes.pontos AS pontosCliente,
		COUNT(DISTINCT DATE_FORMAT(alunosEnvios.data, '%Y-%m')) AS totalEnvios,
		GROUP_CONCAT(alunosEnvios.id,'|',alunosEnvios.valor,'|',alunosEnvios.pontos,'|',alunosEnvios.data) AS registros
	FROM
		alunosClientes
		INNER JOIN alunosEnvios ON alunosEnvios.vinculoCliente = alunosClientes.id
		INNER JOIN (
			SELECT cliente, MAX(dataContrato) AS dataContrato
			FROM alunosClientesContratos
			WHERE status = 1
			GROUP BY cliente
		) AS contratoRecente ON contratoRecente.cliente = alunosClientes.id
		INNER JOIN alunosClientesContratos ON 
			alunosClientesContratos.cliente = contratoRecente.cliente
			AND alunosClientesContratos.dataContrato = contratoRecente.dataContrato
	WHERE alunosEnvios.status = 3 AND alunosEnvios.tipo = 2 AND alunosClientes.status = 1 AND alunosEnvios.data BETWEEN '2024-09-01' AND '".date("Y-m-d")."'  AND alunosClientesContratos.status = 1 AND alunosEnvios.semana > 0
	GROUP BY
		alunosClientes.id
	HAVING
    	totalEnvios > 1
	ORDER BY
		totalEnvios DESC;
	"; //alunosClientesContratos.dataVencimento >= '".date("Y-m-01")."' //AND (alunosClientesContratos.dataVencimento IS NULL OR alunosClientesContratos.dataVencimento = '' )
	//echo $sql."<br><br><br>";
		
		
	$listaClientesRecebimentos = $con->selectList($sql);
	$contadorClientes = 1;
	foreach( $listaClientesRecebimentos as $cliente ){
		if($cliente['totalEnvios']>0){
			echo "CONTADOR ".$contadorClientes."<br>";
			
			if($cliente['tipoContrato']==2 && $cliente['porcentagemContrato']>0){
				$valorInicial = $cliente['valorEnvio'];
				$porcentagem = $cliente['porcentagemContrato'];

				$valorFinal = $valorInicial - ($valorInicial * ($porcentagem / 100));
				$valorComissao = $valorInicial - $valorFinal;

				$cliente['valorEnvio'] = number_format($valorComissao, 2, '.', '');
				$pontosCliente = geraPontosClientes($cliente['valorEnvio']);
				$cliente['pontosCliente'] = $pontosCliente;
			}else{
				if( $cliente['valorContrato']=="" ){
					$pontosCliente = geraPontosClientes($cliente['valorEnvio']);	
				}else{
					$pontosCliente = geraPontosClientes($cliente['valorContrato']);
				}
				$cliente['pontosCliente'] = $pontosCliente;				
			}
			
			
			echo "CLIENTE ".$cliente['idCliente']."<br>";
			echo "CONTRATO ".$cliente['idContrato']."<br>";
			echo "VENCIMENTO CONTRATO ".$cliente['dataVencimentoContrato']."<br>";
			echo "PONTOS GERADOS ".$pontosCliente."<br>";
			echo "PONTOS CADASTRADOS ".$cliente['pontosCliente']."<br>";
			echo "ENVIOS ".$cliente['totalEnvios']."<br>";
			echo "REGISTROS ".$cliente['registros']."<br>";
			echo "VALOR ENVIO ".$cliente['valorEnvio']."<br>";
			
			if( $cliente['pontosCliente'] == "" || $cliente['pontosCliente'] == 0 ){
				$cliente['pontosCliente'] = $pontosCliente;
			}
			
			
			$pontosRetencao = 0;
			$pontosRetencao = geraPontosRetencao($cliente['pontosCliente']);
			
			$pontosSoma = 0;
			
			/*
			$pontosSoma = $pontosRetencao*($cliente['totalEnvios']-1);	
			$buscaClienteRetencao = $con->selectRow("SELECT id FROM alunosClientesPontosMesesRetencao WHERE cliente = ".$cliente['idCliente']);
			if( $buscaClienteRetencao['totalRow'] == 0 ){
				$sql = "INSERT INTO alunosClientesPontosMesesRetencao (aluno,cliente,campeonato,data,pontos,qtdEnvios,idsEnvios) VALUES( '".$cliente['idAluno']."', '".$cliente['idCliente']."', '".$campeonatoVigente['id']."', '".date("Y-m-d H:i:s")."', '".$pontosSoma."', '".$cliente['totalEnvios']."', '".$cliente['registros']."' )";
			}else{
				$sql = "UPDATE alunosClientesPontosMesesRetencao SET pontos = '".$pontosSoma."', qtdEnvios = '".$cliente['totalEnvios']."', data = '".date("Y-m-d H:i:s")."', campeonato = '".$campeonatoVigente['id']."', idsEnvios = '".$cliente['registros']."' WHERE id = ".$buscaClienteRetencao['id'];
			}			
			*/
			
			$pontosSoma = $pontosRetencao;

			
			$buscaClienteRetencao = $con->selectRow("SELECT id FROM alunosClientesPontosMesesRetencao WHERE cliente = ".$cliente['idCliente']);
			if( $buscaClienteRetencao['totalRow'] < ($cliente['totalEnvios']-1) ){
				
				$sql = "INSERT INTO alunosClientesPontosMesesRetencao (aluno,cliente,campeonato,data,pontos,qtdEnvios,idsEnvios,semana) VALUES( '".$cliente['idAluno']."', '".$cliente['idCliente']."', '".$campeonatoVigente['id']."', '".date("Y-m-d H:i:s")."', '".$pontosSoma."', '".$cliente['totalEnvios']."', '".$cliente['registros']."', '".$campeonatoVigente["semanaVigente"]."' )";
				
				$arrMensagemEmail[] = $sql." <br><br>";

				echo $sql."<br>";
				$con->query($sql); 
				
			}
			
			$contadorClientes++;
		}
		echo "<hr>";
	}
	
    //ENVIA E-MAIL E DEPOIS MOSTRA A DIV
    $assunto = "Cron Semanal | Pontos de Retenção - Subido PRO";
    $nomeDestinatario = "Produção Inventandus";
    $emailDestinatario = 'producao@inventandus.com.br';
	
    $multiplosDestinatarios[] = array( 'nome' => 'Flavio Mattos', 'email' => 'flavio.mattos@grupopermaneo.com.br' );
    $multiplosDestinatarios[] = array( 'nome' => 'Mariana Campos', 'email' => 'mariana.campos@grupopermaneo.com.br' );

    $emailResposta = $emailSuporte; $nomeResposta = 'Subido PRO';
    $message = my_file_get_contents("https://subidopro.com.br/painel3.0/aluno/emails/cronSemanalRetencao.php");
	if($message==""){ $message = " "; }
	if(is_array($arrMensagemEmail)){
		$mensagemArrStr = implode("<br>", $arrMensagemEmail);
	}else{
		$mensagemArrStr = "";
	}
	$message = str_replace("[DADOSPERSONALIZADOS]", $mensagemArrStr, $message );
    include($_SERVER["DOCUMENT_ROOT"]."/config/configPhpmailer.php");	
    //ENVIA E-MAIL E DEPOIS MOSTRA A DIV
	
	exit;	
}


if($_GET['calculoRankingSemanaAluno']==1){    
    //PASSA POR TODOS OS REGISTROS E ADICIONA NA TABELA DE LOGS
    foreach( $con->selectList(" SELECT * FROM  alunosPosicoesSemana") as $itemRow ){
        if($itemRow['aluno']==""){ $itemRow['aluno']="0"; }
        if($itemRow['cla']==""){ $itemRow['cla']="0"; }
        
        $sql="INSERT INTO alunosPosicoesSemanaLogs(aluno, cla, semana, posicao, tipo, data, pontos, campeonato) VALUES ('".$itemRow['aluno']."', '".$itemRow['cla']."', '".$itemRow['semana']."', '".$itemRow['posicao']."', '".$itemRow['tipo']."', '".$itemRow['data']."', '".$itemRow['pontos']."', '".$campeonatoVigente["id"]."' )";
        $con->query($sql);
    }
    //PASSA POR TODOS OS REGISTROS E ADICIONA NA TABELA DE LOGS
    
    
	$con->query("UPDATE alunosEnvios SET status = '2', statusMotivo = '63' WHERE semana = $semanaSubidometro AND status < 2"); //".$campeonatoVigente["semanaVigente"]."    
	$con->query("DELETE FROM alunosPosicoesSemana"); //REMOVE RANKING DE ALUNOS	
	$alunos = $con->selectList("SELECT alunos.id, alunos.cla FROM alunos");	
    

	$posicoesAlunos = $con->selectList("
    SELECT 
        lista.*, 
        (COALESCE(lista.totalPontos, 0) + COALESCE(lista.totalPontosClientes, 0) + COALESCE(lista.totalPontosClientesRetencao, 0) ) AS totalPontosFinal,
        DENSE_RANK() OVER (ORDER BY ( COALESCE(lista.totalPontos, 0) + COALESCE(lista.totalPontosClientes, 0) + COALESCE(lista.totalPontosClientesRetencao, 0) ) DESC) AS rank 
    FROM (
        SELECT 
            alunos.id,
            alunos.status AS statusAluno,
            alunos.dataExpiracao AS dataExpiracaoAluno,
            (SELECT SUM(pontos) AS totalPontos FROM alunosEnvios WHERE alunos.id = alunosEnvios.vinculoAluno AND alunosEnvios.campeonato = ".$campeonatoVigente["id"]." AND alunosEnvios.status = 3 AND alunosEnvios.semana <> 0) AS totalPontos, 
            (SELECT SUM(alunosClientes.pontos) AS totalPontosClientes FROM alunosClientes WHERE alunos.id = alunosClientes.aluno AND alunosClientes.campeonato = ".$campeonatoVigente["id"]." AND alunosClientes.status = 1 AND alunosClientes.pontos > 0) AS totalPontosClientes,
			(SELECT SUM(alunosClientesPontosMesesRetencao.pontos) AS totalPontosClientesRetencao FROM alunosClientesPontosMesesRetencao WHERE alunos.id = alunosClientesPontosMesesRetencao.aluno AND alunosClientesPontosMesesRetencao.campeonato = ".$campeonatoVigente["id"]." AND alunosClientesPontosMesesRetencao.pontos > 0) AS totalPontosClientesRetencao
        FROM alunos WHERE alunos.nivel < 16 AND mentoriaCla.definido = 1
		INNER JOIN mentoriaCla ON mentoriaCla.id = alunos.cla
    ) AS lista 
    ORDER BY rank ASC
	"); //WHERE ( alunos.status = 'ACTIVE' OR alunos.status = 'APPROVED' OR alunos.status = 'COMPLETE' OR alunos.dataExpiracao >= '".date("Y-m-d H:i:s")."' )
    //AND alunosClientes.semPontuacao != 1 AND alunosClientes.clienteAntesSubidoPro != 1
    
	
	$contador=1;
	foreach($posicoesAlunos as $posicao){
		$aluno = $alunos[$posicao['id']];
		if( $aluno['cla'] == "" ){ $aluno['cla'] = "0"; }
		if($posicao['totalPontosFinal']==""){ $posicao['totalPontosFinal'] = 0; }
		echo "#".$contador." Aluno ".$aluno['id']." | Pontos ".$posicao['totalPontosFinal']."<br>";
		
		$sql="INSERT INTO alunosPosicoesSemana(aluno, cla, semana, posicao, tipo, data, pontos, campeonato) VALUES ('".$posicao['id']."','".$aluno['cla']."','".$semanaSubidometroAnterior."','".$posicao['rank']."','1','".date("Y-m-d H:i:s")."','".$posicao['totalPontosFinal']."','".$campeonatoVigente["id"]."')";
		echo $sql."<br>";
		$con->query($sql);
		
        $sql="INSERT INTO alunosPosicoesSemanaGeral(aluno, cla, semana, posicao, tipo, data, pontos, campeonato, statusAluno) VALUES ('".$posicao['id']."','".$aluno['cla']."','".$semanaSubidometroAnterior."','".$posicao['rank']."','1','".date("Y-m-d H:i:s")."','".$posicao['totalPontosFinal']."','".$campeonatoVigente["id"]."','".$posicao['statusAluno']."|".$posicao['dataExpiracaoAluno']."')";
		$con->query($sql);
		$contador++;
	}
	echo "<hr>";
	$posicoesAlunosNova = $con->selectList("SELECT * FROM alunosPosicoesSemana WHERE tipo = 1");
	foreach($posicoesAlunosNova as $subidometroRow){
		$pontosClaArr[$subidometroRow['cla']]['pontos'][] = $subidometroRow['pontos'];
	}

	foreach($pontosClaArr as $idCla => $pontosClaRow){
		if($idCla>0){
			$sqlCla="INSERT INTO alunosPosicoesSemana(aluno, cla, semana, posicao, tipo, data, pontos, campeonato) VALUES ('0','".$idCla."','".$semanaSubidometroAnterior."','0','2','".date("Y-m-d H:i:s")."','".array_sum($pontosClaRow['pontos'])."', '".$campeonatoVigente["id"]."')";
			echo $sqlCla."<br>";
			$con->query($sqlCla);
            
            
            $sqlCla="INSERT INTO alunosPosicoesSemanaGeral(aluno, cla, semana, posicao, tipo, data, pontos, campeonato) VALUES ('0','".$idCla."','".$semanaSubidometroAnterior."','0','2','".date("Y-m-d H:i:s")."','".array_sum($pontosClaRow['pontos'])."', '".$campeonatoVigente["id"]."')";
            $con->query($sqlCla);
		}
	}
	
	$posicoesAlunosNova = $con->selectList("SELECT *, RANK() OVER ( ORDER BY pontos DESC ) AS rank FROM alunosPosicoesSemana WHERE tipo = 2 ORDER BY rank ASC");
	foreach($posicoesAlunosNova as $posicao){
		$con->query("UPDATE alunosPosicoesSemana SET posicao = '".$posicao['rank']."' WHERE id = ".$posicao['id']);
	}
	
	
	$con->query("DELETE FROM alunosPosicoesSemana WHERE tipo = 1"); //REMOVE RANKING DE ALUNOS
	
	$posicoesAlunos = $con->selectList("
    SELECT 
        lista.*, 
        (COALESCE(lista.totalPontos, 0) + COALESCE(lista.totalPontosClientes, 0) + COALESCE(lista.totalPontosClientesRetencao, 0) ) AS totalPontosFinal,
        DENSE_RANK() OVER (ORDER BY (COALESCE(lista.totalPontos, 0) + COALESCE(lista.totalPontosClientes, 0) + COALESCE(lista.totalPontosClientesRetencao, 0) ) DESC) AS rank 
    FROM (
        SELECT 
            alunos.id, 
            (SELECT SUM(pontos) AS totalPontos FROM alunosEnvios WHERE alunos.id = alunosEnvios.vinculoAluno AND alunosEnvios.campeonato = ".$campeonatoVigente["id"]." AND alunosEnvios.status = 3 AND alunosEnvios.semana <> 0) AS totalPontos, 
			
            (SELECT SUM(alunosClientes.pontos) AS totalPontosClientes FROM alunosClientes WHERE alunos.id = alunosClientes.aluno AND alunosClientes.campeonato = ".$campeonatoVigente["id"]." AND alunosClientes.status = 1 AND alunosClientes.pontos > 0) AS totalPontosClientes,
			
			(SELECT SUM(alunosClientesPontosMesesRetencao.pontos) AS totalPontosClientesRetencao FROM alunosClientesPontosMesesRetencao WHERE alunos.id = alunosClientesPontosMesesRetencao.aluno AND alunosClientesPontosMesesRetencao.campeonato = ".$campeonatoVigente["id"]." AND alunosClientesPontosMesesRetencao.pontos > 0) AS totalPontosClientesRetencao
			
        FROM alunos
		INNER JOIN mentoriaCla ON mentoriaCla.id = alunos.cla
        WHERE ( alunos.status = 'ACTIVE' OR alunos.status = 'APPROVED' OR alunos.status = 'COMPLETE' OR alunos.dataExpiracao >= '".date("Y-m-d")."' OR (alunos.dataExpiracao7Dias!= '' AND alunos.dataExpiracao7Dias >= '".date("Y-m-d")."') ) AND alunos.nivel < 16 AND mentoriaCla.definido = 1
    ) AS lista 
    ORDER BY rank ASC
	"); //WHERE ( alunos.status = 'ACTIVE' OR alunos.status = 'APPROVED' OR alunos.status = 'COMPLETE' OR alunos.dataExpiracao >= '".date("Y-m-d H:i:s")."' )
    // AND alunosClientes.semPontuacao != 1
    
	$alunos = $con->selectList("SELECT alunos.id, alunos.cla FROM alunos");	
	
	$contador=1;
	foreach($posicoesAlunos as $posicao){
		$aluno = $alunos[$posicao['id']];
		if( $aluno['cla'] == "" ){ $aluno['cla'] = "0"; }
		if($posicao['totalPontosFinal']==""){ $posicao['totalPontosFinal'] = 0; }
		echo "#".$contador." Aluno ".$aluno['id']." | Pontos ".$posicao['totalPontosFinal']."<br>";
		
		$sql="INSERT INTO alunosPosicoesSemana(aluno, cla, semana, posicao, tipo, data, pontos) VALUES ('".$posicao['id']."','".$aluno['cla']."','".$semanaSubidometroAnterior."','".$posicao['rank']."','1','".date("Y-m-d H:i:s")."','".$posicao['totalPontosFinal']."')";
		echo $sql."<br>";
		$con->query($sql);
		$contador++;
	}
	
	$posicoesAlunosNova = $con->selectList("SELECT *, RANK() OVER ( ORDER BY pontos DESC ) AS rank FROM alunosPosicoesSemana WHERE tipo = 2 ORDER BY rank ASC");
	foreach($posicoesAlunosNova as $posicao){
		$con->query("UPDATE alunosPosicoesSemana SET posicao = '".$posicao['rank']."' WHERE id = ".$posicao['id']);
	}
    
    
    unset($pontosClaArr);
    $pontosClaArr = array();
    $con->query("DELETE FROM alunosPosicoesSemana WHERE tipo = 2");
	$posicoesAlunosNova = $con->selectList("SELECT * FROM alunosPosicoesSemana WHERE tipo = 1");
	foreach($posicoesAlunosNova as $subidometroRow){
		$pontosClaArr[$subidometroRow['cla']]['pontos'][] = $subidometroRow['pontos'];
	}

	foreach($pontosClaArr as $idCla => $pontosClaRow){
		if($idCla>0){
            $somaPontos = '0';
            $pontosCla = $con->selectRow("SELECT SUM(pontos) AS totalPontos FROM mentoriaClaPontos WHERE cla = ".$idCla." AND campeonato = ".$campeonatoVigente["id"]." AND status = 3");
            if($pontosCla['totalRow']>0){
                $somaPontos = $pontosCla['totalPontos'];
            }else{
                $somaPontos = '0';
            }            
            $pontos = array_sum($pontosClaRow['pontos']);
            $pontosCla = $pontos + $somaPontos;
            
			$sqlCla="INSERT INTO alunosPosicoesSemana(aluno, cla, semana, posicao, tipo, data, pontos) VALUES ('0','".$idCla."','".$semanaSubidometroAnterior."','0','2','".date("Y-m-d H:i:s")."','".$pontosCla."')";
			echo $sqlCla."<br>";
			$con->query($sqlCla);
		}
	}
	
    $posicoesAlunosNova = $con->selectList("SELECT *, RANK() OVER ( ORDER BY pontos DESC ) AS rank FROM alunosPosicoesSemana WHERE tipo = 2 ORDER BY rank ASC");
	foreach($posicoesAlunosNova as $posicao){
		$con->query("UPDATE alunosPosicoesSemana SET posicao = '".$posicao['rank']."' WHERE id = ".$posicao['id']);
	}
    
	$alunos = $con->selectList("SELECT * FROM alunos");
	$alunosSubidometro = $con->selectList("SELECT * FROM alunosSubidometro WHERE semana = ".$semanaSubidometro." AND campeonato = ".$campeonatoVigente["id"]." ");	
	foreach($alunosSubidometro as $subidometroRow){
		$alunosSubidometroArr[$subidometroRow['aluno']] = $subidometroRow;	
	}
	
	
	foreach($alunos as $aluno){
		if( $aluno['cla'] == "" ){ $aluno['cla'] = "0"; }
		
		$post = array(
			'tabela'       => "alunosSubidometro",
			'campos'       => array(
				array('campo' => 'aluno', 'valor' => $aluno['id'] ),

				array('campo' => 'campeonato', 'valor' => $campeonatoVigente['id'] ),
				array('campo' => 'semana', 'valor' => $semanaSubidometro ),
				array('campo' => 'cla', 'valor' => $aluno['cla'] ),
			)
		);

		if($alunosSubidometroArr[$aluno['id']]['nivel']>0){
			$post['campos'][] = array('campo' => 'nivel', 'valor' => $alunosSubidometroArr[$aluno['id']]['nivel'] );
		}else{
			$post['campos'][] = array('campo' => 'nivel', 'valor' => $aluno['nivel'] );
		}

		if($alunosSubidometroArr[$aluno['id']]['id'] != ""){
			$post['registro'] = array('campo' => 'id','valor' => $alunosSubidometroArr[$aluno['id']]['id']);
		}else{
			$post['campos'][] = array('campo' => 'data', 'valor' => date("Y-m-d H:i:s") );		
		}
		$registro = $con->inserirBancoFront($post);
	}
	
	
	$alunosSubidometro = $con->selectList("SELECT * FROM alunosSubidometro WHERE semana = ".$semanaSubidometro."  AND campeonato = ".$campeonatoVigente["id"]." ORDER BY pontuacaoGeral DESC");
	foreach($alunosSubidometro as $subidometro){
		$con->query("UPDATE alunos SET nivel = '".$subidometro['nivel']."' WHERE id = ".$subidometro['aluno']);
	}
    
    
    //ENVIA E-MAIL E DEPOIS MOSTRA A DIV
    $assunto = "Cron Semanal | Subidômetro - Subido PRO";
    $nomeDestinatario = "Produção Inventandus";
    $emailDestinatario = 'producao@inventandus.com.br';
	
	$multiplosDestinatarios[] = array( 'nome' => 'Flavio Mattos', 'email' => 'flavio.mattos@grupopermaneo.com.br' );
    $multiplosDestinatarios[] = array( 'nome' => 'Mariana Campos', 'email' => 'mariana.campos@grupopermaneo.com.br' );

    $emailResposta = $emailSuporte; $nomeResposta = 'Subido PRO';
    $message = my_file_get_contents("https://subidopro.com.br/painel3.0/aluno/emails/cronSemanal.php");
    include($_SERVER["DOCUMENT_ROOT"]."/config/configPhpmailer.php");	
    //ENVIA E-MAIL E DEPOIS MOSTRA A DIV
	
	exit;
}//NOVO CÓDIGO PARA TESTES



if($_SESSION[SESSAO_UNICA_ALUNOS]['id']==1){
    $campeonatoVigente = $con->selectRow("SELECT * FROM campeonatos WHERE id = 5");
}else{
    $campeonatoVigente = $con->selectRow("SELECT * FROM campeonatos WHERE id = 5");
}
//CONFIGURAÇÃO PARA ESTABELECER AS DATAS DA SEMANA
/* 
	///////// NUMERO DO DIA NA SEMANA /////////
	0 = DOMINGO 
	1 = SEGUNDA 
	2 = TERCA
	3 = QUARTA
	4 = QUINTA
	5 = SEXTA
	6 = SABADO
	///////// NUMERO DO DIA NA SEMANA /////////
*/
$numeroDiaSemana = date("w");



if($_SESSION[SESSAO_UNICA_ALUNOS]['id']==1 ){
    
    //$dataHojeStr = strtotime(date("Y-m-d")." +6 days"); //COLOCAR MAIS DIAS PARA SIMULAR DATA FUTURA
	$dataHojeStr = strtotime("2025-01-22"); //COLOCAR MAIS DIAS PARA SIMULAR DATA FUTURA
	//$dataHojeStr = strtotime(date("Y-m-d")); //USAR PARA PEGAR HOJE
	//$dataHojeStr = strtotime(date("Y-m-d")); //USAR PARA PEGAR HOJE
}else{
	$dataHojeStr = strtotime(date("Y-m-d")); //USAR PARA PEGAR HOJE
}

//$dataHojeStr = strtotime("2024-08-19"); //COLOCAR MAIS DIAS PARA SIMULAR DATA FUTURA

/*
if($_SESSION[SESSAO_UNICA_ALUNOS]['id']!=1){
    if( date("Y-m-d") >= "2024-03-04" && date("Y-m-d") <= "2024-03-10" ){
        $dataHojeStr = strtotime("2024-03-03");
    }
}*/
$dataHoje = date("Y-m-d",$dataHojeStr);

//$totalSemanas = (date( 'W', strtotime( $campeonatoVigente['dataInicio'] ) ) - date( 'W', strtotime( $campeonatoVigente['dataFim'] ) )-1);
//$totalSemanas = (date( 'W', strtotime( $campeonatoVigente['dataFim'] ) ) - date( 'W', strtotime( $campeonatoVigente['dataInicio'] ) )-1);

$totalSemanas = (date( 'W', strtotime( $campeonatoVigente['dataFim'] ) ) - date( 'W', strtotime( $campeonatoVigente['dataInicio'] ) )-1);
$totalSemanas = str_replace("-","",$totalSemanas);



//CRIA O ARRAY DAS SEMANAS E COLOCA NO CAMPEONATO OS DADOS DA SEMANA
$semanasCampeonatoArr = $semanaVigente = array();
for($semana=0;$semana<$totalSemanas;$semana++){ $periodoData = ""; $segunda = strtotime($campeonatoVigente['dataInicio']." +".$semana." weeks");
											   
	for($dia=0;$dia<7;$dia++){ 
		if($dia==6){ $dia = 0;}else{ $dia = $dia+1;}
		$semanasCampeonatoArr[($semana+1)]["datas"][$dia] = date("Y-m-d",strtotime(date("Y-m-d",$segunda)." +".$dia." days"));
		if($dia==0){$dataInicialAtual = date("Y-m-d",strtotime(date("Y-m-d",$segunda)." +".$dia." days")); }
		if($dia==6){$dataFinalAtual = date("Y-m-d",strtotime(date("Y-m-d",$segunda)." +".$dia." days")); }
		$semanaVigenteArr[date("Y-m-d",strtotime(date("Y-m-d",$segunda)." +".$dia." days"))] = $semana+1;		
	} 
	ksort($semanasCampeonatoArr[($semana+1)]["datas"]);
	$semanasCampeonatoArr[($semana+1)]["periodo"] = formatarPeriodo($dataInicialAtual,$dataFinalAtual);	
}

if( strtotime($dataHoje) < strtotime( $campeonatoVigente['dataInicio'] ) ){ $campeonatoVigente["semanaVigente"] = '0'; }else{ $campeonatoVigente["semanaVigente"] = $semanaVigenteArr[$dataHoje]; }
$campeonatoVigente["totalSemanas"] = $totalSemanas;
$campeonatoVigente["hoje"] = $dataHoje;



SELECT 
lista.*, 
(COALESCE(lista.totalPontosRecebimentos, 0) + COALESCE(lista.totalPontosEnvios, 0) + COALESCE(lista.totalPontosClientes, 0) + COALESCE(lista.totalPontosClientesRetencao, 0) ) AS totalPontosFinal,
DENSE_RANK() OVER (ORDER BY (COALESCE(lista.totalPontosRecebimentos, 0) + COALESCE(lista.totalPontosEnvios, 0) + COALESCE(lista.totalPontosClientes, 0) + COALESCE(lista.totalPontosClientesRetencao, 0) ) DESC) AS rank 
FROM (
SELECT 
	alunos.id, 
	(SELECT SUM(pontos) AS totalPontos FROM alunosEnvios WHERE alunos.id = alunosEnvios.vinculoAluno AND alunosEnvios.campeonato = 5 AND alunosEnvios.status = 3 AND alunosEnvios.semana <> 0 AND alunosEnvios.tipo = 2 AND alunosEnvios.data >= '2024-09-01') AS totalPontosRecebimentos,
				
	(SELECT SUM(pontos) AS totalPontos FROM alunosEnvios WHERE alunos.id = alunosEnvios.vinculoAluno AND alunosEnvios.campeonato = 5 AND alunosEnvios.status = 3 AND alunosEnvios.semana <> 0 AND alunosEnvios.tipo != 2) AS totalPontosEnvios, 
				
	(SELECT SUM(alunosClientes.pontos) AS totalPontosClientes FROM alunosClientes WHERE alunos.id = alunosClientes.aluno AND alunosClientes.campeonato = 5 AND alunosClientes.status = 1 AND alunosClientes.pontos > 0) AS totalPontosClientes,
				
	(SELECT SUM(alunosClientesPontosMesesRetencao.pontos) AS totalPontosClientesRetencao FROM alunosClientesPontosMesesRetencao WHERE alunos.id = alunosClientesPontosMesesRetencao.aluno AND alunosClientesPontosMesesRetencao.campeonato = 5 AND alunosClientesPontosMesesRetencao.pontos > 0) AS totalPontosClientesRetencao
	
FROM alunos
INNER JOIN `mentoriaCla_camp5-2025-03-06` ON `mentoriaCla_camp5-2025-03-06`.id = alunos.claAnterior
WHERE ( alunos.status = 'ACTIVE' OR alunos.status = 'APPROVED' OR alunos.status = 'COMPLETE' OR alunos.dataExpiracao >= '2025-03-01' OR (alunos.dataExpiracao7Dias!= '' AND alunos.dataExpiracao7Dias >= '2025-03-01') ) AND alunos.nivel < 16 AND `mentoriaCla_camp5-2025-03-06`.definido = 1
) AS lista 
ORDER BY rank ASC