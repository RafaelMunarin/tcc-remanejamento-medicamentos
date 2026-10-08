"""Regras e preparação dos dados usadas no notebook e na interface."""
from io import BytesIO
import hashlib
import json
import re
import unicodedata
import numpy as np
import pandas as pd

PARAMETROS = {
    'referencia': '2026-06-09',
    'dias_mes': 30.0,
    'validade_min': 30,
    'validade_max': 540,
    'sal': 'TCC_ESTOQUE_20260609',
    'consumo_min': 5,
    'consumo_max': 120,
    'percentual_zero': 15,
}
DATA_REFERENCIA = pd.Timestamp(PARAMETROS['referencia'])
TOL = TOLERANCIA = 1e-8  # tolerância para arredondamento
CHAVE = ['id_unidade', 'id_medicamento']
CAMPOS_ESTOQUE = ['id_lote','id_unidade','id_medicamento','quantidade','validade']

# Interrompo a execução quando uma condição não é atendida.
def exigir(condicao, mensagem):
    if not bool(condicao):
        raise ValueError(mensagem)

def conferir_proximidade(obtido, esperado, mensagem):
    exigir(np.allclose(obtido, esperado, atol=TOLERANCIA, rtol=0, equal_nan=False), mensagem)

# Gero um número fixo para cada chave.
def hash_inteiro(*partes):
    # Uso JSON para separar os campos da chave.
    chave = json.dumps([str(p) for p in partes], ensure_ascii=False, separators=(",", ":"))
    return int(hashlib.sha256(chave.encode("utf-8")).hexdigest()[:16], 16)

# Confiro as faixas do gerador.
def validar_consumo_simulado(minimo, maximo, percentual_zero):
    exigir(all(isinstance(v, (int, np.integer)) and not isinstance(v, (bool, np.bool_))
               for v in [minimo, maximo, percentual_zero]), "Parâmetros de consumo devem ser inteiros.")
    exigir(0 < minimo <= maximo, "Faixa de consumo deve ser positiva e ordenada.")
    exigir(0 <= percentual_zero <= 100, "Percentual de consumo zero fora de 0–100.")

