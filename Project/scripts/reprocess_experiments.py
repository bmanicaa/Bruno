"""
REPROCESSAMENTO DOS EXPERIMENTOS LIMPOS (Fase A - 24/08/2026)

Re-roda o walk-forward de toda config NAO contaminada para que o arquivo
exp_{hash}.json passe a conter `sharpe_trading` (excesso sobre o cash yield).

Por que e necessario: o Deflated Sharpe compara o Sharpe da config candidata
contra a distribuicao dos Sharpes de todas as tentativas. Se metade dos
experimentos guarda o Sharpe COM o cash yield e a outra metade sem, o teste
mistura duas escalas e o resultado nao significa nada. O
statistical_validation.py detecta a mistura e cai na metrica legada — este
script elimina a necessidade disso.

Nao toca em experimentos marcados com `invalid_lookahead` (pre-V2.3): eles sao
evidencia historica, nao tentativas validas.

Uso:
  python scripts/reprocess_experiments.py            # todas as familias
  python scripts/reprocess_experiments.py --family swing
"""

import argparse
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backtest_institucional as bi

SWING_KEYS = {'risk_pct', 'max_positions', 'fee_pct', 'entry_tf', 'runner_mode',
              'short_mode', 'universe'}
CS_KEYS = {'top_n', 'mom_days', 'reb_days'}
TREND_KEYS = {'ema_span', 'check_days', 'assets'}


def classify(cfg):
    keys = set(cfg)
    if SWING_KEYS & keys:
        return 'swing'
    if CS_KEYS & keys:
        return 'cs_momentum'
    if TREND_KEYS & keys:
        return 'trend'
    return None


def collect_clean_configs():
    """Configs validas agrupadas por familia, deduplicadas por hash."""
    out = {'swing': [], 'cs_momentum': [], 'trend': []}
    seen = set()
    for path in sorted(glob.glob(os.path.join(bi.EXP_DIR, 'exp_*.json'))):
        with open(path, encoding='utf-8') as f:
            try:
                d = json.load(f)
            except json.JSONDecodeError:
                continue
        if d.get('invalid_lookahead'):
            continue
        cfg = d.get('config') or {}
        fam = classify(cfg)
        if fam is None:
            continue
        h = d.get('config_hash')
        if h in seen:
            print(f'  [dup] {os.path.basename(path)} repete o hash {h} — pulado')
            continue
        seen.add(h)
        out[fam].append((h, cfg))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--family', choices=['swing', 'cs_momentum', 'trend', 'all'], default='all')
    args = ap.parse_args()

    groups = collect_clean_configs()
    total = sum(len(v) for k, v in groups.items()
                if args.family in ('all', k))
    print(f'Configs limpas a reprocessar: {total}')
    for fam, items in groups.items():
        print(f'  {fam:12} {len(items)}')

    done = 0
    t0 = time.time()

    if args.family in ('all', 'swing') and groups['swing']:
        print('\n' + '=' * 90)
        print('FAMILIA SWING — carregando dados uma unica vez')
        print('=' * 90)
        preloaded = bi.load_all_data()
        for h, cfg in groups['swing']:
            done += 1
            print(f'\n[{done}/{total}] swing {h}: {json.dumps(cfg, ensure_ascii=False)}')
            bi.run_walkforward(cfg, 100000.0, append=False, preloaded=preloaded)

    if args.family in ('all', 'cs_momentum') and groups['cs_momentum']:
        import backtest_cs_momentum as cs
        print('\n' + '=' * 90)
        print('FAMILIA CROSS-SECTIONAL MOMENTUM — carregando dados uma unica vez')
        print('=' * 90)
        pre_cs = cs.load_preloaded()
        for h, cfg in groups['cs_momentum']:
            done += 1
            print(f'\n[{done}/{total}] cs_mom {h}: {json.dumps(cfg, ensure_ascii=False)}')
            cs.run_wf(cfg, preloaded=pre_cs)

    if args.family in ('all', 'trend') and groups['trend']:
        import backtest_trend_bh as tb
        print('\n' + '=' * 90)
        print('FAMILIA TIME-SERIES TREND — carregando dados uma unica vez')
        print('=' * 90)
        pre_tb = tb.load_preloaded()
        for h, cfg in groups['trend']:
            done += 1
            print(f'\n[{done}/{total}] trend {h}: {json.dumps(cfg, ensure_ascii=False)}')
            tb.run_wf(cfg, preloaded=pre_tb)

    print(f'\nConcluido: {done} experimentos em {(time.time() - t0) / 60:.1f} min')


if __name__ == '__main__':
    main()
