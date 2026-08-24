"""Compara dois artefatos de experimento e exige igualdade TRADE A TRADE.

Ferramenta de prova para mudanças que devem ser NULAS (refatorações de
performance, reorganização de código): re-rodar uma config conhecida e exigir
que o `exp_{hash}.json` saia idêntico ao de referência.

Ignora apenas `generated_at`, que é carimbo de hora e muda a cada execução.
Qualquer outra diferença — métrica, trade, ponto da curva de equity — é reportada
com o caminho exato e faz o script sair com código 1.

Uso:
    python scripts/verify_replay.py <referencia.json> <novo.json>
    python scripts/verify_replay.py --hash ad61cd70 <referencia.json>
"""
import argparse
import json
import math
import os
import sys

IGNORED_TOP_LEVEL = {'generated_at'}
MAX_DIFFS_SHOWN = 25


def _load(path):
    # utf-8-sig le tanto arquivos com BOM (o que o PowerShell gera ao redirecionar
    # `git show`) quanto sem BOM (o que o motor grava). Sem isso, comparar contra
    # uma referencia extraida do git no Windows quebra com JSONDecodeError.
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def _num_eq(a, b):
    """Igualdade numérica ESTRITA (bit a bit), com NaN == NaN.

    Não há tolerância de ponto flutuante de propósito: uma refatoração que se
    propõe nula deve ler os mesmos float64 e produzir os mesmos bits. Tolerância
    aqui esconderia exatamente o tipo de desvio que este script existe para pegar.
    """
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        return a == b
    return a == b


def _walk(a, b, path, diffs):
    if len(diffs) >= MAX_DIFFS_SHOWN:
        return
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        diffs.append(f"{path}: tipo {type(a).__name__} != {type(b).__name__}")
        return
    if isinstance(a, dict):
        ka, kb = set(a), set(b)
        for k in sorted(ka - kb):
            diffs.append(f"{path}.{k}: presente na referencia, ausente no novo")
        for k in sorted(kb - ka):
            diffs.append(f"{path}.{k}: ausente na referencia, presente no novo")
        for k in sorted(ka & kb):
            if path == '' and k in IGNORED_TOP_LEVEL:
                continue
            _walk(a[k], b[k], f"{path}.{k}" if path else k, diffs)
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: tamanho {len(a)} != {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            _walk(x, y, f"{path}[{i}]", diffs)
    else:
        if not _num_eq(a, b):
            diffs.append(f"{path}: {a!r} != {b!r}")


def _trade_summary(doc):
    out = {}
    for win, det in (doc.get('windows_detail') or {}).items():
        out[win] = len(det.get('trades') or [])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('reference', help='JSON de referencia (o resultado que deve ser preservado)')
    ap.add_argument('candidate', nargs='?', help='JSON novo; omitido se --hash for usado')
    ap.add_argument('--hash', dest='cfg_hash', default=None,
                    help='le o candidato de data/experimentos/exp_{hash}.json')
    args = ap.parse_args()

    if args.cfg_hash:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cand_path = os.path.join(base, 'data', 'experimentos', f'exp_{args.cfg_hash}.json')
    elif args.candidate:
        cand_path = args.candidate
    else:
        ap.error('informe o JSON candidato ou use --hash')

    ref = _load(args.reference)
    cand = _load(cand_path)

    print(f"referencia : {args.reference}")
    print(f"candidato  : {cand_path}")
    print(f"config_hash: {ref.get('config_hash')} -> {cand.get('config_hash')}")
    print(f"trades/janela (ref): {_trade_summary(ref)}")
    print(f"trades/janela (novo): {_trade_summary(cand)}")

    diffs = []
    _walk(ref, cand, '', diffs)

    if not diffs:
        print("\nOK: artefatos IDENTICOS trade a trade (ignorando generated_at).")
        return 0

    print(f"\nFALHA: {len(diffs)} diferenca(s)"
          f"{' (mostrando as primeiras)' if len(diffs) >= MAX_DIFFS_SHOWN else ''}:")
    for d in diffs:
        print(f"  - {d}")
    return 1


if __name__ == '__main__':
    sys.exit(main())