# Gero o consumo-base com os parâmetros definidos.
def gerar_consumo_base(grade, semente, minimo=5, maximo=120, percentual_zero=15):
    validar_consumo_simulado(minimo, maximo, percentual_zero)
    hashes = [hash_inteiro(semente, "consumo", c, p)
              for c, p in grade[["cnes", "codigo_produto"]].itertuples(index=False, name=None)]
    return np.array([0 if h % 100 < percentual_zero else minimo + (h // 100) % (maximo-minimo+1)
                     for h in hashes], dtype="int64")

def gerar_series_temporais(grade_base, semente, n_historico=6):
    """Gero o histórico sem consultar saldos ou resultados."""
    perfis = ['ESTAVEL', 'CRESCENTE', 'DECRESCENTE', 'INTERMITENTE', 'RUPTURA']
    registros = []
    for r in grade_base.sort_values(['id_unidade', 'id_medicamento']).itertuples(index=False):
        perfil = perfis[hash_inteiro(semente, 'perfil', r.cnes, r.codigo_produto) % len(perfis)]
        if r.quantidade_base_simulada == 0:
            perfil = 'ZERO'
        for t in range(-n_historico, 0):
            h = hash_inteiro(semente, 'ruido', r.cnes, r.codigo_produto, t)
            ruido = 0.75 + (h % 10001) / 10000 * 0.5
            fator = 1.0
            if perfil == 'CRESCENTE':
                fator = max(0.15, 1.0 + 0.015 * t)
            elif perfil == 'DECRESCENTE':
                fator = max(0.15, 1.0 - 0.015 * t)
            elif perfil == 'INTERMITENTE':
                fator = 0.0 if (h // 10001) % 100 < 60 else 2.5
            elif perfil == 'RUPTURA':
                # Nesta janela, RUPTURA usa o mesmo fator do perfil estável.
                fator = 1.0
            quantidade = int(np.rint(r.quantidade_base_simulada * fator * ruido))
            registros.append((int(r.id_unidade), int(r.id_medicamento), t, perfil, quantidade))
    return pd.DataFrame(registros, columns=['id_unidade', 'id_medicamento', 'indice_tempo',
                                          'perfil_simulado', 'quantidade_saida'])

def gerar_dados_experimentais(base, grade_original, parametros):
    """Gero validade e saídas com as mesmas chaves da base revisada."""
    p = parametros
    exigir(0 <= p['validade_min'] <= p['validade_max'], 'Faixa de validade inválida.')
    exigir(p['dias_mes'] > 0 and np.isfinite(p['dias_mes']), 'Dias por mês inválidos.')
    validar_consumo_simulado(p['consumo_min'], p['consumo_max'], p['percentual_zero'])
    exigir(isinstance(p['sal'], str) and bool(p['sal']), 'Sal do hash vazio.')
    estoque = base.copy()
    amplitude = p['validade_max'] - p['validade_min'] + 1
    dias = [p['validade_min'] + hash_inteiro(p['sal'], 'validade', produto, lote, codigo) % amplitude
            for produto, lote, codigo in estoque[['codigo_produto','lote','codigo_lote']].itertuples(index=False, name=None)]
    estoque['validade'] = pd.Timestamp(p['referencia']) + pd.to_timedelta(dias, unit='D')
    estoque = estoque.rename(columns={'id_estoque_lote':'id_lote', 'quantidade_estoque':'quantidade'})
    grade_local = grade_original.copy()
    grade_local['quantidade_base_simulada'] = gerar_consumo_base(grade_local, p['sal'],
        p['consumo_min'], p['consumo_max'], p['percentual_zero'])
    historico = gerar_series_temporais(grade_local, p['sal'], n_historico=6)
    periodos = pd.period_range(end=pd.Timestamp(p['referencia']).to_period('M')-1, periods=6)
    historico['periodo'] = historico.indice_tempo.map(dict(zip(range(-6,0), periodos.astype(str))))
    return estoque, historico, periodos

def calcular_cmm(historico, periodos):
    """Calculo a média dos seis meses completos."""
    campos = CHAVE + ['periodo', 'quantidade_saida']
    exigir(set(campos).issubset(historico), 'Histórico sem os campos necessários.')
    h = historico[campos].copy()
    h['periodo'] = h.periodo.astype(str)
    meses = [str(p) for p in periodos]
    exigir(len(meses) == 6 and len(set(meses)) == 6, 'São necessários seis meses distintos.')
    exigir(h[CHAVE].notna().all().all(), 'Histórico com identificação ausente.')
    exigir(not h.duplicated(CHAVE + ['periodo']).any(), 'Mês duplicado no histórico.')
    exigir(set(h.periodo) == set(meses), 'Histórico com mês ausente ou fora da janela.')
    h['quantidade_saida'] = pd.to_numeric(h.quantidade_saida, errors='raise')
    exigir(np.isfinite(h.quantidade_saida).all() and h.quantidade_saida.ge(0).all(),
           'Saída mensal deve ser finita e não negativa.')
    exigir(h.groupby(CHAVE).periodo.nunique().eq(6).all(), 'Combinação sem os seis meses.')
    return h.groupby(CHAVE, as_index=False).agg(
        cmm=('quantidade_saida', 'mean'), total_seis_meses=('quantidade_saida', 'sum'))

def validar_entradas(estoque, medias, referencia, dias_mes):
    exigir(set(CAMPOS_ESTOQUE).issubset(estoque), 'Estoque incompleto.')
    exigir(set(CHAVE + ['cmm']).issubset(medias), 'Tabela de CMM incompleta.')
    exigir(np.isfinite(dias_mes) and dias_mes > 0, 'Dias por mês inválidos.')
    exigir(not pd.isna(referencia), 'Data de referência ausente.')
    exigir(not medias.duplicated(CHAVE).any(), 'CMM duplicado.')
    exigir(medias[CHAVE].notna().all().all(), 'Identificador de CMM ausente.')
    exigir(np.isfinite(medias.cmm).all() and medias.cmm.ge(0).all(), 'CMM inválido.')
    exigir(estoque[['id_lote'] + CHAVE].notna().all().all(), 'Identificador de estoque ausente.')
    exigir(estoque.id_lote.is_unique, 'ID de lote duplicado.')
    exigir(np.isfinite(estoque.quantidade.to_numpy(dtype=float)).all() and estoque.quantidade.ge(0).all(), 'Saldo inválido.')
    exigir(pd.to_datetime(estoque.validade, errors='raise').notna().all(), 'Validade ausente.')
    pares = set(map(tuple, medias[CHAVE].to_numpy()))
    exigir(set(map(tuple, estoque[CHAVE].to_numpy())).issubset(pares),
           'Estoque sem CMM. Um dado ausente não pode ser convertido em zero.')

def organizar_grupos(estoque, medias):
    grupos = {tuple(chave): g.to_dict('records') for chave, g in estoque.groupby(CHAVE)}
    taxas = {(int(r.id_unidade), int(r.id_medicamento)): float(r.cmm)
             for r in medias.itertuples(index=False)}
    return grupos, taxas

def alocar_pvps(lotes, cmm, referencia, dias_mes=30.0):
    """Distribuo a capacidade pela ordem de vencimento."""
    acumulado = 0.0
    resultado = []
    for ordem, lote in enumerate(sorted(lotes, key=lambda r: (r['validade'], r['id_lote'])), 1):
        dias = (pd.Timestamp(lote['validade']) - pd.Timestamp(referencia)).days
        capacidade = cmm * max(0, dias) / dias_mes
        consumivel = min(lote['quantidade'], max(0.0, capacidade - acumulado))
        resultado.append(dict(lote, ordem_pvps=ordem, dias_ate_validade=dias,
            capacidade_acumulada=capacidade, consumo_anterior=acumulado,
            consumivel=consumivel, risco=lote['quantidade']-consumivel))
        acumulado += consumivel
    return resultado

def diagnosticar_lotes(estoque, medias, referencia, dias_mes=30.0):
    validar_entradas(estoque, medias, referencia, dias_mes)
    grupos, taxas = organizar_grupos(estoque, medias)
    linhas = []
    for chave, lotes in sorted(grupos.items()):
        linhas.extend(alocar_pvps(lotes, taxas[chave], referencia, dias_mes))
    campos = CAMPOS_ESTOQUE + ['ordem_pvps', 'dias_ate_validade',
        'capacidade_acumulada', 'consumo_anterior', 'consumivel', 'risco']
    return pd.DataFrame(linhas, columns=campos).astype({c: float for c in
        ['quantidade', 'capacidade_acumulada', 'consumo_anterior', 'consumivel', 'risco']})

def diagnosticar_combinacoes(estoque, medias, dias_mes=30.0):
    # Parto do histórico para manter as combinações sem estoque.
    saldos = estoque.groupby(CHAVE, as_index=False).quantidade.sum()
    tabela = medias.merge(saldos, on=CHAVE, how='left', validate='one_to_one')
    tabela['quantidade'] = tabela.quantidade.astype(float).fillna(0.0)
    tabela['cobertura_dias'] = np.nan
    positivo = tabela.cmm.gt(0)
    tabela.loc[positivo, 'cobertura_dias'] = (
        tabela.loc[positivo, 'quantidade'] / tabela.loc[positivo, 'cmm'] * dias_mes)
    tabela['situacao'] = np.select([
        tabela.quantidade.eq(0) & positivo,
        tabela.quantidade.gt(0) & ~positivo,
        tabela.quantidade.eq(0) & ~positivo], [
        'INDISPONIVEL_COM_CONSUMO', 'ESTOQUE_SEM_CONSUMO', 'SEM_ESTOQUE_SEM_CONSUMO'],
        default='COM_ESTOQUE_E_CONSUMO')
    return tabela

def capacidade_destino(proprios, cmm, validade_recebida, referencia, dias_mes=30.0):
    """Calculo quanto o destino pode receber sem aumentar seu risco."""
    prazo = max(0, (pd.Timestamp(validade_recebida) - pd.Timestamp(referencia)).days)
    diagnostico = alocar_pvps(proprios, cmm, referencia, dias_mes)
    prioritario = sum(r['consumivel'] for r in diagnostico if r['validade'] <= validade_recebida)
    livre = max(0.0, cmm * prazo / dias_mes - prioritario)
    # Preservo também o consumo dos lotes que vencem depois.
    folgas = [livre]
    for r in diagnostico:
        if r['validade'] > validade_recebida:
            folgas.append(max(0.0, r['capacidade_acumulada'] - r['consumo_anterior'] - r['consumivel']))
    return livre, min(folgas)

CAMPOS_CANDIDATAS = ['id_lote_origem', 'id_unidade_origem', 'id_medicamento', 'id_unidade_destino', 'cmm_destino', 'capacidade_livre', 'capacidade_sem_novo_risco', 'quantidade_admissivel', 'motivo']

def avaliar_candidatas(lote, risco, grupos, taxas, referencia, dias_mes=30.0):
    linhas = []
    prazo = (pd.Timestamp(lote['validade']) - pd.Timestamp(referencia)).days
    for (unidade, medicamento), cmm in sorted(taxas.items()):
        if medicamento != lote['id_medicamento'] or unidade == lote['id_unidade']:
            continue
        livre, segura = capacidade_destino(grupos.get((unidade, medicamento), []),
            cmm, lote['validade'], referencia, dias_mes)
        quantidade = max(0, int(np.floor(min(risco, segura) + TOL))) if prazo > 0 else 0
        if prazo <= 0:
            motivo = 'SEM_PRAZO_UTIL'
        elif cmm == 0:
            motivo = 'CMM_ZERO'
        elif quantidade == 0:
            motivo = 'CAPACIDADE_OU_RISCO_INFERIOR_A_UMA_UNIDADE'
        else:
            motivo = 'ADMISSIVEL'
        linhas.append({'id_lote_origem': lote['id_lote'],
            'id_unidade_origem': lote['id_unidade'], 'id_medicamento': medicamento,
            'id_unidade_destino': unidade, 'cmm_destino': cmm,
            'capacidade_livre': livre, 'capacidade_sem_novo_risco': segura,
            'quantidade_admissivel': quantidade, 'motivo': motivo})
    return sorted(linhas, key=lambda r: (-r['quantidade_admissivel'], -r['capacidade_livre'],
                                       r['id_unidade_destino']))

def candidatas_iniciais(estoque, medias, diagnostico, referencia, dias_mes=30.0):
    grupos, taxas = organizar_grupos(estoque, medias)
    linhas = []
    for lote in diagnostico.loc[diagnostico.risco.gt(TOL)].to_dict('records'):
        linhas.extend(avaliar_candidatas(lote, lote['risco'], grupos, taxas, referencia, dias_mes))
    return pd.DataFrame(linhas, columns=CAMPOS_CANDIDATAS)

def construir_plano(estoque, medias, referencia, dias_mes=30.0):
    """Atualizo os saldos após cada sugestão."""
    validar_entradas(estoque, medias, referencia, dias_mes)
    grupos, taxas = organizar_grupos(estoque[CAMPOS_ESTOQUE], medias)
    estado = [r for lotes in grupos.values() for r in lotes]
    originais = sorted(estado, key=lambda r: (r['validade'], r['id_medicamento'], r['id_lote']))
    novo_id = int(estoque.id_lote.max()) + 1 if len(estoque) else 1
    plano, alternativas = [], []
    etapa = 0
    for lote in originais:
        origem = (lote['id_unidade'], lote['id_medicamento'])
        while True:
            diag_origem = alocar_pvps(grupos[origem], taxas[origem], referencia, dias_mes)
            risco = next(r['risco'] for r in diag_origem if r['id_lote'] == lote['id_lote'])
            if risco + TOL < 1 or lote['validade'] <= referencia:
                break
            candidatas = avaliar_candidatas(lote, risco, grupos, taxas, referencia, dias_mes)
            etapa += 1
            alternativas.extend(dict(r, etapa=etapa) for r in candidatas)
            admissiveis = [r for r in candidatas if r['quantidade_admissivel'] > 0]
            if not admissiveis:
                break
            escolhida = admissiveis[0]
            destino = (escolhida['id_unidade_destino'], lote['id_medicamento'])
            quantidade = escolhida['quantidade_admissivel']
            consumo_antes = sum(r['consumivel'] for r in diag_origem)
            destino_antes = alocar_pvps(grupos.get(destino, []), taxas[destino], referencia, dias_mes)
            recebido = dict(lote, id_lote=novo_id, id_unidade=destino[0], quantidade=float(quantidade))
            lote['quantidade'] -= quantidade
            grupos.setdefault(destino, []).append(recebido)
            estado.append(recebido)
            origem_depois = alocar_pvps(grupos[origem], taxas[origem], referencia, dias_mes)
            destino_depois = alocar_pvps(grupos[destino], taxas[destino], referencia, dias_mes)
            plano.append(dict(escolhida, etapa=etapa, ordem_movimento=len(plano)+1,
                id_lote_recebido=novo_id, validade=lote['validade'], risco_antes=risco,
                consumo_origem_antes=consumo_antes,
                consumo_origem_depois=sum(r['consumivel'] for r in origem_depois),
                risco_destino_antes=sum(r['risco'] for r in destino_antes),
                risco_destino_depois=sum(r['risco'] for r in destino_depois)))
            novo_id += 1
    campos = CAMPOS_CANDIDATAS + ['etapa', 'ordem_movimento', 'id_lote_recebido',
        'validade', 'risco_antes', 'consumo_origem_antes', 'consumo_origem_depois',
        'risco_destino_antes', 'risco_destino_depois']
    return (pd.DataFrame(plano, columns=campos), pd.DataFrame(estado, columns=CAMPOS_ESTOQUE),
            pd.DataFrame(alternativas, columns=['etapa']+CAMPOS_CANDIDATAS))

def executar_cenario_base(base, grade_original, parametros):
    estoque, historico, periodos = gerar_dados_experimentais(base, grade_original, parametros)
    medias = calcular_cmm(historico, periodos)
    ref, dias = pd.Timestamp(parametros['referencia']), parametros['dias_mes']
    diagnostico = diagnosticar_lotes(estoque, medias, ref, dias)
    candidatas = candidatas_iniciais(estoque, medias, diagnostico, ref, dias)
    plano, final, alternativas = construir_plano(estoque, medias, ref, dias)
    return dict(estoque=estoque, historico=historico, medias=medias, diagnostico=diagnostico,
        combinacoes=diagnosticar_combinacoes(estoque, medias, dias), candidatas=candidatas,
        plano=plano, final=final, alternativas=alternativas)

def assinatura_tabela(tabela, chaves):
    """Comparo o conteúdo completo, sem arredondar os valores."""
    canonica = tabela.sort_values(chaves).reset_index(drop=True)
    texto = canonica.to_csv(index=False, lineterminator='\n', date_format='%Y-%m-%d', float_format='%.17g')
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

# Separo linhas vazias e rodapés conhecidos.
def separar_linhas_estoque(bruto):
    exigir("Produto - Código" in bruto.columns, "Código de produto ausente do cabeçalho.")
    valores = pd.to_numeric(bruto["Produto - Código"], errors="coerce")
    rotulos = bruto["Produto - Código"].fillna("").astype(str).str.strip()
    conhecidos = rotulos.str.fullmatch(r"Total de Registros:|IPM Sistemas Ltda|Atende\.Net - EST v:[0-9.]+")
    campos = [c for c in bruto if not str(c).startswith("Unnamed:") and c != "Produto - Código"]
    rodape = valores.isna() & conhecidos & bruto[campos].isna().all(axis=1)
    vazias = bruto.isna().all(axis=1)
    desconhecidas = valores.isna() & ~(rodape | vazias)
    exigir(not desconhecidas.any(), f"Linhas com produto inválido exigem revisão: {(bruto.index[desconhecidas]+5).tolist()[:20]}")
    removidas = bruto.loc[rodape | vazias].copy()
    removidas["linha_excel_origem"] = removidas.index + 5
    removidas["motivo_exclusao"] = np.where(vazias.loc[removidas.index], "LINHA_VAZIA", "RODAPE_RECONHECIDO")
    return bruto.loc[~(rodape | vazias)].copy(), removidas

# Padronizo os nomes das unidades.
def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor).strip().upper())
    return re.sub(r"\s+", " ", "".join(c for c in texto if not unicodedata.combining(c)))

