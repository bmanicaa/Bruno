"""
LOTE DE EXPERIMENTOS WALK-FORWARD (motor V2.3.1)

Roda multiplas configs com UMA unica carga de dados, gravando cada uma em
data/experimentos/exp_{hash}.json (sem tocar no analises.md).

Uso: python scripts/batch_experiments.py [--only nome1,nome2]

--------------------------------------------------------------------------
LOTE VIGENTE: Fase B item 1 — hibrido trend + swing (24/08/2026)
--------------------------------------------------------------------------
Hipotese do analises.md secao 2: "so operar swing quando o BTC esta acima da
EMA200 diaria". PRE-REGISTRO das configs abaixo ANTES de rodar, para que o
numero de tentativas do DSR seja o planejado e nao o que sobrou depois de
olhar os resultados.

Achado que define o lote (ver analises.md, 24/08 Fase B): o filtro literal ja
existe. O regime bull do motor exige close_1d >= EMA50 E close_1d >= EMA200,
logo "acima da EMA200" e REDUNDANTE para longs — 'ema200d' sozinho so desliga
os shorts. O que ainda nao foi testado, e o que este lote testa, e um filtro
macro MAIS ESTRITO que o regime bull:
  - ema200d + confirmacao de 7 dias  -> nao entrar em regime recem-virado
                                        (equivale a checagem semanal do airbag
                                         do PLANO_OPERACIONAL_REAL)
  - ema50w  (fechamento semanal >= EMA50 semanal) -> airbag lento
  - ema50w + confirmacao de 7 dias

Baseline escolhida: ad61cd70 (alpha, pullback, sem short, risco 1,50%) — a
unica config de swing com amostra grande (243 trades OOS) E 3/4 blocos OOS
positivos, ou seja a que tem folga para perder trades para o filtro sem cair
abaixo do minimo de 30 trades do protocolo. A g3 (45c0eb3c) entra com um unico
filtro, so para continuidade do historico.

'ctrl_ad61cd70_invariancia' NAO e candidata: e a re-execucao da baseline com o
motor novo. Tem de reproduzir exp_ad61cd70.json byte a byte, provando que a
porta macro desligada nao mexeu em nada.
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

# ad61cd70 — melhor baseline de swing por amostra + consistencia de blocos.
BASE_SWING = dict(BASE, short_mode='none')
# 45c0eb3c — a antiga g3, reprovada na Fase A; entra so por continuidade.
BASE_G3 = dict(BASE, short_mode='none', risk_pct=0.0075, fee_pct=0.0002, universe='btceth')


CONFIGS = [
    ('ctrl_ad61cd70_invariancia', dict(BASE_SWING)),
    ('h1_ema200d_confirm7', dict(BASE_SWING, macro_filter='ema200d', macro_confirm_days=7)),
    ('h2_ema50w', dict(BASE_SWING, macro_filter='ema50w')),
    ('h3_ema50w_confirm7', dict(BASE_SWING, macro_filter='ema50w', macro_confirm_days=7)),
    ('h4_g3_ema200d_confirm7', dict(BASE_G3, macro_filter='ema200d', macro_confirm_days=7)),
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
        w = summary['windows']
        blocos_pos = sum(1 for n in ['OOS1', 'OOS2', 'OOS3', 'OOS4'] if w[n]['trading_pnl'] > 0)
        table.append((name, summary['config_hash'], oa, blocos_pos))

    print('\n' + '=' * 104)
    print('RESUMO COMPARATIVO DO LOTE (OOS 4 blocos) — criterios do analises.md secao 3')
    print('=' * 104)
    print('%-26s %-10s %7s %11s %6s %8s %6s %8s' % (
        'config', 'hash', 'trades', 'tradingPnL', 'PFmed', 'ShrpTrd', 'blk+', 'ExpR'))
    for name, h, oa, blk in table:
        print('%-26s %-10s %7d %11.0f %6.2f %8.2f %6s %8.3f' % (
            name, h, oa['trades_total'], oa['trading_pnl_sum'], oa['pf_median'],
            oa['sharpe_trading_mean'], f'{blk}/4', oa['expectancy_r_mean']))
    print('-' * 104)
    print('baseline ad61cd70 (alpha s/ short): trades=243 tradingPnL=-13,283 PFmed=1.05 ShrpTrd=-0.12 blk+=3/4')
    print('baseline 45c0eb3c (g3, reprovada):  trades= 46 tradingPnL= +4,493 PFmed=0.64 ShrpTrd=-0.47 blk+=1/4')
    print('aceite: ShrpTrd>0 E blk+>=3/4 E trades>=30 E PFmed>1.0 (depois: bootstrap>=90% e DSR p<0.10)')


if __name__ == '__main__':
    main()
