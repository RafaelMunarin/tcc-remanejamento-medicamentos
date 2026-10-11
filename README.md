# Protótipo de remanejamento de medicamentos

Este projeto faz parte do meu TCC. A ideia é ter uma interface simples para consultar o resultado do modelo de apoio ao remanejamento de medicamentos entre UBS.

Separei a interface em três telas:

- **Importação**: envio da planilha e consulta do estoque;
- **Diagnóstico**: lotes em risco, com filtros por unidade e medicamento;
- **Destinos**: primeira opção em destaque e até três alternativas, com unidade e quantidade.

O modelo usa regras fixas de consumo médio mensal, PVPS e capacidade de absorção. Ele não usa aprendizado de máquina, não faz previsão e não realiza transferências sozinho.

## Arquivos principais

- `app.py`: interface do Streamlit.
- `modelo.py`: regras usadas pela interface.
- `modelo_remanejamento_tcc_rafael.ipynb`: notebook usado no Google Colab.
- `dados/`: planilhas usadas no experimento.
- `iniciar_streamlit.bat`: inicia a interface no Windows.
- `requirements.txt`: versões das bibliotecas.
- `verificar_integracao.py`: conferência rápida entre o notebook e a interface.

## Requisitos

- Windows 10 ou 11.
- Python 3.12.
- Git.
- Internet na primeira execução, para instalar as bibliotecas.

## 1. Clonar o projeto

Abra o CMD e escolha a pasta onde deseja guardar o projeto. Este exemplo usa a pasta TCC do OneDrive:

```cmd
cd /d "%USERPROFILE%\OneDrive\Documentos\TCC"
git clone https://github.com/RafaelMunarin/tcc-remanejamento-medicamentos.git
cd /d "%USERPROFILE%\OneDrive\Documentos\TCC\tcc-remanejamento-medicamentos"
```

Se a sua pasta for diferente, altere apenas os comandos `cd`.

Para confirmar que o projeto foi clonado corretamente:

```cmd
git remote -v
git status
```

## 2. Conferir Python e Git

```cmd
python --version
git --version
```

O Python deve aparecer como `Python 3.12.x`. Se `python` ou `git` não for reconhecido, instale o programa e abra um novo CMD.

## 3. Iniciar o Streamlit

Dentro da pasta do projeto, execute:

```cmd
iniciar_streamlit.bat
```

Na primeira vez, o arquivo cria o ambiente virtual e instala as bibliotecas. Depois, ele abre a interface no navegador. Deixe o CMD aberto enquanto usar o sistema.

O ambiente virtual é criado fora da pasta do projeto, em `%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv`. Fiz assim para evitar bloqueios do OneDrive com a pasta `.venv`.

Se o navegador não abrir, copie o endereço `Local URL` mostrado no CMD. Para parar a aplicação, pressione `Ctrl+C`.

## 4. Executar sem o arquivo `.bat`

Se precisar fazer cada etapa manualmente:

```cmd
python -m venv "%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv"
"%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv\Scripts\python.exe" -m pip install -r requirements.txt
"%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv\Scripts\python.exe" -m streamlit run app.py
```

## 5. Usar a interface

1. Abra **Importação**.
2. Envie `dados/Consulta de Estoque.xlsx`.
3. Clique em **Importar planilha**. O arquivo `CNES.xlsx` é usado internamente.
4. Confira a base pelos filtros.
5. Abra **Diagnóstico** e clique em **Gerar diagnóstico**.
6. Use os filtros para consultar os lotes e clique em **Ver destinos**.
7. Escolha um lote para comparar os destinos. Se houver mais de um envio, selecione qual deseja consultar.

O cálculo considera a rede inteira. Os filtros mudam apenas o que aparece na tela. Os cards comparam até quatro opções para o mesmo envio, na ordem definida pelo modelo. As quantidades das alternativas não devem ser somadas. As regras e as explicações do modelo ficam no notebook.

## 6. Abrir o notebook no Google Colab

1. Abra `modelo_remanejamento_tcc_rafael.ipynb` no Google Colab.
2. Execute as células na ordem.
3. Quando o notebook pedir, envie `dados/CNES.xlsx` e `dados/Consulta de Estoque.xlsx`.

O notebook contém o desenvolvimento das regras e os testes dos cenários. Não é necessário instalar o Streamlit para usar o notebook.

## 7. Conferir a integração

Depois de instalar as bibliotecas, execute na pasta do projeto:

```cmd
"%LOCALAPPDATA%\tcc-remanejamento-medicamentos\.venv\Scripts\python.exe" verificar_integracao.py
```

Esse comando compara as tabelas geradas pelo notebook com as tabelas usadas na interface.

## Observações

- Os seis meses de consumo são a janela usada para calcular o CMM. Isso não significa que o diagnóstico precise ser executado somente a cada seis meses.
- A validade e o consumo do experimento são sintéticos.
- A interface é um protótipo acadêmico executado localmente com Streamlit.
- O projeto não faz transferências automaticamente.
- A ausência de estoque em uma data não prova que a unidade não usa o medicamento.
