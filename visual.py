"""Elementos visuais compartilhados pelas seções da interface."""
from html import escape
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components


def configurar():
    st.set_page_config(page_title='Apoio ao remanejamento', page_icon='💊', layout='wide')
    css=(Path(__file__).parent/'estilo.css').read_text(encoding='utf-8')
    st.markdown('<style>'+css+'</style>', unsafe_allow_html=True)
    # Removo a preferência antiga para aplicar o tema fixo desta versão.
    components.html('''<script>
    try {
        const app = window.parent;
        const chave = `stActiveTheme-${app.location.pathname}-v1`;
        const tema = JSON.parse(app.localStorage.getItem(chave) || "null");
        if (tema && tema.name !== "Custom Theme") {
            app.localStorage.removeItem(chave);
            app.location.reload();
        }
    } catch (erro) {
        console.warn("Não foi possível remover a preferência antiga de tema.");
    }
    </script>''',height=0,width=0,tab_index=-1)


def texto(valor):
    return escape(str(valor))


def numero(valor, casas=0):
    return f'{valor:,.{casas}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def resumo(itens):
    for coluna, (rotulo, valor) in zip(st.columns(len(itens)), itens):
        coluna.metric(rotulo, numero(valor))


def lote_card(lote):
    st.markdown(f'''
<div class="lot-card">
  <div class="lot-main">
    <h3>{texto(lote.medicamento)}</h3><p>{texto(lote.unidade)} · lote {texto(lote.lote)}</p>
    <small>Validade simulada: {lote.validade:%d/%m/%Y}</small>
  </div>
  <div class="lot-amount"><strong>{numero(lote.risco,2)}</strong><span>unidades em risco</span>
    <small>de {numero(lote.quantidade,2)} em estoque</small></div>
</div>''',unsafe_allow_html=True)


def destinos_card(classificacao):
    primeira = classificacao.iloc[0]
    st.markdown(f'''
<div class="destination-primary">
  <span class="destination-rank">1ª opção - destino sugerido</span>
  <div class="destination-content">
    <h3>{texto(primeira.destino)}</h3>
    <div class="destination-amount"><strong>{numero(primeira.quantidade_admissivel)}</strong>
      <span>unidades sugeridas</span></div>
  </div>
</div>''', unsafe_allow_html=True)

    outras = classificacao.iloc[1:4]
    if not outras.empty:
        for posicao, (coluna, opcao) in enumerate(
            zip(st.columns(3), outras.itertuples(index=False)), start=2,
        ):
            with coluna:
                st.markdown(f'''
<div class="destination-alternative">
  <span class="destination-rank">{posicao}ª opção</span>
  <h3>{texto(opcao.destino)}</h3>
  <div class="destination-amount"><strong>{numero(opcao.quantidade_admissivel)}</strong>
    <span>unidades</span></div>
</div>''', unsafe_allow_html=True)
        st.caption('Alternativas para o mesmo envio. As quantidades não devem ser somadas.')


def tabela(dados, colunas, inteiros=(), decimais=(), altura=340):
    configuracao={}
    for nome in inteiros:
        if nome in colunas:
            configuracao[colunas[nome]]=st.column_config.NumberColumn(format='%d',width='small')
    for nome in decimais:
        if nome in colunas:
            configuracao[colunas[nome]]=st.column_config.NumberColumn(format='%.2f',width='small')
    for nome in ('medicamento','descricao_produto','unidade','nome_unidade','destino','origem'):
        if nome in colunas:
            configuracao[colunas[nome]]=st.column_config.TextColumn(width='medium')
    if 'validade' in colunas:
        configuracao[colunas['validade']]=st.column_config.DateColumn(format='DD/MM/YYYY')
    st.dataframe(dados[list(colunas)].rename(columns=colunas),hide_index=True,
                 width='stretch',height=altura,column_config=configuracao)