def preparar_dados(cnes_bytes, estoque_bytes, parametros):
    """Leio as duas planilhas e mantenho o recorte definido no TCC."""
    df_cnes = pd.read_excel(BytesIO(cnes_bytes))
    df_estoque_bruto = pd.read_excel(BytesIO(estoque_bytes), header=3)
    DATA_REFERENCIA = pd.Timestamp(parametros['referencia'])

    # Confiro as colunas e retiro os rodapés.
    COLUNAS_ESTOQUE = ["Produto - Código", "Produto - Descrição", "Lote", "Código", "Lote - Código",
                      "Quantidade", "Estabelecimento - Nome", "Estabelecimento - Código",
                      "Grupo de Produto - Código", "Grupo de Produto - Descrição"]

    exigir(set(COLUNAS_ESTOQUE).issubset(df_estoque_bruto.columns), "Cabeçalho do estoque diferente do esperado.")
    df_estoque, df_linhas_excluidas = separar_linhas_estoque(df_estoque_bruto)
    administrativas_removidas = len(df_linhas_excluidas)

    # Confiro as colunas sem nome antes de removê-las.
    unnamed = [c for c in df_estoque.columns if str(c).startswith("Unnamed:")]
    exigir(df_estoque[unnamed].isna().all().all(), "Há conteúdo em colunas Unnamed: revisar o relatório.")
    df_estoque = df_estoque[COLUNAS_ESTOQUE].copy()

    # Guardo a linha de origem e renomeio as colunas.
    df_estoque["linha_excel_origem"] = df_estoque.index + 5
    df_estoque = df_estoque.rename(columns={
        "Produto - Código": "codigo_produto", "Produto - Descrição": "descricao_produto",
        "Lote": "lote", "Código": "codigo_registro_estoque", "Lote - Código": "codigo_lote",
        "Quantidade": "quantidade_estoque", "Estabelecimento - Nome": "nome_estabelecimento_portal",
        "Estabelecimento - Código": "codigo_estabelecimento",
        "Grupo de Produto - Código": "grupo_produto_codigo", "Grupo de Produto - Descrição": "grupo_produto_descricao"
    })

    # Converto os códigos e confiro se são válidos.
    for coluna in ["codigo_produto", "codigo_registro_estoque", "codigo_lote", "codigo_estabelecimento", "grupo_produto_codigo"]:
        valores = pd.to_numeric(df_estoque[coluna], errors="raise")
        exigir(valores.notna().all() and np.isfinite(valores).all() and (valores % 1 == 0).all(), f"Código inválido: {coluna}")
        df_estoque[coluna] = valores.astype("int64")

    df_estoque["quantidade_estoque"] = pd.to_numeric(df_estoque["quantidade_estoque"], errors="raise")

    # Defino o recorte de unidades e produtos.
    UNIDADES_SELECIONADAS = [
        "EAP ITOUPAVA", "ESF SILVIO SCHUTZ BAIRRO SUMARE", "PSF BARRA DO TROMBUDO",
        "PSF BARRAGEM CAIC", "PSF BELA ALIANCA", "PSF BOA VISTAEUGENIO SCHNEIDER",
        "PSF BREMER", "PSF BUDAG", "PSF CANOAS", "PSF CANTA GALO", "PSF FUNDO CANOAS",
        "PSF LARANJEIRAS", "PSF PAMPLONA", "PSF PROGRESSO", "PSF SANTA RITA", "PSF SANTANA", "PSF TABOAO"
    ]
    GRUPOS_MEDICAMENTOS = {6: "Medicamentos", 24: "MED PAI", 26: "MED ANTIBIOTICOS",
                          27: "MED BASICOS", 41: "TABAGISMO medicamentos e Insumos"}

    ordem = {normalizar_texto(nome): i for i, nome in enumerate(UNIDADES_SELECIONADAS, 1)}
    exigir(len(ordem) == len(UNIDADES_SELECIONADAS), "Unidades selecionadas repetidas.")

    # Padronizo os nomes nas duas fontes.
    exigir({"NOME FANTASIA", "CNES"}.issubset(df_cnes.columns), "Cabeçalho CNES inválido.")
    cnes_normalizado = df_cnes.assign(nome_normalizado=df_cnes["NOME FANTASIA"].map(normalizar_texto))
    cnes_sel = cnes_normalizado.loc[cnes_normalizado.nome_normalizado.isin(ordem), ["CNES", "NOME FANTASIA", "nome_normalizado"]].copy()
    portal = df_estoque[["codigo_estabelecimento", "nome_estabelecimento_portal"]].drop_duplicates().copy()
    portal["nome_normalizado"] = portal.nome_estabelecimento_portal.map(normalizar_texto)
    portal = portal.loc[portal.nome_normalizado.isin(ordem)]

    # Relaciono as fontes e confiro os identificadores.
    df_cadastro_unidades = cnes_sel.merge(portal, on="nome_normalizado", how="left", validate="one_to_one")
    exigir(set(df_cadastro_unidades.nome_normalizado) == set(ordem), "Uma ou mais unidades não foram localizadas no CNES.")
    exigir(df_cadastro_unidades.codigo_estabelecimento.notna().all(), "Unidade sem correspondência no estoque.")
    df_cadastro_unidades = df_cadastro_unidades.rename(columns={"CNES": "cnes", "NOME FANTASIA": "nome_unidade"})
    df_cadastro_unidades["id_unidade"] = df_cadastro_unidades.nome_normalizado.map(ordem).astype(int)

    for c in ["cnes", "codigo_estabelecimento"]:
        valores = pd.to_numeric(df_cadastro_unidades[c], errors="raise")
        exigir(valores.notna().all() and (valores % 1 == 0).all(), f"Identificador inválido: {c}")
        df_cadastro_unidades[c] = valores.astype("int64")
        exigir(df_cadastro_unidades[c].is_unique, f"Identificador duplicado: {c}")

    df_cadastro_unidades = df_cadastro_unidades[[
        "id_unidade", "cnes", "codigo_estabelecimento", "nome_unidade", "nome_estabelecimento_portal"
        ]].sort_values("id_unidade").reset_index(drop=True)

    # Seleciono os registros e confiro seus dados.
    selecionados = df_estoque.loc[
        df_estoque.codigo_estabelecimento.isin(df_cadastro_unidades.codigo_estabelecimento)
        & df_estoque.grupo_produto_codigo.isin(GRUPOS_MEDICAMENTOS)
    ].copy()

    exigir(len(selecionados) > 0, "Seleção sem registros.")
    exigir(selecionados[["lote", "descricao_produto", "grupo_produto_descricao"]].notna().all().all(), "Campos cadastrais ausentes.")
    selecionados["lote"] = selecionados.lote.astype(str)
    exigir(selecionados.lote.str.strip().ne("").all(), "Lote vazio.")
    exigir(np.isfinite(selecionados.quantidade_estoque).all() and selecionados.quantidade_estoque.gt(0).all(), "Estoque deve ser finito e positivo nesta extração.")
    exigir(selecionados.codigo_registro_estoque.is_unique, "Código de registro repetido: revisar antes de somar.")

    # Monto o catálogo de medicamentos.
    df_medicamentos = selecionados[[
        "codigo_produto", "descricao_produto", "grupo_produto_codigo", "grupo_produto_descricao"
        ]].drop_duplicates().sort_values("codigo_produto").reset_index(drop=True)

    exigir(df_medicamentos.codigo_produto.is_unique, "Produto com atributos cadastrais divergentes.")
    df_medicamentos.insert(0, "id_medicamento", np.arange(1, len(df_medicamentos) + 1))

    # Incluo os IDs de unidade e medicamento no estoque.
    df_registros_estoque = selecionados.merge(
        df_cadastro_unidades[["codigo_estabelecimento", "id_unidade"]], on="codigo_estabelecimento", validate="many_to_one"
    ).merge(df_medicamentos[["codigo_produto", "id_medicamento"]], on="codigo_produto", validate="many_to_one")

    # Agrupo os registros de cada lote.
    CHAVE_ANALITICA = ["id_unidade", "id_medicamento", "lote", "codigo_lote"]

    df_estoque_consolidado = df_registros_estoque.groupby(CHAVE_ANALITICA, as_index=False, dropna=False).agg(
        quantidade_estoque=("quantidade_estoque", "sum"),
        quantidade_registros_origem=("codigo_registro_estoque", "size")
    ).sort_values(CHAVE_ANALITICA).reset_index(drop=True)

    df_estoque_consolidado.insert(0, "id_estoque_lote", np.arange(1, len(df_estoque_consolidado) + 1))
    df_estoque_consolidado = df_estoque_consolidado.merge(df_medicamentos, on="id_medicamento", validate="many_to_one").merge(
        df_cadastro_unidades[["id_unidade", "cnes", "nome_unidade"]], on="id_unidade", validate="many_to_one"
        )
    df_estoque_consolidado["data_referencia_estoque"] = DATA_REFERENCIA
    df_estoque_consolidado["natureza_estoque"] = "PUBLICO_DERIVADO_POR_AGREGACAO"

    # Mantenho a ligação com as linhas da fonte.
    df_rastreabilidade = df_registros_estoque[CHAVE_ANALITICA + ["codigo_registro_estoque", "linha_excel_origem", "quantidade_estoque"]].merge(
        df_estoque_consolidado[CHAVE_ANALITICA + ["id_estoque_lote"]], on=CHAVE_ANALITICA, validate="many_to_one"
        )

    # Confiro se o agrupamento preservou as quantidades.
    exigir(not df_estoque_consolidado.duplicated(CHAVE_ANALITICA).any(), "Chave analítica duplicada após consolidação.")
    conferir_proximidade(df_estoque_consolidado.quantidade_estoque.sum(), df_registros_estoque.quantidade_estoque.sum(), "Soma de estoque alterada.")

    controle_antes = df_registros_estoque.groupby(["id_unidade", "id_medicamento"]).quantidade_estoque.sum().sort_index()
    controle_depois = df_estoque_consolidado.groupby(["id_unidade", "id_medicamento"]).quantidade_estoque.sum().sort_index()

    exigir(controle_antes.index.equals(controle_depois.index), "Combinações alteradas na consolidação.")
    conferir_proximidade(controle_antes, controle_depois, "Estoque alterado por unidade–medicamento.")

    # Incluo todas as combinações, mesmo sem estoque.
    grade = df_cadastro_unidades[["id_unidade", "cnes"]].merge(
        df_medicamentos[["id_medicamento", "codigo_produto"]], how="cross"
        )

    return dict(base=df_estoque_consolidado, grade=grade, unidades=df_cadastro_unidades,
                medicamentos=df_medicamentos, rastreabilidade=df_rastreabilidade)


