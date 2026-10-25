# Avaliação do modelo

Nesta pasta, reuni os registros usados para conferir as regras do modelo, comparar sua execução em sessões distintas e examinar os resultados de uma amostra manual. A avaliação considera o experimento com validade e consumo sintéticos, por isso a concordância encontrada se refere aos cálculos e às premissas adotadas.

## Registros preservados

| Arquivo ou pasta | Finalidade |
| --- | --- |
| [validacao_manual](validacao_manual/) | Conferência preenchida em 21/10/2026, com 50 valores manuais |
| [conferencia_apoio.xlsx](conferencia_apoio.xlsx) | Planilha de apoio da amostra anterior, com 263 campos comparados |
| [amostra_registrada.json](amostra_registrada.json) | Critérios e identificação da amostra anterior |
| [esperados_planilha.json](esperados_planilha.json) e [esperados_planilha.sha256](esperados_planilha.sha256) | Valores de referência preservados para os 263 campos |
| [entradas](entradas/) | Estoque preparado e histórico sintético utilizados nas contas |
| [evidencias_locais](evidencias_locais/) | Cenários, invariantes, sensibilidade e comparações locais |
| [conferencia_colab](conferencia_colab/) | Comparação da exportação identificada como proveniente do Colab |
| [conferir_exportacao.py](conferir_exportacao.py) | Comparação de uma exportação com os 263 valores de referência |

## Resultados registrados

Os registros locais apresentam oito de oito cenários controlados conformes, dez de dez casos de borda conformes e 17 de 17 invariantes atendidos. As nove tabelas coincidiram entre duas sessões locais distintas e entre o notebook e o núcleo utilizado pelo Streamlit.

O arquivo [conferencia_colab/conferencia.json](conferencia_colab/conferencia.json) registra concordância nos 263 campos, sem divergências, e a reprodução das nove tabelas em sessões distintas. A identificação do ambiente foi informada na chamada do script por `--ambiente colab`; esse parâmetro não detecta onde o notebook foi executado. O registro é mantido como evidência da comparação realizada, separado da conferência manual posterior.

## Conferência manual de 21/10/2026

Registrei a conferência dos dados de entrada, do diagnóstico de oito lotes dos medicamentos 33 e 104 e do plano completo de um medicamento, com três movimentos. A análise dos destinos considerou as 17 unidades do recorte. O arquivo utilizado foi identificado como `Resultados_Modelo_Final.zip`, obtido em 21/10/2026.

As planilhas estão em [validacao_manual](validacao_manual/). O arquivo original foi preservado, junto de uma cópia com a tolerância decimal de 0,00000001 restaurada e as fórmulas recalculadas. Os 50 valores preenchidos permaneceram iguais nas duas versões. A tolerância zero do arquivo original provocava sete alertas por diferenças decimais; com a tolerância prevista, as 39 linhas do quadro de comparação apresentaram concordância. As outras 11 médias mensais completam os 50 valores conferidos.

A preparação da planilha contou com auxílio de assistente e acesso prévio ao código e às saídas. A revisão dos valores foi registrada por mim, mas nem todas as contas intermediárias foram preservadas. A conferência documenta a concordância da amostra, sem constituir avaliação cega ou revisão independente. A identificação da exportação se limita ao nome e à data informados, pois o hash do ZIP originalmente baixado não foi obtido.

## Amostra anterior de 263 campos

A planilha `conferencia_apoio.xlsx` utiliza `estoque_preparado.csv` e `historico_sintetico.csv`, preservados em `entradas/`. A amostra reúne oito combinações escolhidas por características das entradas, como vários lotes, empate de validade, prazo curto, consumo zero e ausência de estoque. Foram incluídos os 19 lotes dessas combinações, os 16 destinos possíveis para o lote 2183 e o plano completo do medicamento 66.

