"""
LOTE DE EXPERIMENTOS WALK-FORWARD (motor V2.3 limpo)

Roda multiplas configs com UMA unica carga de dados, gravando cada uma em
data/experimentos/exp_{hash}.json (sem tocar no analises.md).

Uso: python scripts/batch_experiments.py [--only nome1,nome2]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backtest_institucional as bi

BASE = {
    'risk_pct': 0.015,
    'max_positions': 4,
    'fee_pct': 0.00075,
    'btc_adx_min': 0.0,
    'entry_tf': '1d',
    'runner_mode': 'ema20_1d',
    'short_mode': 'breakout',
    'universe': 'alpha',
}


def cfg(**over):
    c = dict(BASE)
    c.update(over)
    return c


CONFIGS = [
    ('g1_btceth_breakout', cfg(long_mode='breakout', short_mode='none', risk_pct=0.0075, universe='btceth')),
    ('g2_btceth_breakout_1p5', cfg(long_mode='breakout', short_mode='none', universe='btceth')),
    ('g3_f4_vipfee', cfg(short_mode='none', risk_pct=0.0075, fee_pct=0.0002, universe='btceth')),
    ('g4_alpha_breakout_ns', cfg(long_mode='breakout', short_mode='none')),
]


def main():
    only = None
    if '--only' in sys.argv:
        only = sys.argv[sys.argv.index('--only') + 1].split(',')

    preloaded = bi.load_all_data()
    table = []
    for name, params in CONFIGS:
        if only and name not in only:
            continue
        print('\n' + '#' * 96)
        print(f'EXPERIMENTO {name}: {json.dumps(params, ensure_ascii=False)}')
        print('#' * 96)
        summary = bi.run_walkforward(params, 100000.0, append=False, preloaded=preloaded)
        oa = summary['oos_aggregate']
        table.append((name, summary['config_hash'], oa))

    print('\n' + '=' * 96)
    print('RESUMO COMPARATIVO DOS EXPERIMENTOS DO LOTE (OOS 4 blocos)')
    print('=' * 96)
    print('%-24s %-10s %7s %11s %6s %6s %7s %8s %8s' % (
        'config', 'hash', 'trades', 'tradingPnL', 'PFmed', 'PFmed*', 'Win%', 'Sharpe', 'ExpR'))
    for name, h, oa in table:
        print('%-24s %-10s %7d %11.0f %6.2f %6.2f %7.1f %8.2f %8.3f' % (
            name, h, oa['trades_total'], oa['trading_pnl_sum'], oa['pf_mean'],
            oa['pf_median'], oa['win_rate_mean'], oa['sharpe_mean'], oa['expectancy_r_mean']))
    print('-' * 96)
    print('baseline V2.3 alpha (9ea2dff4):  trades=277 tradingPnL=-12,064 PF=0.99 Sharpe=0.11 ExpR=0.010')
    print('baseline btceth  (0c42aa92):    trades= 89 tradingPnL= -2,578 PF=0.94 Sharpe=0.33 ExpR=0.001')


if __name__ == '__main__':
    main()
