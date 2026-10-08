"""Consulta da base, diagnóstico e comparação dos destinos."""
from io import BytesIO
from pathlib import Path
import json
import zipfile

import streamlit as st

from modelo import PARAMETROS, TOL, preparar_dados, executar_modelo, tabelas_apresentacao
from visual import (configurar, numero, cabecalho, resumo, lote_card,
                    destino_indicado, alternativa_card, tabela)

PASTA=Path(__file__).resolve().parent
PAGINAS=['Importação','Diagnóstico','Sugestões de destino']
configurar()
st.session_state.setdefault('navegacao','Importação')


def liberada(pagina):
    if pagina=='Diagnóstico':
        return 'base_ativa' in st.session_state
    if pagina=='Sugestões de destino':
        return 'base_ativa' in st.session_state and 'execucao' in st.session_state
    return pagina in PAGINAS


def navegar(pagina,lote=None):
    if not liberada(pagina):
        return
    st.session_state['navegacao']=pagina
    if lote is not None:
        st.session_state['lote_foco']=int(lote)


def limpar_base():
    # Uma troca de arquivos invalida a análise anterior.
    for nome in ['base_ativa','execucao','consulta','lote_foco','resultado_zip',
                 '_erro_importacao','_erro_diagnostico']:
        st.session_state.pop(nome,None)
    for nome in list(st.session_state):
        if nome.startswith(('_base_','_diag_','_sug_','_lote_','_etapa_')):
            st.session_state.pop(nome,None)


def exigir_base():
    if 'base_ativa' in st.session_state:
        return True
    st.info('Importe a planilha de estoque para continuar.')
    st.button('Abrir importação',type='primary',on_click=navegar,args=('Importação',))
    return False


def exigir_diagnostico():
    if not exigir_base():
        return False
    if 'execucao' in st.session_state:
        return True
    st.info('A base já está pronta. Execute o diagnóstico para comparar os destinos.')
    st.button('Ir para o diagnóstico',type='primary',on_click=navegar,args=('Diagnóstico',))
    return False


def nomes():
    cadastro=st.session_state['base_ativa']['cadastro']
    unidades=cadastro['unidades'].set_index('id_unidade').nome_unidade.to_dict()
    medicamentos=cadastro['medicamentos'].set_index('id_medicamento').descricao_produto.to_dict()
    return unidades,medicamentos


def escolher_recorte(prefixo):
    unidades,medicamentos=nomes()
    anterior=st.session_state.get('consulta',{'modo':'Rede completa','unidade':None,'medicamento':None})
    modos=['Rede completa','Por unidade','Por medicamento']
    a,b=st.columns([1.1,1.8])
    modo=a.selectbox('Como deseja consultar?',modos,index=modos.index(anterior['modo']),
                     key=prefixo+'_modo')
    unidade=medicamento=None
    if modo=='Por unidade':
        opcoes=list(unidades)
        indice=opcoes.index(anterior['unidade']) if anterior['unidade'] in opcoes else 0
        unidade=b.selectbox('Selecione a unidade',opcoes,index=indice,
                            format_func=unidades.get,key=prefixo+'_unidade')
    elif modo=='Por medicamento':
        opcoes=list(medicamentos)
        indice=opcoes.index(anterior['medicamento']) if anterior['medicamento'] in opcoes else 0
        medicamento=b.selectbox('Selecione o medicamento',opcoes,index=indice,
                                format_func=lambda x:f'{medicamentos[x]} · ID {x}',key=prefixo+'_medicamento')
    consulta=dict(modo=modo,unidade=unidade,medicamento=medicamento)
    st.session_state['consulta']=consulta
    return consulta


def filtrar(dados,consulta,campo_unidade='id_unidade'):
    if consulta['unidade'] is not None:
        dados=dados.loc[dados[campo_unidade].eq(consulta['unidade'])]
    if consulta['medicamento'] is not None:
        dados=dados.loc[dados.id_medicamento.eq(consulta['medicamento'])]
    return dados


