"""Importação do estoque e consulta dos resultados."""
from io import BytesIO
from pathlib import Path
import json
import zipfile

import streamlit as st

from modelo import PARAMETROS, TOL, preparar_dados, executar_modelo, tabelas_apresentacao
from visual import configurar, numero, resumo, lote_card, destinos_card, tabela

PASTA = Path(__file__).resolve().parent
PAGINAS = ['Importação', 'Diagnóstico', 'Destinos']
configurar()
st.session_state.setdefault('navegacao', 'Importação')


def liberada(pagina):
    if pagina == 'Diagnóstico':
        return 'base_ativa' in st.session_state
    if pagina == 'Destinos':
        return 'base_ativa' in st.session_state and 'execucao' in st.session_state
    return pagina == 'Importação'


def navegar(pagina):
    if liberada(pagina):
        st.session_state['navegacao'] = pagina


def limpar_base():
    # Ao trocar a planilha, retiro os resultados da base anterior.
    for nome in ['base_ativa', 'execucao', 'consulta', 'resultado_zip',
                 '_erro_importacao', '_erro_diagnostico', '_apenas_risco']:
        st.session_state.pop(nome, None)
    for nome in list(st.session_state):
        if nome.startswith(('_base_', '_diag_', '_sug_', '_lote_')):
            st.session_state.pop(nome, None)


def nomes():
    cadastro = st.session_state['base_ativa']['cadastro']
    unidades = cadastro['unidades'].set_index('id_unidade').nome_unidade.to_dict()
    medicamentos = cadastro['medicamentos'].set_index('id_medicamento').descricao_produto.to_dict()
    return unidades, medicamentos


def escolher_recorte(prefixo):
    unidades, medicamentos = nomes()
    anterior = st.session_state.get('consulta', {'unidade': None, 'medicamento': None})
    colunas = st.columns(2)
    consulta = {}
    campos = [('unidade', 'Unidade', unidades, 'Todas as unidades'),
              ('medicamento', 'Medicamento', medicamentos, 'Todos os medicamentos')]
    for coluna, (campo, rotulo, cadastro, todos) in zip(colunas, campos):
        opcoes = [None] + sorted(cadastro, key=lambda item: cadastro[item])
        indice = opcoes.index(anterior[campo]) if anterior[campo] in opcoes else 0
        consulta[campo] = coluna.selectbox(
            rotulo, opcoes, index=indice, key=prefixo + '_' + campo,
            format_func=lambda item, nomes=cadastro, texto=todos: texto if item is None else nomes[item],
        )
    st.session_state['consulta'] = consulta
    return consulta


def filtrar(dados, consulta):
    if consulta['unidade'] is not None:
        dados = dados.loc[dados.id_unidade.eq(consulta['unidade'])]
    if consulta['medicamento'] is not None:
        dados = dados.loc[dados.id_medicamento.eq(consulta['medicamento'])]
    return dados


def exportar(execucao):
    diagnostico, plano, combinacoes = tabelas_apresentacao(execucao)
    tabelas = {
        'diagnostico_lotes': diagnostico,
        'plano_remanejamento': plano,
        'diagnostico_combinacoes': combinacoes,
        'alternativas_decisoes': execucao['resultado']['alternativas'],
    }
    arquivo = BytesIO()
    with zipfile.ZipFile(arquivo, 'w', zipfile.ZIP_DEFLATED) as pacote:
        for nome, dados in tabelas.items():
            pacote.writestr(nome + '.csv', dados.to_csv(index=False).encode('utf-8-sig'))
        contexto = {'parametros': execucao['parametros'], 'fontes_sha256': execucao['fontes_sha256']}
        pacote.writestr('contexto.json', json.dumps(contexto, ensure_ascii=False, indent=2))
    return arquivo.getvalue()


