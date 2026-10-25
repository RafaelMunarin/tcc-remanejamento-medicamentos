# Modelo de apoio ao remanejamento de medicamentos

Este repositório reúne o desenvolvimento do meu TCC em Sistemas de Informação na UNIDAVI, intitulado **Modelo baseado em dados para apoio à análise do remanejamento de medicamentos em Unidades Básicas de Saúde**. O projeto identifica lotes com risco de vencimento e calcula possibilidades de remanejamento entre unidades, com uma interface local para consultar os resultados.

O modelo usa regras determinísticas de consumo médio mensal, alocação PVPS (Primeiro que Vence, Primeiro que Sai) e capacidade do destino. A heurística gulosa escolhe a maior quantidade admissível e atualiza os saldos após cada sugestão, preservando o estoque utilizável na origem e a capacidade sem novo risco no destino. A ordem das escolhas pode afetar o plano, sem garantia de melhor solução global.

O experimento considera 17 unidades, 161 medicamentos e 3.846 lotes analíticos. O cadastro e o saldo vêm das planilhas preservadas em `dados/`; as validades e as saídas mensais são sintéticas. A posição de referência é 09/06/2026, com seis meses de consumo sintético, de dezembro de 2025 a maio de 2026. O projeto não usa aprendizado de máquina e as sugestões dependem da avaliação do responsável antes de qualquer transferência.

## Organização do repositório

| Arquivo ou pasta | Conteúdo |
| --- | --- |
| [modelo_remanejamento_tcc_rafael.ipynb](modelo_remanejamento_tcc_rafael.ipynb) | Desenvolvimento do modelo, cálculos e avaliação no Google Colab |
| [app.py](app.py) | Interface local em Streamlit |
| [modelo.py](modelo.py) | Regras de cálculo usadas pela interface |
| [visual.py](visual.py) e [estilo.css](estilo.css) | Apresentação das informações na interface |
| [dados](dados/) | Planilhas de entrada preservadas para o experimento |
| [avaliacao/LEIA_ME.md](avaliacao/LEIA_ME.md) | Procedimentos, resultados e limites das verificações |
| [avaliacao/validacao_manual](avaliacao/validacao_manual/) | Planilhas preenchidas da conferência manual, identificação dos arquivos e hashes |
| [verificar_integracao.py](verificar_integracao.py) | Comparação entre as tabelas do notebook e do núcleo da interface |
| [iniciar_streamlit.bat](iniciar_streamlit.bat) | Inicialização da interface no Windows |
| [requirements.txt](requirements.txt) | Versões das bibliotecas usadas pela aplicação |

## Execução local

A aplicação utiliza Windows 10 ou 11, Python 3.12 e Git. A primeira execução também precisa de acesso à internet para instalar as bibliotecas. A clonagem e a inicialização são feitas no CMD, a partir da pasta escolhida para o projeto:

```cmd
git clone https://github.com/RafaelMunarin/tcc-remanejamento-medicamentos.git
cd tcc-remanejamento-medicamentos
iniciar_streamlit.bat
```

O arquivo de inicialização cria o ambiente virtual em `%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv`, instala as dependências e inicia o Streamlit. Mantive o ambiente fora da pasta do projeto para evitar bloqueios de sincronização do OneDrive. O CMD permanece aberto durante o uso; `Ctrl+C` encerra a aplicação. O endereço `Local URL`, exibido no terminal, permite abrir a interface quando o navegador não inicia automaticamente.

A execução sem o arquivo `.bat` usa os mesmos caminhos:

```cmd
python -m venv "%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv"
"%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv\Scripts\python.exe" -m pip install -r requirements.txt
"%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv\Scripts\python.exe" -m streamlit run app.py
```

## Consulta pela interface

Organizei a interface em três telas. Em **Importação**, o arquivo `dados/Consulta de Estoque.xlsx` é enviado e processado pelo botão **Importar planilha**, enquanto o cadastro `CNES.xlsx` é usado internamente. A base importada pode ser consultada pelos filtros disponíveis.

Em **Diagnóstico**, o botão **Gerar diagnóstico** executa o cálculo para toda a rede. A consulta dos lotes permite acessar **Ver destinos**, onde aparecem a primeira opção e até três alternativas para o envio selecionado. Quando um lote participa de mais de um envio, cada movimento pode ser consultado separadamente.

Os filtros alteram apenas a exibição. As alternativas representam possibilidades para o mesmo envio, por isso suas quantidades não são somadas. A geração do plano considera a capacidade já ocupada pelas sugestões anteriores.

## Notebook e integração

O notebook é executado no Google Colab, com as células na ordem e envio de `dados/CNES.xlsx` e `dados/Consulta de Estoque.xlsx` quando solicitado. A cópia pública não contém saídas salvas. As seções de avaliação registram as regras verificadas e os resultados históricos, enquanto a seção 24.6 compara nove tabelas entre sessões distintas.

A última célula permite baixar `Resultados_Modelo_Final.zip` quando `BAIXAR_RESULTADOS = True`. O uso do notebook independe da instalação do Streamlit. No ambiente local, a integração é conferida com:

```cmd
"%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv\Scripts\python.exe" verificar_integracao.py
```

## Resultados e limites

No cenário principal, 1.198 lotes apresentaram risco, dos quais 797 receberam sugestão de remanejamento, em 1.076 movimentos. Os outros 401 lotes permaneceram sem sugestão. As verificações registradas abrangem oito cenários controlados, dez casos de borda, 17 invariantes e a reprodução das nove tabelas. A conferência manual de 21/10/2026 reúne 50 valores, com concordância dentro da tolerância decimal de 0,00000001 e igualdade exata nos identificadores e nas quantidades inteiras.

A documentação da [avaliação](avaliacao/LEIA_ME.md) distingue essa conferência manual da comparação automatizada anterior de 263 campos. As [duas planilhas manuais](avaliacao/validacao_manual/) preservam o arquivo recebido e a cópia com a tolerância ajustada, sem alteração dos 50 valores preenchidos.

Os resultados descrevem um experimento com validade e consumo sintéticos. O modelo não avalia transporte, armazenamento ou elegibilidade operacional, e a ausência de estoque em uma data não comprova que a unidade não utiliza o medicamento. A interface é um protótipo acadêmico, sem transferências automáticas ou importação mensal de movimentações reais.

As regras de cálculo correspondem ao [commit 5944d16](https://github.com/RafaelMunarin/tcc-remanejamento-medicamentos/commit/5944d16c24f921a41d2d9df99c13f4ddf74fe065). O [commit 3357d60](https://github.com/RafaelMunarin/tcc-remanejamento-medicamentos/commit/3357d6069042bf19f50679d8772d2aba6a2dfc65) registra a atualização documental de 23/10/2026. A inclusão das planilhas e a revisão dos textos em 25/10/2026 preservam o código e as entradas desse experimento.