Os critérios constam em `amostra_registrada.json`. As referências foram calculadas e preservadas em `esperados_planilha.json` antes da comparação específica, com SHA-256 registrado em arquivo separado. Essa ordem preserva a referência utilizada na comparação, mas não caracteriza independência, pois a preparação ocorreu com conhecimento do notebook.

A tolerância de 0,00000001 se aplica apenas aos resultados decimais. IDs, quantidades inteiras e a sequência relativa ao medicamento 66 exigem igualdade exata. Os IDs gerados para lotes recebidos e a numeração global dos movimentos ficaram fora do recorte. O plano dessa amostra contém um movimento, enquanto a disputa entre várias origens é tratada pelo caso de borda B7.

A indicação de revisão humana pendente nos arquivos históricos se refere a essa amostra de 263 campos. A conferência de 21/10 foi registrada em outra planilha, com outro recorte, por isso seus 50 valores não são somados aos 263 campos. Mantive os arquivos históricos com seus resultados e estados originais.

## Reprodução e comparação da exportação

A seção 24.6 do notebook compara arquivos, parâmetros, versões de bibliotecas e o conteúdo das nove tabelas. A primeira execução grava `referencia_reprodutibilidade.json`; uma segunda execução, em nova sessão do mesmo ambiente e com as mesmas entradas, permite verificar a condição `SESSAO_DISTINTA` e a concordância das nove tabelas. `MESMA_SESSAO` não comprova a reprodução em outra sessão, e `CONTEXTO_DIFERENTE` identifica mudanças no contexto comparado.

A exportação ocorre na última célula do notebook, com `BAIXAR_RESULTADOS = True`. O script abaixo compara o ZIP com as referências da amostra de 263 campos, a partir da pasta `avaliacao`:

```cmd
python conferir_exportacao.py Resultados_Modelo_Final.zip --ambiente colab --saida conferencia_nova
```

A pasta de saída diferente preserva o registro existente em `conferencia_colab`. O script usa bibliotecas da instalação padrão do Python, exige as mesmas entradas e compara a exportação com os valores preservados. Ele não executa o modelo nem preenche a revisão manual dos 50 valores. Uma nova comparação precisa manter a identificação de sua própria execução, sem substituir silenciosamente os registros anteriores.

## Sensibilidade e tempo de execução

A variante que admite apenas destinos com registro original do item gerou 1.045 movimentos e 783 lotes com sugestão, contra 1.076 movimentos e 797 lotes no cenário principal. O plano foi recalculado por completo, pois a restrição modifica a disputa pela capacidade. A diferença de 31 movimentos não equivale à exclusão direta dos 141 movimentos do cenário principal destinados a unidades sem registro daquele item.

A seção 24.8 do notebook registra a medição local de 22/10/2026 para a função `construir_plano`: três execuções de 1,886009947, 1,873988872 e 1,655624938 segundo, com mediana de 1,873988872 segundo. O registro descreve o ambiente e os limites da medição. Esses tempos se referem à construção do plano em contêiner Linux, sem representar o tempo total do notebook ou uma medição no Colab. O tempo de aproximadamente 74,9 segundos presente no registro local anterior corresponde ao conjunto daquela verificação, com escopo diferente.

## Limites e versão

As amostras são intencionais e não permitem generalização estatística. Os testes conferem a implementação das regras, enquanto a validade e o consumo continuam sintéticos. As sugestões não demonstram redução real de perdas nem comprovam a viabilidade operacional de uma transferência.

A base pública de 09/06/2026 contém 821 combinações sem estoque registrado, das quais 688 receberam consumo sintético positivo. A ausência de registro não comprova ausência de uso, assim como o consumo gerado não comprova demanda real. O notebook mantém essa distinção na análise dos destinos.

As células de cálculo e as entradas correspondem ao commit `5944d16c24f921a41d2d9df99c13f4ddf74fe065`. A atualização documental de 25/10/2026 inclui as planilhas manuais e organiza os registros já disponíveis, sem gerar novos resultados experimentais.
