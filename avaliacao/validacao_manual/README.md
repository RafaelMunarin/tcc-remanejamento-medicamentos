# Registro da conferência manual

Registrei esta conferência em 21/10/2026 para examinar os dados de entrada, o diagnóstico por lote e o plano de remanejamento de uma amostra do modelo. As planilhas preservam os valores preenchidos e os campos de identificação da revisão. A exportação utilizada foi identificada como `Resultados_Modelo_Final.zip`, obtida na mesma data.

## Arquivos

| Arquivo | Registro preservado |
| --- | --- |
| [Validacao_manual_Rafael - Resultados.xlsx](<Validacao_manual_Rafael - Resultados.xlsx>) | Arquivo original preenchido, com tolerância zero na célula `Entradas!B10` |
| [Validacao_manual_Rafael_Tolerancia_Conferida.xlsx](Validacao_manual_Rafael_Tolerancia_Conferida.xlsx) | Cópia com a tolerância de 0,00000001 restaurada, fórmulas recalculadas e identificação da exportação |
| [SHA256SUMS](SHA256SUMS) | SHA-256 dos dois arquivos, para verificar sua integridade |

Os arquivos foram incluídos sem alteração de seu conteúdo. Mantive inclusive os textos de orientação que faziam parte do instrumento utilizado, pois eles registram como a planilha foi preparada. A descrição consolidada do procedimento e de seus resultados está neste documento.

## Amostra e valores registrados

A amostra reúne seis lotes analíticos do medicamento 33 e dois do medicamento 104, totalizando oito lotes. A análise de capacidade considera as 17 unidades do recorte, enquanto a conferência do plano acompanha três movimentos de um medicamento.

| Parte da conferência | Células na aba `Calculos` | Quantidade de valores |
| --- | --- | ---: |
| Saldos dos lotes | `H9:H16` | 8 |
| Consumo médio mensal | `G23:G40` | 18 |
| Quantidade consumível e risco por lote | `L48:M55` | 16 |
| Capacidade livre e capacidade sem novo risco | `B69:B70` | 2 |
| Destino e quantidade de cada movimento | `B85:B86`, `B140:B141` e `B195:B196` | 6 |
| Total | | 50 |

O quadro da aba `Comparacao` reúne 39 desses valores: oito saldos, sete médias mensais, 16 resultados do diagnóstico, duas capacidades e seis valores do plano. As 11 médias mensais adicionais completam a conferência de 50 valores. Esse total se refere aos campos preenchidos, não a 50 casos independentes.

## Tolerância e resultado

Os 50 valores manuais são iguais nas duas versões. No arquivo original, a tolerância zero provocava sete indicações de `INVESTIGAR` por diferenças decimais, enquanto as outras 32 linhas apresentavam `COINCIDE`. Na cópia ajustada, `Entradas!B10` contém `0,00000001` e as 39 linhas de `Comparacao!H11:H49` apresentam `COINCIDE`.

A maior diferença absoluta entre os valores manuais e as referências do quadro é inferior a 0,000000001, portanto menor que a tolerância adotada. Os identificadores dos destinos e as quantidades inteiras coincidem exatamente. As 18 médias registradas em `Calculos!G23:G40` também concordam com as referências correspondentes, dentro da mesma tolerância.

A comparação não altera a regra de consumo por lote. Por exemplo, a capacidade acumulada de aproximadamente 328,4556 unidades para o lote 829 não significa que esse lote possa consumir tal quantidade: seu saldo é de 60 unidades, que limita a quantidade consumível a 60. O risco calculado para esse lote é zero. A distinção entre capacidade livre e capacidade sem novo risco também foi examinada, incluindo a situação em que uma capacidade livre positiva não permite receber estoque porque isso aumentaria o risco de lotes próprios posteriores.

## Identificação da revisão

A aba `Comparacao` registra Rafael Batistti Munarin em `B5` e a data de 21/10/2026 em `B6`. Os campos `B54:B56` e `B63` contêm `Sim`. Na cópia ajustada, `B64` identifica `Resultados_Modelo_Final.zip (21/10/2026)`; esse campo estava vazio no original.

A célula `Comparacao!B7` da cópia ajustada apresenta `REGISTROS PREENCHIDOS; REVISAR CONCLUSAO`. Essa é a mensagem prevista pela fórmula quando não há divergências, os campos exigidos estão preenchidos e as confirmações foram registradas. Ela não representa uma divergência numérica nem equivale a aprovação externa do trabalho.

O texto em `Entradas!A16`, segundo o qual a revisão de Rafael começava pendente, pertence à preparação inicial do instrumento. O estado posterior é documentado pelos valores preenchidos e pelos campos de revisão. Os dois arquivos foram mantidos para preservar essa sequência, sem modificar retroativamente o registro original.

## Alcance da conferência

A seleção da amostra e a preparação da planilha contaram com auxílio de assistente após acesso ao código e às saídas. A revisão foi registrada por mim, mas nem todas as contas intermediárias foram guardadas. A amostra verifica a concordância dos valores registrados com as regras adotadas, sem constituir avaliação cega ou revisão independente.

Os identificadores dos lotes recebidos e a numeração global dos movimentos ficaram fora da comparação. Também não foi obtido o hash do ZIP originalmente baixado, por isso os hashes desta pasta identificam apenas as planilhas preservadas. Validade e consumo permanecem sintéticos, e a concordância da amostra não demonstra a viabilidade operacional das transferências.

A comparação automatizada de 263 campos, preservada em [conferencia_colab](../conferencia_colab/), pertence a uma amostra anterior. Seus resultados e a indicação histórica de revisão humana pendente são mantidos separadamente, conforme descrito no [registro da avaliação](../LEIA_ME.md).