def executar_modelo(cnes_bytes, estoque_bytes):
    """Executo a rede inteira antes de aplicar filtros de consulta."""
    parametros = dict(PARAMETROS)
    base = preparar_dados(cnes_bytes, estoque_bytes, parametros)
    resultado = executar_cenario_base(base['base'], base['grade'], parametros)
    exigir(resultado['estoque'].groupby(['codigo_produto','lote','codigo_lote'])
           .validade.nunique().eq(1).all(), 'Mesmo lote com validades diferentes.')
    return dict(resultado=resultado, cadastro=base, parametros=parametros,
        fontes_sha256={'CNES.xlsx':hashlib.sha256(cnes_bytes).hexdigest(),
                      'Consulta de Estoque.xlsx':hashlib.sha256(estoque_bytes).hexdigest()})


def tabelas_apresentacao(execucao):
    """Acrescento os nomes para facilitar a consulta."""
    r, cadastro = execucao['resultado'], execucao['cadastro']
    unidades = cadastro['unidades'].set_index('id_unidade').nome_unidade
    medicamentos = cadastro['medicamentos'].set_index('id_medicamento').descricao_produto
    lotes = r['estoque'].set_index('id_lote').lote
    diagnostico = r['diagnostico'].merge(r['medias'], on=CHAVE, validate='many_to_one')
    diagnostico['unidade'] = diagnostico.id_unidade.map(unidades)
    diagnostico['medicamento'] = diagnostico.id_medicamento.map(medicamentos)
    diagnostico['lote'] = diagnostico.id_lote.map(lotes)
    envios = r['plano'].groupby('id_lote_origem').quantidade_admissivel.sum()
    diagnostico['quantidade_sugerida'] = diagnostico.id_lote.map(envios).fillna(0).astype(int)
    plano = r['plano'].copy()
    plano['origem'] = plano.id_unidade_origem.map(unidades)
    plano['destino'] = plano.id_unidade_destino.map(unidades)
    plano['medicamento'] = plano.id_medicamento.map(medicamentos)
    plano['lote'] = plano.id_lote_origem.map(lotes)
    combinacoes = r['combinacoes'].copy()
    combinacoes['unidade'] = combinacoes.id_unidade.map(unidades)
    combinacoes['medicamento'] = combinacoes.id_medicamento.map(medicamentos)
    return diagnostico, plano, combinacoes
