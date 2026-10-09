# Modelo de remanejamento de medicamentos

A ideia é analisar o estoque de medicamentos das UBS e mostrar:

* quais lotes podem vencer;
* quais unidades podem receber parte desse estoque;
* qual destino faz mais sentido para cada lote.

O modelo usa regras fixas de consumo médio mensal, PVPS e capacidade de absorção. Ele não usa aprendizado de máquina, não faz previsão e não realiza transferências sozinho.

Os dados de validade e de consumo usados no experimento são gerados pelo próprio código. A base de estoque e o cadastro das unidades ficam na pasta `dados`.

## 1\. Clonar o projeto

Abra o CMD e escolha a pasta onde deseja guardar o projeto.

```cmd
git clone https://github.com/RafaelMunarin/tcc-remanejamento-medicamentos.git
```

Se a sua pasta for diferente, altere apenas os comandos `cd`.

Para confirmar que o projeto foi clonado corretamente:

```cmd
git remote -v
git status
```

## 2\. Conferir Python e Git

```cmd
python --version
git --version
```

O Python deve aparecer como `Python 3.12.x`. Se `python` ou `git` não for reconhecido, instale o programa e abra um novo CMD.

## 3\. Iniciar o Streamlit

Dentro da pasta do projeto, execute:

```cmd
iniciar_streamlit.bat
```

Na primeira vez, o arquivo cria o ambiente virtual e instala as bibliotecas. Depois, ele abre a interface no navegador. Deixe o CMD aberto enquanto usar o sistema.

Se o navegador não abrir, copie o endereço `Local URL` mostrado no CMD. Para parar a aplicação, pressione `Ctrl+C`.

## 4\. Executar sem o arquivo `.bat`

Se precisar fazer cada etapa manualmente:

```cmd
python -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.venv\\Scripts\\python.exe -m streamlit run app.py
```

## 5\. Usar a interface

1. Abra **Importação**.
2. Envie `dados/Consulta de Estoque.xlsx`.
3. Clique em **Importar planilha**. O arquivo `CNES.xlsx` é usado internamente.
4. Consulte os dados por unidade ou medicamento.
5. Abra **Diagnóstico** e clique em **Executar diagnóstico**.
6. Escolha um lote em risco para ver os possíveis destinos.

O cálculo considera a rede inteira, mesmo quando um filtro está ativo. As alternativas exibidas para um lote são opções diferentes para a mesma situação e não devem ser somadas.

## 6\. Abrir o notebook no Google Colab

1. Abra `modelo_remanejamento_tcc_rafael.ipynb` no Google Colab.
2. Execute as células na ordem.
3. Quando o notebook pedir, envie `dados/CNES.xlsx` e `dados/Consulta de Estoque.xlsx`.

O notebook contém o desenvolvimento das regras e os testes dos cenários. Não é necessário instalar o Streamlit para usar o notebook.