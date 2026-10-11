"""Comparo a exportação com os valores já calculados e preservados da planilha."""
import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exportacao', type=Path, help='Pasta dos CSVs ou Resultados_Modelo_Final.zip')
    parser.add_argument('--ambiente', choices=['local', 'colab'], required=True)
    parser.add_argument('--saida', type=Path, default=Path('conferencia_comparada'))
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    referencia = base / 'esperados_planilha.json'
    assinatura = hashlib.sha256(referencia.read_bytes()).hexdigest()
    assert assinatura == (base / 'esperados_planilha.sha256').read_text().strip(), 'Referência da planilha alterada.'
    esperado = json.loads(referencia.read_text(encoding='utf-8'))
    pacote = zipfile.ZipFile(args.exportacao) if args.exportacao.is_file() else None

    def ler_bytes(nome):
        if pacote:
            return pacote.read(nome)
        return (args.exportacao / nome).read_bytes()

    def ler_csv(nome):
        return list(csv.DictReader(io.StringIO(ler_bytes(nome).decode('utf-8-sig'))))

    for nome, sha in esperado['fontes_sha256'].items():
        assert hashlib.sha256(ler_bytes(nome)).hexdigest() == sha, (
            f'Entrada diferente: {nome}. Não comparar esta amostra com outra base.')
    lotes = {r['id_lote']: r for r in ler_csv('diagnostico_lotes.csv')}
    combinacoes = {f"{r['id_unidade']}|{r['id_medicamento']}": r for r in ler_csv('diagnostico_combinacoes.csv')}
    candidatas = {f"{r['id_lote_origem']}|{r['id_unidade_destino']}": r for r in ler_csv('candidatas_iniciais.csv')}
    plano = [r for r in ler_csv('plano_remanejamento.csv') if int(r['id_medicamento']) == esperado['medicamento_plano']]
    ordens = [int(r['ordem_movimento']) for r in plano]
    assert ordens == sorted(set(ordens)), 'A sequência original do plano foi alterada ou duplicada.'
    for i, r in enumerate(plano, 1):
        r['ordem_no_medicamento'] = i

    def valor_obtido(registro):
        tipo, chave, campo = registro['tipo'], registro['chave'], registro['campo']
        if tipo == 'plano_total':
            return len(plano)
        if tipo == 'lote':
            linha = lotes.get(chave, {})
            if campo == 'cmm' and linha:
                linha = combinacoes.get(f"{linha['id_unidade']}|{linha['id_medicamento']}", {})
        elif tipo == 'combinacao':
            linha = combinacoes.get(chave, {})
        elif tipo == 'capacidade':
            linha = candidatas.get(chave, {})
        else:
            indice = int(chave) - 1
            linha = plano[indice] if indice < len(plano) else {}
        return linha.get(campo)

    comparacoes = []
    for registro in esperado['comparacoes']:
        valor = valor_obtido(registro)
        e = registro['esperado']
        # Saldos inteiros também exigem correspondência exata.
        regra_exata = registro['exato'] or (
            registro['campo'] == 'quantidade' and isinstance(e, (int, float))
            and float(e).is_integer())
        if isinstance(e, (int, float)) and not isinstance(e, bool) and valor is not None:
            try:
                valor = float(valor)
                if not math.isfinite(valor):
                    valor = None
                elif regra_exata and valor.is_integer():
                    valor = int(valor)
            except (TypeError, ValueError):
                valor = None
        diferenca = abs(valor - e) if isinstance(e, (int, float)) and isinstance(valor, (int, float)) else None
        coincide = valor is not None and (valor == e if regra_exata else diferenca is not None and diferenca <= esperado['tolerancia'])
        comparacoes.append(dict(registro, exato=regra_exata, obtido=valor, diferenca=diferenca,
            conforme=coincide, causa='' if coincide else 'PENDENTE DE INVESTIGAÇÃO'))
    reproducao = ler_csv('reprodutibilidade.csv')
    repeticao_ok = len(reproducao) == 9 and all(r['situacao'] == 'SESSAO_DISTINTA' and r['resultado_identico'].lower() == 'true' for r in reproducao)
    resumo = {
        'comparado_em_utc': datetime.now(timezone.utc).isoformat(),
        'ambiente_informado': args.ambiente,
        'esperados_sha256': assinatura,
        'coincidiram': sum(r['conforme'] for r in comparacoes),
        'total': len(comparacoes),
        'divergencias': sum(not r['conforme'] for r in comparacoes),
        'nove_tabelas_identicas_em_sessoes_distintas': repeticao_ok,
        'revisao_humana': 'PENDENTE',
        'limite': 'Comparação automatizada de apoio; não comprova revisão humana. O ambiente informado não é detectado pelo script.',
        'comparacoes': comparacoes,
    }
    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / 'conferencia.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding='utf-8')
    with (args.saida / 'conferencia_campos.csv').open('w', encoding='utf-8-sig', newline='') as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=list(comparacoes[0]))
        writer.writeheader()
        writer.writerows(comparacoes)
    print(f"{resumo['coincidiram']} de {resumo['total']} conferências de campos coincidiram ({args.ambiente}).")
    print('Revisão humana: PENDENTE. Reprodutibilidade da exportação:', repeticao_ok)
    if resumo['divergencias']:
        print('Registre a causa de cada divergência antes de encerrar a conferência.')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
