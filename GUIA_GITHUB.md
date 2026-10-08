# Usar e atualizar o repositório

O projeto está no repositório público [RafaelMunarin/tcc-remanejamento-medicamentos](https://github.com/RafaelMunarin/tcc-remanejamento-medicamentos). O ponto de partida para a revisão é o [README.md](README.md).

## Baixar para executar

No GitHub, use **Code → Download ZIP** e extraia os arquivos. Siga as instruções do README para executar a interface ou abrir o notebook no Colab.

## Manter uma cópia com Git

Para editar o projeto e enviar ajustes, abra um terminal com Git disponível e clone o repositório:

```bash
git clone https://github.com/RafaelMunarin/tcc-remanejamento-medicamentos.git
cd tcc-remanejamento-medicamentos
```

Trabalhe nessa pasta. Antes de iniciar novos ajustes, com a cópia local sem alterações pendentes, atualize a branch:

```bash
git pull --ff-only
```

Depois de editar, confira os arquivos e envie o commit:

```bash
git status
git diff
git add .
git commit -m "Ajusta projeto apos orientacao"
git push
```

Se o Git solicitar identificação no primeiro commit, configure seu nome e o e-mail que usa para os commits. Para enviar, conclua a autenticação solicitada pelo Git.

As duas planilhas, o notebook e `.streamlit/config.toml` fazem parte do projeto. O `.gitignore` deixa de fora o ambiente virtual, os caches, as configurações locais e os arquivos exportados nas execuções.

## Compartilhar com o orientador

Compartilhe o link do repositório e indique o README como ponto de partida. Por ser público, o conteúdo pode ser consultado sem convite. O README explica como executar o Streamlit e onde conferir a avaliação no notebook. A interface continua sendo executada localmente.

No Drive, mantenha o texto atual do TCC e os documentos para revisão. Use o GitHub como referência para o código; se também guardar uma cópia do notebook no Drive, mantenha a mesma versão do repositório.
