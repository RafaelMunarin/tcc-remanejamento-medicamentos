"""Confiro se o núcleo da interface mantém os resultados do notebook."""
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import json

import pandas as pd
import modelo

PASTA = Path(__file__).resolve().parent


def verificar():
    notebook = json.loads((PASTA/'modelo_remanejamento_tcc_rafael.ipynb').read_text(encoding='utf-8'))
    ambiente = {'__name__':'__main__', 'display':lambda *args:None,
        'PASTA_DADOS':PASTA/'dados', 'ARQUIVOS':['CNES.xlsx','Consulta de Estoque.xlsx']}
    # Executo a preparação e o cálculo do notebook sem pedir upload.
    with redirect_stdout(StringIO()):
        for indice, celula in enumerate(notebook['cells']):
            if celula['cell_type']=='code' and indice<=59 and indice not in (3,10):
                exec(compile(''.join(celula['source']), f'notebook_celula_{indice}', 'exec'), ambiente)
    esperado = ambiente['resultado']
    execucao = modelo.executar_modelo((PASTA/'dados'/'CNES.xlsx').read_bytes(),
                                     (PASTA/'dados'/'Consulta de Estoque.xlsx').read_bytes())
    obtido = execucao['resultado']
    for nome in esperado:
        pd.testing.assert_frame_equal(esperado[nome], obtido[nome], check_exact=True)
        print('Tabela idêntica:', nome)

    # Aplico os cenários do notebook às funções usadas no Streamlit.
    for nome in ['calcular_cmm','diagnosticar_lotes','diagnosticar_combinacoes',
                 'candidatas_iniciais','construir_plano','alocar_pvps','avaliar_candidatas',
                 'organizar_grupos','capacidade_destino']:
        ambiente[nome]=getattr(modelo,nome)
    with redirect_stdout(StringIO()):
        for indice in [63,65,66,68,69,70]:
            exec(compile(''.join(notebook['cells'][indice]['source']),
                         f'notebook_celula_{indice}', 'exec'), ambiente)
    resumo=ambiente['resumo_cenarios']
    assert len(resumo)==18 and resumo.conforme.all(), 'Divergência nos cenários.'
    invariantes=ambiente['verificar_invariantes'](
        obtido['estoque'], obtido['medias'], obtido['diagnostico'], obtido['candidatas'],
        obtido['plano'], obtido['final'], modelo.DATA_REFERENCIA, modelo.PARAMETROS['dias_mes'])
    assert len(invariantes)==17 and invariantes.conforme.all(), 'Divergência nos invariantes.'
    diagnostico, plano, combinacoes=modelo.tabelas_apresentacao(execucao)
    assert len(diagnostico)==len(obtido['diagnostico'])
    assert len(plano)==len(obtido['plano'])
    assert len(combinacoes)==len(obtido['combinacoes'])
    assert diagnostico[['unidade','medicamento','lote']].notna().all().all()
    assert plano[['origem','destino','medicamento','lote']].notna().all().all()
    print('18 cenários conformes; 17 invariantes conformes.')
    print('Integração verificada: as nove tabelas são idênticas às do notebook.')


if __name__=='__main__':
    verificar()
