# Fechamento da avaliação

Este pacote atualiza o notebook e reúne a conferência das regras. A interface e a regra principal de destinos continuam iguais.

Copie `modelo_remanejamento_tcc_rafael.ipynb` e a pasta `avaliacao` para a pasta do projeto. Substitua somente o notebook quando o Windows perguntar. Não apague o repositório.

## O que foi conferido aqui

- 8 de 8 cenários controlados conformes.
- 10 de 10 casos de borda conformes.
- 17 de 17 invariantes conformes.
- As nove tabelas ficaram idênticas em duas sessões locais distintas.
- O núcleo usado no Streamlit gerou as mesmas nove tabelas do notebook.
- 263 de 263 conferências de campos da planilha coincidiram com a exportação local.

Esses resultados são locais. Eles não substituem a reprodução no Colab nem a revisão humana da planilha.

## Notebook

O arquivo `.ipynb` é o que deve ser aberto no Google Colab. Ele está sem saídas salvas para a execução final.

A seção 24.7 registra as 821 combinações sem estoque, as 688 com consumo sintético positivo e os 141 movimentos para destinos sem registro do item, entre os 1.076 movimentos do cenário principal. Isso não comprova uso do medicamento nem viabilidade operacional da transferência.

A seção 24.5 inclui uma variante que aceita apenas destinos com registro original do item. Ela gerou 1.045 movimentos e 783 lotes com sugestão, contra 1.076 movimentos e 797 lotes no cenário principal. O plano é recalculado inteiro: a diferença de 31 movimentos não é uma simples exclusão dos 141 movimentos anteriores.

Essa variante não mudou a regra principal nem as nove tabelas usadas na reprodutibilidade.

## Conferência da planilha

Abra `conferencia_apoio.xlsx`. Comece pelas abas `Conferencia`, `Lotes`, `Capacidade` e `Plano`. A aba `Comparacao` mostra esperado, obtido e conformidade. Os valores obtidos já preenchidos vêm da execução local.

As únicas entradas das contas são `estoque_preparado.csv` e `historico_sintetico.csv`. Os recortes estão nas abas `Estoque` e `Historico`; os arquivos completos estão em `entradas`.

A amostra foi registrada em `amostra_registrada.json` antes da comparação específica. São oito combinações escolhidas por características das entradas: vários lotes, empate de validade, prazo curto, consumo zero e ausência de estoque. Todos os lotes dessas combinações entraram na conta, totalizando 19. Também entram os 16 destinos possíveis para o lote 2183 e o plano inteiro do medicamento 66. Esse medicamento foi escolhido pelo menor número de lotes entre os casos que atendiam aos critérios registrados, para manter a conta revisável.

Os esperados foram calculados em fórmulas e preservados em `esperados_planilha.json` antes de ler os resultados dessa amostra. O SHA-256 protege essa referência. Não altere os esperados para fazer uma comparação coincidir.

A tolerância é de 0,00000001 somente para valores calculados com casas decimais. IDs, quantidades inteiras e a sequência do medicamento devem coincidir exatamente. A sequência é relativa ao medicamento 66; IDs gerados para os lotes recebidos e números globais dos movimentos ficam fora deste recorte. O plano dessa amostra tem um movimento, portanto não testa disputa entre várias origens; essa situação está no cenário B7.

A preparação foi feita com auxílio do assistente, que já conhecia o notebook. Portanto, não é uma avaliação cega nem uma revisão humana independente. A revisão humana exigida pelo orientador continua pendente: conferir as fórmulas a partir das regras das seções 17 a 21, preencher revisor/data e registrar qualquer divergência e sua causa. Uma amostra intencional não permite generalização estatística.

## Execução final no Colab

1. Abra o notebook atualizado e execute todas as células. Envie `CNES.xlsx` e `Consulta de Estoque.xlsx` da pasta `dados` quando solicitado.
2. Na primeira execução, a seção 24.6 grava `referencia_reprodutibilidade.json`. Guarde uma cópia. Não use a referência de uma execução local para esta comparação.
3. Reinicie a sessão sem apagar os arquivos. Execute o notebook inteiro novamente, com as mesmas planilhas e parâmetros.
4. Confira a seção 24.6: precisam aparecer `SESSAO_DISTINTA` e `True` nas nove linhas. `MESMA_SESSAO` ou `CONTEXTO_DIFERENTE` não concluem essa etapa.
5. Na última célula, altere `BAIXAR_RESULTADOS = False` para `BAIXAR_RESULTADOS = True` e execute essa célula para baixar `Resultados_Modelo_Final.zip`.
6. Salve também o `.ipynb` com as saídas das duas execuções documentadas. Se a sessão apagar os arquivos, reenvie as mesmas planilhas e a referência gravada na primeira execução do Colab.

## Comparar a exportação do Colab

Coloque `Resultados_Modelo_Final.zip` dentro de `avaliacao`. No CMD, execute um comando de cada vez:

```bat
cd /d "C:\Users\rafae\OneDrive\Documentos\TCC\tcc-remanejamento-medicamentos\avaliacao"
```

```bat
python conferir_exportacao.py Resultados_Modelo_Final.zip --ambiente colab --saida conferencia_colab
```

O script usa apenas bibliotecas que já vêm com o Python. Ele não recalcula o modelo: compara a exportação com os esperados preservados da planilha e exige as mesmas entradas. O parâmetro `--ambiente colab` identifica a origem informada do arquivo; ele não detecta onde o notebook foi executado.

O resultado fica em `conferencia_colab`. Se houver divergência, investigue a causa. Se o modelo precisar de correção, reexecute e refaça a conferência. O script não preenche a revisão humana por você.

## Publicar esta atualização

Depois de copiar os arquivos para o projeto, execute um comando de cada vez:

```bat
cd /d "C:\Users\rafae\OneDrive\Documentos\TCC\tcc-remanejamento-medicamentos"
```

```bat
git status
```

```bat
git add modelo_remanejamento_tcc_rafael.ipynb avaliacao
```

```bat
git commit -m "Atualiza avaliacao e prepara conferencia das regras"
```

```bat
git push origin main
```

Os arquivos vão soltos para o GitHub. Não adicione este ZIP.

## O que ainda falta

- Registrar a revisão humana da conferência e suas limitações.
- Guardar a reprodução em sessões distintas do Colab e comparar a exportação final.
- Revisar o capítulo 3 do texto vigente e consolidar os resultados e limites no relatório. As contagens devem vir da versão final e ser descritas como resultados do cenário simulado.

Use "X de Y conferências coincidiram", sem chamar isso de acurácia. A interface é um protótipo acadêmico; a importação mensal de movimentações reais continua fora desta entrega.
