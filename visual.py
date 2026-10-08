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


def cabecalho(titulo, descricao):
    st.title(titulo)
    st.markdown(f'<p class="page-description">{texto(descricao)}</p>',unsafe_allow_html=True)


def resumo(itens):
    for coluna, (rotulo, valor) in zip(st.columns(len(itens)), itens):
        coluna.metric(rotulo, numero(valor))


def lote_card(lote):
    risco=float(lote.risco)
    classe='attention' if risco>1e-8 else 'calm'
    estado='RISCO POTENCIAL' if risco>1e-8 else 'SEM RISCO NESTE CÁLCULO'
    st.markdown(f'''
<div class="lot-card">
  <div class="lot-main"><span class="tag {classe}">{estado}</span>
    <h3>{texto(lote.medicamento)}</h3><p>{texto(lote.unidade)} · lote {texto(lote.lote)}</p>
    <div class="pills"><span>Validade {lote.validade:%d/%m/%Y}</span>
      <span>{numero(lote.dias_ate_validade)} dias</span><span>CMM {numero(lote.cmm,2)}</span></div>
  </div>
  <div class="lot-amount"><strong>{numero(risco,2)}</strong><span>unidades em risco</span>
    <small>de {numero(lote.quantidade,2)} em estoque</small></div>
</div>''',unsafe_allow_html=True)


def destino_indicado(unidade, quantidade, justificativa, risco, capacidade):
    st.markdown(f'''
<div class="recommended-card">
  <span class="recommended-tag">✓ DESTINO INDICADO NESTA ETAPA</span>
  <div class="recommended-content"><div><p class="overline">A melhor opção pelas regras do modelo é</p>
    <h2>{texto(unidade)}</h2><p class="reason">{texto(justificativa)}</p></div>
    <div class="recommended-amount"><strong>{numero(quantidade)}</strong><span>unidades sugeridas</span></div>
  </div>
  <div class="recommended-footer"><span>Risco do lote nesta etapa: <b>{numero(risco,2)}</b></span>
    <span>Capacidade sem novo risco: <b>{numero(capacidade,2)}</b></span></div>
</div>''',unsafe_allow_html=True)


def alternativa_card(unidade, quantidade, capacidade, motivo):
    st.markdown(f'''
<div class="alternative-card"><span class="eyebrow">OUTRA POSSIBILIDADE</span>
<h3>{texto(unidade)}</h3><p class="alternative-amount">{numero(quantidade)} <span>unidades</span></p>
<p>Capacidade sem novo risco: <b>{numero(capacidade,2)}</b></p>
<div class="alternative-reason">{texto(motivo)}</div></div>''',unsafe_allow_html=True)


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