def exportar(execucao):
    d,p,c=tabelas_apresentacao(execucao)
    tabelas={'diagnostico_lotes':d,'plano_remanejamento':p,'diagnostico_combinacoes':c,
             'alternativas_decisoes':execucao['resultado']['alternativas']}
    arquivo=BytesIO()
    with zipfile.ZipFile(arquivo,'w',zipfile.ZIP_DEFLATED) as z:
        for nome,t in tabelas.items():
            z.writestr(nome+'.csv',t.to_csv(index=False).encode('utf-8-sig'))
        contexto={'parametros':execucao['parametros'],'fontes_sha256':execucao['fontes_sha256']}
        z.writestr('contexto.json',json.dumps(contexto,ensure_ascii=False,indent=2))
    return arquivo.getvalue()


def pagina_base():
    cabecalho('Importação','Envie a planilha de estoque e confira os dados por unidade.')
    arquivo=st.file_uploader('Planilha de estoque (.xlsx)',type=['xlsx'],key='_estoque',on_change=limpar_base)
    if st.button('Importar planilha',type='primary',disabled=arquivo is None):
        limpar_base()
        try:
            with st.spinner('Organizando a planilha...'):
                cnes=(PASTA/'dados'/'CNES.xlsx').read_bytes()
                estoque=arquivo.getvalue()
                cadastro=preparar_dados(cnes,estoque,dict(PARAMETROS))
            st.session_state['base_ativa']=dict(cadastro=cadastro,cnes=cnes,estoque=estoque,
                                               arquivo=arquivo.name)
        except Exception as erro:
            st.session_state['_erro_importacao']=str(erro)
        st.rerun()
    if '_erro_importacao' in st.session_state:
        st.error('Não foi possível importar a base. Confira o motivo e tente novamente.')
        st.write(st.session_state['_erro_importacao'])
    with st.expander('Como importar a planilha?'):
        st.write('Selecione o relatório Consulta de Estoque no formato do arquivo abaixo e clique em '
                 '**Importar planilha**. Mantenha o cabeçalho na quarta linha e os nomes das colunas.')
        st.write('A limpeza e a normalização são automáticas. O cadastro das unidades já está no aplicativo; '
                 'o recorte de unidades e medicamentos é o definido no TCC.')
        exemplo=PASTA/'dados'/'Consulta de Estoque.xlsx'
        if exemplo.exists():
            st.download_button('Baixar planilha do experimento',data=exemplo.read_bytes(),
                               file_name=exemplo.name,mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    if 'base_ativa' not in st.session_state:
        return
    cadastro=st.session_state['base_ativa']['cadastro']
    st.divider()
    st.subheader('Estoque disponível para consulta')
    st.caption('Arquivo importado: '+st.session_state['base_ativa']['arquivo'])
    unidades,_=nomes()
    a,b=st.columns([1,1.5])
    unidade=a.selectbox('Filtrar por unidade',[None]+list(unidades),
                        format_func=lambda x:'Todas as unidades' if x is None else unidades[x],key='_base_unidade')
    busca=b.text_input('Buscar medicamento',placeholder='Digite parte do nome',key='_base_busca')
    base=cadastro['base']
    if unidade is not None:base=base.loc[base.id_unidade.eq(unidade)]
    if busca.strip():base=base.loc[base.descricao_produto.str.contains(busca.strip(),case=False,regex=False)]
    resumo([('Unidades na consulta',base.id_unidade.nunique()),('Medicamentos',base.id_medicamento.nunique()),
            ('Lotes',len(base))])
    st.caption('Saldos consolidados da planilha importada.')
    tabela(base,{'descricao_produto':'Medicamento','quantidade_estoque':'Saldo','lote':'Lote',
                 'nome_unidade':'Unidade'},decimais=['quantidade_estoque'],altura=340)
    if base.empty:st.info('Nenhum registro atende aos filtros.')
    st.button('Seguir para o diagnóstico',type='primary',on_click=navegar,args=('Diagnóstico',))


def pagina_diagnostico():
    cabecalho('Diagnóstico','Consulte os lotes em risco por unidade, medicamento ou em toda a rede.')
    if not exigir_base():return
    consulta=escolher_recorte('_diag')
    st.caption('O cálculo considera toda a rede. Os filtros alteram apenas a consulta.')
    pronto='execucao' in st.session_state
    if st.button('Atualizar diagnóstico' if pronto else 'Executar diagnóstico',type='primary'):
        ativa=st.session_state['base_ativa']
        st.session_state.pop('_erro_diagnostico',None)
        try:
            with st.spinner('Calculando os riscos e a capacidade das unidades...'):
                resultado=executar_modelo(ativa['cnes'],ativa['estoque'])
                pacote=exportar(resultado)
            st.session_state['execucao']=resultado
            st.session_state['resultado_zip']=pacote
        except Exception as erro:
            st.session_state.pop('execucao',None)
            st.session_state.pop('resultado_zip',None)
            st.session_state['_erro_diagnostico']=str(erro)
        st.rerun()
    if '_erro_diagnostico' in st.session_state:
        st.error('Não foi possível concluir o diagnóstico.')
        st.write(st.session_state['_erro_diagnostico'])
    if 'execucao' not in st.session_state:return
    d,plano,combinacoes=tabelas_apresentacao(st.session_state['execucao'])
    dados=filtrar(d,consulta)
    risco=dados.loc[dados.risco.gt(TOL)]
    sugeridos=set(plano.id_lote_origem)
    com_destino=int(risco.id_lote.isin(sugeridos).sum())
    st.divider()
    resumo([('Lotes em risco',len(risco)),('Com sugestão de envio',com_destino),
            ('Sem sugestão de envio',len(risco)-com_destino)])
    st.caption('Contagens do recorte selecionado. Um lote com envio sugerido ainda pode manter risco residual.')
    apenas_risco=st.toggle('Mostrar somente lotes em risco',value=True,key='_apenas_risco')
    visiveis=(risco if apenas_risco else dados).sort_values(['validade','id_lote'])
    if visiveis.empty:
        st.info('Nenhum lote atende a este recorte. Desative o filtro de risco para consultar os demais lotes.')
    else:
        por_id=visiveis.set_index('id_lote')
        escolhido=st.selectbox('Escolha um lote para analisar',visiveis.id_lote.tolist(),
            format_func=lambda x:f'{por_id.loc[x,"medicamento"]} · lote {por_id.loc[x,"lote"]} · {por_id.loc[x,"unidade"]}',
            key='_lote_diagnostico')
        lote=visiveis.loc[visiveis.id_lote.eq(escolhido)].iloc[0]
        lote_card(lote)
        with st.expander('Como esse risco foi calculado?'):
            st.write(f'CMM **{numero(lote.cmm,2)}** × **{numero(lote.dias_ate_validade)} dias** '
                     f'÷ **{numero(PARAMETROS["dias_mes"])} dias por mês** define a capacidade acumulada até a validade.')
            st.write(f'Capacidade até a validade: **{numero(lote.capacidade_acumulada,2)}**. '
                     f'Consumo reservado aos lotes anteriores: **{numero(lote.consumo_anterior,2)}**.')
            st.write(f'Saldo **{numero(lote.quantidade,2)}** − quantidade utilizável '
                     f'**{numero(lote.consumivel,2)}** = risco **{numero(lote.risco,2)}**.')
            st.caption('PVPS significa Primeiro que Vence, Primeiro que Sai. O CMM é a média dos seis meses completos.')
            st.caption('O risco é uma quantidade calculada nas premissas do experimento, não uma perda confirmada.')
        if lote.risco>TOL:
            st.button('Ver destinos deste lote',type='primary',on_click=navegar,
                      args=('Sugestões de destino',int(escolhido)))
    with st.expander(f'Ver os {numero(len(visiveis))} lotes desta consulta'):
        tabela(visiveis,{'medicamento':'Medicamento','risco':'Em risco','quantidade':'Saldo',
            'quantidade_sugerida':'Envio sugerido','validade':'Validade sintética','unidade':'Unidade','lote':'Lote'},
            inteiros=['quantidade_sugerida'],decimais=['risco','quantidade'])
    sem_estoque=filtrar(combinacoes,consulta)
    sem_estoque=sem_estoque.loc[sem_estoque.situacao.eq('INDISPONIVEL_COM_CONSUMO')]
    if not sem_estoque.empty:
        with st.expander(f'Sem estoque e com consumo sintético: {numero(len(sem_estoque))} combinações'):
            tabela(sem_estoque,{'medicamento':'Medicamento','unidade':'Unidade','cmm':'CMM sintético'},decimais=['cmm'])
    st.download_button('Baixar diagnóstico da rede completa',data=st.session_state['resultado_zip'],
                        file_name='Resultados_Streamlit.zip',mime='application/zip')


def motivo_escolha(alternativas,movimento):
    mesma_quantidade=alternativas.loc[alternativas.quantidade_admissivel.eq(movimento.quantidade_admissivel)]
    if len(mesma_quantidade)==1:
        return 'Entre os destinos comparados, é o que pode receber a maior quantidade nesta etapa.'
    mesma_capacidade=mesma_quantidade.loc[mesma_quantidade.capacidade_livre.eq(movimento.capacidade_livre)]
    if len(mesma_capacidade)==1:
        return ('Outras unidades recebem a mesma quantidade, mas esta tem a maior capacidade livre '
                f'até a validade: {numero(movimento.capacidade_livre,2)}.')
    return ('Houve empate na quantidade e na capacidade livre. O desempate usa o menor ID da unidade: '
            f'{int(movimento.id_unidade_destino)}.')


def mostrar_comparacao(alternativas,unidades,escolhida=None):
    alternativas=alternativas.copy()
    alternativas['destino']=alternativas.id_unidade_destino.map(unidades)
    alternativas['situacao']=alternativas.motivo.replace({
        'ADMISSIVEL':'Pode receber','CMM_ZERO':'Consumo médio zero','SEM_PRAZO_UTIL':'Sem prazo útil',
        'CAPACIDADE_OU_RISCO_INFERIOR_A_UMA_UNIDADE':'Capacidade ou risco abaixo de 1 unidade'})
    if escolhida is not None:
        alternativas.loc[alternativas.id_unidade_destino.eq(escolhida),'situacao']='Indicada nesta etapa'
    tabela(alternativas,{'destino':'Destino','quantidade_admissivel':'Pode receber','capacidade_livre':'Capacidade livre',
                         'capacidade_sem_novo_risco':'Sem novo risco','situacao':'Situação'},
                         inteiros=['quantidade_admissivel'],decimais=['capacidade_livre','capacidade_sem_novo_risco'])


def pagina_sugestoes():
    cabecalho('Sugestões de destino','Compare as unidades que podem receber o lote selecionado.')
    if not exigir_diagnostico():return
    consulta=escolher_recorte('_sug')
    execucao=st.session_state['execucao']
    d,plano,_=tabelas_apresentacao(execucao)
    risco=filtrar(d,consulta)
    risco=risco.loc[risco.risco.gt(TOL)].sort_values(['validade','id_lote'])
    if risco.empty:
        st.info('Nenhum lote em risco neste recorte.')
        return
    por_id=risco.set_index('id_lote')
    opcoes=risco.id_lote.tolist()
    foco=st.session_state.pop('lote_foco',None)
    if foco in opcoes:
        st.session_state['_lote_sugestao']=foco
    elif st.session_state.get('_lote_sugestao') not in opcoes:
        st.session_state['_lote_sugestao']=opcoes[0]
    id_lote=st.selectbox('Qual lote deseja remanejar?',opcoes,
        format_func=lambda x:f'{por_id.loc[x,"medicamento"]} · lote {por_id.loc[x,"lote"]} · {por_id.loc[x,"unidade"]}',
        key='_lote_sugestao')
    lote=risco.loc[risco.id_lote.eq(id_lote)].iloc[0]
    st.caption(f'Origem: {lote.unidade} · Validade sintética: {lote.validade:%d/%m/%Y} · '
               f'Risco inicial: {numero(lote.risco,2)} unidades')
    unidades,_=nomes()
    envios=plano.loc[plano.id_lote_origem.eq(id_lote)]
    if envios.empty:
        st.info('Este lote tem risco potencial, mas não tem envio admissível no plano.')
        r=execucao['resultado']
        alternativas=r['alternativas'].loc[r['alternativas'].id_lote_origem.eq(id_lote)]
        if not alternativas.empty:
            alternativas=alternativas.loc[alternativas.etapa.eq(alternativas.etapa.max())]
        else:
            alternativas=r['candidatas'].loc[r['candidatas'].id_lote_origem.eq(id_lote)]
        if lote.dias_ate_validade<=0:st.write('Não há prazo útil para consumo antes do vencimento.')
        elif lote.risco+TOL<1:st.write('O risco é inferior a uma unidade inteira, que é o mínimo para sugerir um envio.')
        else:st.write('Nenhuma unidade tem capacidade disponível para receber ao menos uma unidade sem aumentar seu próprio risco nessa etapa.')
        with st.expander('Entender as unidades descartadas'):
            mostrar_comparacao(alternativas,unidades)
        return
    if len(envios)>1:
        st.caption(f'Este lote tem {len(envios)} envios sugeridos. Cada etapa usa a capacidade restante após as anteriores.')
        ordens=envios.ordem_movimento.tolist()
        envio=st.selectbox('Qual etapa deseja comparar?',ordens,
            format_func=lambda x:f'Envio {ordens.index(x)+1} de {len(ordens)} · sugestão {x}',key='_etapa_envio')
        m=envios.loc[envios.ordem_movimento.eq(envio)].iloc[0]
    else:m=envios.iloc[0]
    alternativas=execucao['resultado']['alternativas']
    alternativas=alternativas.loc[alternativas.etapa.eq(m.etapa)]
    destino_indicado(m.destino,m.quantidade_admissivel,motivo_escolha(alternativas,m),
                      m.risco_antes,m.capacidade_sem_novo_risco)
    outras=alternativas.loc[(alternativas.id_unidade_destino!=m.id_unidade_destino)
                            & alternativas.quantidade_admissivel.gt(0)]
    if outras.empty:
        st.write('**Só esta unidade atende às regras nesta etapa.**')
    else:
        st.subheader('Outras possibilidades')
        st.caption('Comparação isolada nessa etapa. As quantidades abaixo não devem ser somadas como novos envios.')
        for coluna,(_,opcao) in zip(st.columns(min(3,len(outras))),outras.head(3).iterrows()):
            if opcao.quantidade_admissivel<m.quantidade_admissivel:
                motivo='Recebe uma quantidade menor nesta etapa.'
            elif opcao.capacidade_livre<m.capacidade_livre:
                motivo='Mesma quantidade, com menor capacidade livre.'
            else:motivo='Empate resolvido pelo menor ID da unidade.'
            with coluna:
                alternativa_card(unidades[opcao.id_unidade_destino],opcao.quantidade_admissivel,
                                  opcao.capacidade_sem_novo_risco,motivo)
    with st.expander(f'Ver todas as {len(alternativas)} unidades comparadas'):
        mostrar_comparacao(alternativas,unidades,m.id_unidade_destino)
    with st.expander('Como a quantidade e o destino foram definidos?'):
        st.write(f'Menor valor entre risco ({numero(m.risco_antes,2)}) e capacidade sem novo risco '
                 f'({numero(m.capacidade_sem_novo_risco,2)}), arredondado para baixo: '
                 f'**{numero(m.quantidade_admissivel)} unidades**.')
        st.write('Ordem de escolha: maior quantidade admissível; depois, maior capacidade livre; '
                 'persistindo o empate, menor ID da unidade. A escolha considera o estado da rede naquela etapa.')
        st.caption('A escolha é feita em sequência, sem buscar a melhor combinação global de envios.')


if not liberada(st.session_state['navegacao']):
    st.session_state['navegacao']='Importação'
pagina=st.session_state['navegacao']
with st.sidebar:
    st.markdown('<div class="sidebar-brand"><span class="health-mark">+</span>'
        '<div><b>Remanejamento</b><small>de medicamentos</small></div></div>',unsafe_allow_html=True)
    rotulos=['1 · Importação','2 · Diagnóstico','3 · Sugestões de destino']
    for destino,rotulo in zip(PAGINAS,rotulos):
        ajuda=None
        if not liberada(destino):
            ajuda='Importe a planilha primeiro.' if destino=='Diagnóstico' else 'Conclua o diagnóstico primeiro.'
        st.button(rotulo,key='nav_'+destino,type='primary' if pagina==destino else 'secondary',
                  width='stretch',disabled=not liberada(destino),help=ajuda,
                  on_click=navegar,args=(destino,))
    st.divider()
    st.caption('Referência · 09/06/2026')

{'Importação':pagina_base,'Diagnóstico':pagina_diagnostico,
 'Sugestões de destino':pagina_sugestoes}[pagina]()
st.markdown('<div class="app-footer">TCC · Rafael Munarin · Validade e consumo sintéticos. '
            'As sugestões apoiam a decisão e não executam transferências.</div>',unsafe_allow_html=True)