def pagina_base():
    st.title('Importar estoque')
    arquivo = st.file_uploader(
        'Planilha de estoque (.xlsx)', type=['xlsx'], key='_estoque', on_change=limpar_base,
    )
    importar, exemplo = st.columns(2)
    if importar.button('Importar planilha', type='primary', disabled=arquivo is None):
        limpar_base()
        try:
            with st.spinner('Importando estoque...'):
                cnes = (PASTA / 'dados' / 'CNES.xlsx').read_bytes()
                estoque = arquivo.getvalue()
                cadastro = preparar_dados(cnes, estoque, dict(PARAMETROS))
            st.session_state['base_ativa'] = dict(
                cadastro=cadastro, cnes=cnes, estoque=estoque, arquivo=arquivo.name,
            )
        except Exception as erro:
            st.session_state['_erro_importacao'] = str(erro)
        st.rerun()

    planilha = PASTA / 'dados' / 'Consulta de Estoque.xlsx'
    if planilha.exists():
        exemplo.download_button(
            'Baixar planilha de exemplo', data=planilha.read_bytes(), file_name=planilha.name,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    if '_erro_importacao' in st.session_state:
        st.error('Não foi possível importar a planilha: ' + st.session_state['_erro_importacao'])
    if 'base_ativa' not in st.session_state:
        return

    st.divider()
    st.subheader('Estoque importado')
    st.caption(st.session_state['base_ativa']['arquivo'])
    unidades, _ = nomes()
    a, b = st.columns(2)
    unidade = a.selectbox(
        'Unidade', [None] + sorted(unidades, key=unidades.get), key='_base_unidade',
        format_func=lambda item: 'Todas as unidades' if item is None else unidades[item],
    )
    busca = b.text_input('Buscar medicamento', placeholder='Nome do medicamento', key='_base_busca')
    base = st.session_state['base_ativa']['cadastro']['base']
    if unidade is not None:
        base = base.loc[base.id_unidade.eq(unidade)]
    if busca.strip():
        base = base.loc[base.descricao_produto.str.contains(busca.strip(), case=False, regex=False)]
    if base.empty:
        st.info('Nenhum registro encontrado com esses filtros.')
    else:
        tabela(base, {'descricao_produto': 'Medicamento', 'nome_unidade': 'Unidade',
                      'lote': 'Lote', 'quantidade_estoque': 'Saldo'}, decimais=['quantidade_estoque'])
        st.caption(f'{numero(len(base))} lotes na consulta')
    st.button('Ir para o diagnóstico', type='primary', on_click=navegar, args=('Diagnóstico',))


def pagina_diagnostico():
    st.title('Diagnóstico')
    if 'execucao' not in st.session_state:
        st.caption('Estoque: ' + st.session_state['base_ativa']['arquivo'])
        if st.button('Gerar diagnóstico', type='primary'):
            ativa = st.session_state['base_ativa']
            st.session_state.pop('_erro_diagnostico', None)
            try:
                with st.spinner('Gerando diagnóstico...'):
                    resultado = executar_modelo(ativa['cnes'], ativa['estoque'])
                    pacote = exportar(resultado)
                st.session_state['execucao'] = resultado
                st.session_state['resultado_zip'] = pacote
            except Exception as erro:
                st.session_state['_erro_diagnostico'] = str(erro)
            st.rerun()
        if '_erro_diagnostico' in st.session_state:
            st.error('Não foi possível gerar o diagnóstico: ' + st.session_state['_erro_diagnostico'])
        return

    consulta = escolher_recorte('_diag')
    diagnostico, plano, _ = tabelas_apresentacao(st.session_state['execucao'])
    dados = filtrar(diagnostico, consulta)
    risco = dados.loc[dados.risco.gt(TOL)]
    com_destino = int(risco.id_lote.isin(plano.id_lote_origem).sum())
    resumo([('Lotes em risco', len(risco)), ('Com destino sugerido', com_destino),
            ('Sem destino sugerido', len(risco) - com_destino)])

    apenas_risco = st.toggle('Somente lotes em risco', value=True, key='_apenas_risco')
    visiveis = (risco if apenas_risco else dados).sort_values(['validade', 'id_lote'])
    if visiveis.empty:
        st.info('Nenhum lote encontrado com esses filtros.')
    else:
        tabela(visiveis, {
            'medicamento': 'Medicamento', 'unidade': 'Unidade', 'lote': 'Lote',
            'quantidade': 'Saldo', 'risco': 'Em risco', 'quantidade_sugerida': 'Envio sugerido',
            'validade': 'Validade simulada',
        }, inteiros=['quantidade_sugerida'], decimais=['quantidade', 'risco'], altura=400)

    destinos, baixar = st.columns(2)
    destinos.button('Ver destinos', type='primary', disabled=risco.empty,
                    on_click=navegar, args=('Destinos',))
    baixar.download_button('Baixar resultados da rede', data=st.session_state['resultado_zip'],
                           file_name='Resultados_Streamlit.zip', mime='application/zip')


def pagina_destinos():
    st.title('Destinos sugeridos')
    consulta = escolher_recorte('_sug')
    diagnostico, plano, _ = tabelas_apresentacao(st.session_state['execucao'])
    risco = filtrar(diagnostico, consulta)
    risco = risco.loc[risco.risco.gt(TOL)].sort_values(['validade', 'id_lote'])
    if risco.empty:
        st.info('Nenhum lote em risco com esses filtros.')
        return

    por_id = risco.set_index('id_lote')
    opcoes = risco.id_lote.tolist()
    if st.session_state.get('_lote_sugestao') not in opcoes:
        st.session_state['_lote_sugestao'] = opcoes[0]
    id_lote = st.selectbox(
        'Lote', opcoes, key='_lote_sugestao',
        format_func=lambda item: (
            f'{por_id.loc[item, "medicamento"]} - '
            f'lote {por_id.loc[item, "lote"]} - {por_id.loc[item, "unidade"]}'
        ),
    )
    lote = por_id.loc[id_lote]
    lote_card(lote)
    envios = plano.loc[plano.id_lote_origem.eq(id_lote)].sort_values('ordem_movimento')
    if envios.empty:
        if lote.dias_ate_validade <= 0:
            mensagem = 'Sem destino sugerido: o lote não tem prazo até o vencimento.'
        elif lote.risco + TOL < 1:
            mensagem = 'Sem destino sugerido: a quantidade em risco é menor que uma unidade.'
        else:
            mensagem = 'Sem destino sugerido para este lote no cenário analisado.'
        st.info(mensagem)
        return

    if len(envios) > 1:
        ordens = envios.ordem_movimento.tolist()
        if st.session_state.get('_sug_envio') not in ordens:
            st.session_state['_sug_envio'] = ordens[0]
        ordem = st.selectbox(
            'Comparar destinos do envio', ordens, key='_sug_envio',
            format_func=lambda item: f'{ordens.index(item) + 1} de {len(ordens)}',
        )
        envio = envios.loc[envios.ordem_movimento.eq(ordem)].iloc[0]
    else:
        envio = envios.iloc[0]

    # Comparo as opções da mesma etapa, na ordem usada pelo modelo.
    alternativas = st.session_state['execucao']['resultado']['alternativas']
    classificacao = alternativas.loc[
        alternativas.etapa.eq(envio.etapa)
        & alternativas.id_lote_origem.eq(id_lote)
        & alternativas.quantidade_admissivel.gt(0)
    ].sort_values(['quantidade_admissivel', 'capacidade_livre', 'id_unidade_destino'],
                  ascending=[False, False, True]).head(4).copy()
    unidades, _ = nomes()
    classificacao['destino'] = classificacao.id_unidade_destino.map(unidades)
    destinos_card(classificacao)
    st.caption('As sugestões precisam ser avaliadas pelo responsável antes de qualquer transferência.')


if not liberada(st.session_state['navegacao']):
    st.session_state['navegacao'] = 'Importação'
pagina = st.session_state['navegacao']
with st.sidebar:
    st.markdown('<div class="sidebar-brand"><span class="health-mark">+</span>'
                '<div><b>Remanejamento</b><small>de medicamentos</small></div></div>',
                unsafe_allow_html=True)
    for destino in PAGINAS:
        ajuda = None
        if not liberada(destino):
            ajuda = 'Importe a planilha primeiro.' if destino == 'Diagnóstico' else 'Gere o diagnóstico primeiro.'
        st.button(destino, key='nav_' + destino,
                  type='primary' if pagina == destino else 'secondary', width='stretch',
                  disabled=not liberada(destino), help=ajuda, on_click=navegar, args=(destino,))
    st.caption('Protótipo acadêmico. Validade e consumo simulados.')

{'Importação': pagina_base, 'Diagnóstico': pagina_diagnostico, 'Destinos': pagina_destinos}[pagina]()
