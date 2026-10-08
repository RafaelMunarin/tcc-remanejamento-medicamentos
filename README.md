# Modelo de apoio ao remanejamento de medicamentos

**Rafael Munarin · TCC em Sistemas de Informação · Versão para revisão do orientador**

Neste projeto, identifico lotes com risco potencial de vencimento e unidades que podem receber parte desse estoque. Uso um modelo determinístico baseado em regras de consumo médio mensal (CMM), PVPS — Primeiro que Vence, Primeiro que Sai — e capacidade de absorção.

O desenvolvimento e a avaliação estão no notebook, organizados pelo CRISP-DM. A interface em Streamlit permite consultar os dados e visualizar as sugestões. Ela utiliza as mesmas regras do notebook.

## O que conferir nesta versão

- **Modelo e metodologia:** [notebook do TCC](modelo_remanejamento_tcc_rafael.ipynb), com as regras na seção 1 e a preparação dos dados nas seções 3–14.
- **Avaliação:** seção 24 do notebook, com cenários controlados, casos de borda, invariantes, sensibilidade e reprodutibilidade.
- **Funcionamento visual:** seguir o roteiro de execução abaixo e consultar um lote em risco e seus destinos.

## Dados e limites do experimento

| Informação | Origem |
|---|---|
| Cadastro das unidades e posição de estoque | Planilhas da pasta `dados` |
| Validade dos lotes e seis meses de saídas | Geração sintética e determinística no código |
| CMM, risco, capacidade e sugestões | Cálculos do modelo |

A referência é fixa em **09/06/2026**. O histórico sintético corresponde a **dezembro/2025 a maio/2026**. A planilha importada contém uma posição de estoque; os seis meses de consumo são gerados internamente.

O modelo não usa aprendizado de máquina, não prevê consumo e não executa transferências. As sugestões seguem escolhas sequenciais; não representam uma solução global ótima. Os resultados verificam o comportamento das regras no experimento e não comprovam perdas reais ou a viabilidade operacional de uma transferência.

## Executar a interface no Windows

1. Baixe o projeto completo pelo GitHub em **Code → Download ZIP**, ou use o pacote recebido, e extraia os arquivos.
2. Use **Python 3.12**. No CMD, confira se `python --version` retorna `Python 3.12.x`.
3. Abra a pasta que contém `app.py` e execute **`iniciar_windows.bat`**.
4. Aguarde a abertura do navegador. Na primeira execução, o iniciador instala as bibliotecas e precisa de internet. Mantenha o terminal aberto durante o uso.

Se o navegador não abrir, use o endereço **Local URL** exibido no terminal. Para encerrar, pressione `Ctrl+C` no terminal.

### Roteiro de uso

1. Em **Importação**, envie `dados/Consulta de Estoque.xlsx` e clique em **Importar planilha**. O cadastro `CNES.xlsx` é lido internamente.
2. Consulte o estoque por unidade ou busque um medicamento.
3. Em **Diagnóstico**, clique em **Executar diagnóstico**. Os filtros permitem consultar a rede, uma unidade ou um medicamento.
4. Selecione um lote em risco e abra **Ver destinos deste lote**. O card destaca a unidade indicada e a quantidade sugerida; as alternativas ficam abaixo.

O cálculo considera a rede completa, mesmo quando a consulta está filtrada. As quantidades das alternativas não devem ser somadas como novos envios: cada uma representa uma possibilidade na mesma etapa. Trocar a planilha exige importar e calcular novamente.

### Conferência rápida

Com os arquivos incluídos e a consulta em **Rede completa**, a referência é:

| Resultado | Quantidade |
|---|---:|
| Unidades | 17 |
| Medicamentos | 161 |
| Lotes | 3.846 |
| Lotes em risco | 1.198 |
| Lotes com sugestão de envio | 797 |
| Lotes sem sugestão de envio | 401 |
| Sugestões de envio no plano | 1.076 |

Um lote pode ter mais de um envio e ainda manter risco residual. Essas contagens descrevem o experimento; não são medidas de acurácia.

## Abrir o notebook no Google Colab

Abra **`modelo_remanejamento_tcc_rafael.ipynb`** no Colab e execute as células em ordem. Quando solicitado, envie as duas planilhas da pasta `dados`: `CNES.xlsx` e `Consulta de Estoque.xlsx`.

O notebook mantém as saídas salvas da execução anterior. Para conferir uma nova execução, siga a seção **24.6**, que compara o conteúdo completo das nove tabelas após reiniciar a sessão. Não é necessário instalar o Streamlit para executar o notebook.

## Conferir a integração entre notebook e interface

Depois de iniciar o aplicativo ao menos uma vez, abra o terminal na pasta do projeto e execute:

```powershell
.venv\Scripts\python.exe verificar_integracao.py
```

A verificação compara as nove tabelas do notebook com as produzidas pelo núcleo usado na interface. Na base incluída, a conferência retornou **nove tabelas idênticas, 18 cenários conformes e 17 invariantes conformes**. Isso é verificação das regras, não validação em UBS reais. A sensibilidade e a comparação entre sessões estão no notebook.

<details>
<summary>Execução pelo terminal, sem o iniciador</summary>

No Windows, dentro da pasta do projeto:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

No Linux/macOS, usando Python 3.12:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Para conferir a integração nesses ambientes, execute `.venv/bin/python verificar_integracao.py`.

</details>

## Arquivos principais

| Arquivo | Função |
|---|---|
| [modelo_remanejamento_tcc_rafael.ipynb](modelo_remanejamento_tcc_rafael.ipynb) | Desenvolvimento e avaliação no Colab |
| [modelo.py](modelo.py) | Preparação dos dados e regras usadas pela interface |
| [app.py](app.py) | Importação, diagnóstico, filtros e consulta de destinos |
| `visual.py`, `estilo.css` e `.streamlit/config.toml` | Apresentação da interface e tema escuro |
| `dados/` | Planilhas necessárias para reproduzir o experimento |
| [iniciar_windows.bat](iniciar_windows.bat) e [requirements.txt](requirements.txt) | Inicialização e versões das bibliotecas |
| [verificar_integracao.py](verificar_integracao.py) | Comparação entre notebook e núcleo do Streamlit |

## Pontos para alinhamento na orientação

- **Rotina de importação mensal:** permanece em discussão. Os seis meses representam a janela usada para calcular o CMM, não um intervalo obrigatório entre diagnósticos. A versão atual trabalha com uma posição fixa de estoque e não acumula importações mensais.
- **Conferência independente por planilha:** não foi realizada. A consulta dos cenários no Colab não substitui essa etapa; a retirada do item precisa ser alinhada com o orientador, conforme registrado na seção 24.4.

O GitHub reúne os arquivos para consulta e download. A interface descrita aqui é executada localmente com Streamlit.
