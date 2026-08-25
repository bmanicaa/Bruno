#!/usr/bin/env python3
"""
TESTE DE SINAL NULO (Fase E, Etapa 2)

O instrumento que o analises.md identifica como faltante ("o instrumento que
falta no laboratorio e o teste de sinal nulo") e para o qual a vetorizacao I2
(197,6s -> 23,0s) foi feita — e que nunca foi executado.

Pergunta
--------
Qual e a distribuicao de resultados de uma estrategia SEM NENHUM EDGE *neste*
motor, com esta carteira de 4 vagas, estes custos e estes precos? Sem essa
distribuicao nao ha como saber se +R$12.909 (ac35a444) ou Sharpe +1,99 (bull 6m)
sao sinal ou o que a mecanica da carteira produz sozinha.

Dois usos, o segundo mais importante que o primeiro:
  1. Confere a taxa de FALSO POSITIVO real dos gates (deveria ficar em ~10%).
  2. Mede quanto do resultado observado e mecanica de carteira + beta do BTC, e
     nao sinal. Se entradas aleatorias na alta de 2023-24 tambem produzem Sharpe
     de trading alto, entao "Bull 6m: +1,99, o unico resultado genuino" do
     README.md nao e genuino — e beta.

Como o nulo e construido (e por que e honesto)
----------------------------------------------
Monkey-patch APENAS em `_hot_arrays`, a funcao que alimenta os dois lacos de
TRIAGEM do motor (linhas 575 e 734). O laco de gestao de posicoes le
`df4.loc[current_time]` direto do DataFrame e NAO passa por ela — portanto:

  * ALEATORIZADO: so as colunas de SINAL (rsi14_1d, cvd, close_1d/ema20_1d,
    return_7d, adx14, ...), por ROTACAO CIRCULAR de deslocamento aleatorio.
    A rotacao preserva a distribuicao marginal e a autocorrelacao de cada sinal
    — logo a TAXA de entradas continua realista — e destroi apenas o alinhamento
    entre o sinal e o preco futuro. E exatamente a hipotese nula.
  * INTOCADO: open/high/low/close/atr14 (preco de entrada e stop sao calculados
    com eles na triagem), daily_avg_vol_30d (filtro de liquidez e legitimo, nao
    e previsao), e todo o laco de saidas, custos, funding, cash yield, 4 vagas,
    breakeven, parcial, runner e time-stop.

Todas as colunas de sinal giram com o MESMO deslocamento por moeda, para que a
coerencia interna entre elas (close_1d > ema20_1d > ema50_1d) se mantenha e a
frequencia de disparo nao mude artificialmente.

Nenhum arquivo do Projeto A e modificado. O patch vive em memoria, neste script.

Uso:
  python scripts/sinal_nulo.py --rodadas 300
  python scripts/sinal_nulo.py --rodadas 20 --janelas OOS2      # so um bloco
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest_institucional as eng   # noqa: E402  (importado, NUNCA editado)
import statistical_validation as sv    # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, 'data', 'acumulacao')

# Colunas que carregam PREVISAO — sao estas que o nulo destroi.
COLUNAS_DE_SINAL = (
    'ema20', 'ema50', 'ema200', 'rsi14', 'adx14', 'cvd', 'vol_ratio', 'return_7d',
    'close_1d', 'open_1d', 'high_1d', 'low_1d', 'ema20_1d', 'ema50_1d',
    'rsi14_1d', 'atr14_1d', 'close_1d_prev', 'high_1d_prev', 'low_1d_prev',
)
# Colunas que definem EXECUCAO (preco de entrada, stop) e LIQUIDEZ — intocadas.
COLUNAS_PRESERVADAS = ('open', 'high', 'low', 'close', 'atr14', 'daily_avg_vol_30d')

_ORIGINAL_HOT = eng._hot_arrays
_estado = {'rng': None, 'offsets': {}, 'ativo': False}


def _hot_arrays_nulo(df, cols=eng._HOT_COLS_4H):
    """Versao nula: rotaciona as colunas de sinal, preserva as de execucao."""
    out = _ORIGINAL_HOT(df, cols)
    if not _estado['ativo']:
        return out
    chave = id(df)
    n = len(df)
    if chave not in _estado['offsets']:
        # Deslocamento longe das bordas para nao "quase alinhar" com o original.
        _estado['offsets'][chave] = int(_estado['rng'].integers(n // 10, max(n // 10 + 1, n)))
    off = _estado['offsets'][chave] % max(n, 1)
    for c in cols:
        if c in COLUNAS_DE_SINAL and c not in COLUNAS_PRESERVADAS:
            out[c] = np.roll(out[c], off)
    return out


def ativar_nulo(seed):
    _estado['rng'] = np.random.default_rng(seed)
    _estado['offsets'] = {}
    _estado['ativo'] = True
    eng._hot_arrays = _hot_arrays_nulo


def desativar_nulo():
    _estado['ativo'] = False
    eng._hot_arrays = _ORIGINAL_HOT


# --------------------------------------------------------------------------

def rodar_uma(seed, params, preloaded, janelas):
    ativar_nulo(seed)
    try:
        res_por_janela, trades_todos, curvas = {}, [], {}
        for nome, ini, fim in janelas:
            res, trades, eq = eng.run_portfolio_backtest(
                ini, fim, 100000.0, params=params, preloaded=preloaded)
            res_por_janela[nome] = eng.compact_metrics(res)
            trades_todos.extend(trades)
            curvas[nome] = [float(v) for v in eq['capital'].tolist()]
    finally:
        desativar_nulo()

    pnl = [res_por_janela[n]['trading_pnl'] for n in res_por_janela]
    sh = [res_por_janela[n]['sharpe_trading'] for n in res_por_janela]
    return {
        'seed': seed,
        'trading_pnl_sum': float(sum(pnl)),
        'sharpe_trading_mean': float(np.mean(sh)),
        'trades_total': int(sum(res_por_janela[n]['trades'] for n in res_por_janela)),
        'blocos_positivos': int(sum(1 for p in pnl if p > 0)),
        'pnl_por_janela': {n: res_por_janela[n]['trading_pnl'] for n in res_por_janela},
        'sharpe_por_janela': {n: res_por_janela[n]['sharpe_trading'] for n in res_por_janela},
        'pf_por_janela': {n: res_por_janela[n]['pf'] for n in res_por_janela},
        'trades_r': [t['pnl_brl'] / max(t.get('risk_brl', 1e-9), 1e-9)
                     for t in trades_todos if 'pnl_brl' in t],
        'curvas': curvas,
    }


def percentil_de(valor, distribuicao):
    d = np.asarray(distribuicao, dtype=float)
    if len(d) == 0:
        return float('nan')
    return float((d < valor).mean() * 100)


def main():
    ap = argparse.ArgumentParser(description='Teste de sinal nulo (Fase E, Etapa 2)')
    ap.add_argument('--rodadas', type=int, default=300)
    ap.add_argument('--janelas', nargs='*', default=None,
                    help='subconjunto de janelas (padrao: as 4 OOS)')
    ap.add_argument('--incluir-bull', action='store_true',
                    help='adiciona a janela BULL 6m do README para testar o "+1,99"')
    ap.add_argument('--saida', default=os.path.join(OUT_DIR, 'sinal_nulo.json'))
    ap.add_argument('--seed', type=int, default=20260824)
    args = ap.parse_args()

    janelas = [(n, s, e) for n, s, e in eng.WALKFORWARD_WINDOWS if n != 'IS']
    if args.janelas:
        janelas = [j for j in janelas if j[0] in args.janelas]
    if args.incluir_bull:
        janelas.append(('BULL6M', '2023-10-01', '2024-03-31'))

    # Baseline: a config de referencia do projeto (alpha, sem short).
    params = {'risk_pct': 0.015, 'max_positions': 4, 'fee_pct': eng.FEE_PCT,
              'btc_adx_min': 0.0, 'entry_tf': '1d', 'runner_mode': 'ema20_1d',
              'short_mode': 'none', 'universe': 'alpha'}

    print('=' * 78)
    print('TESTE DE SINAL NULO — Fase E, Etapa 2')
    print('=' * 78)
    print('Janelas   : %s' % [j[0] for j in janelas])
    print('Config    : %s (hash %s)' % (params['universe'], eng.config_hash(params)[:8]))
    print('Rodadas   : %d' % args.rodadas)
    print('Sinais aleatorizados : %d colunas por rotacao circular' % len(COLUNAS_DE_SINAL))
    print('Preservado           : %s + toda a mecanica de saidas/custos' % str(COLUNAS_PRESERVADAS))
    print()
    print('Carregando dados uma unica vez...')
    t0 = time.time()
    preloaded = eng.load_all_data()
    print('  dados carregados em %.1fs' % (time.time() - t0))

    # Referencia real (motor intacto), para posicionar contra o nulo.
    print('\nRodando a REFERENCIA (motor intacto, sinal real)...')
    t0 = time.time()
    real = rodar_uma(args.seed, params, preloaded, janelas)
    desativar_nulo()
    real_intacto = {}
    for nome, ini, fim in janelas:
        res, trades, eq = eng.run_portfolio_backtest(ini, fim, 100000.0, params=params,
                                                     preloaded=preloaded)
        real_intacto[nome] = eng.compact_metrics(res)
    pnl_real = sum(real_intacto[n]['trading_pnl'] for n in real_intacto)
    sh_real = float(np.mean([real_intacto[n]['sharpe_trading'] for n in real_intacto]))
    tr_real = sum(real_intacto[n]['trades'] for n in real_intacto)
    print('  REAL: PnL de trading %+.0f | Sharpe de trading %+.2f | %d trades  (%.1fs)'
          % (pnl_real, sh_real, tr_real, time.time() - t0))

    print('\nRodando %d simulacoes nulas...' % args.rodadas)
    nulos = []
    t0 = time.time()
    for i in range(args.rodadas):
        r = rodar_uma(args.seed + 1000 + i, params, preloaded, janelas)
        r.pop('curvas', None)
        r.pop('trades_r', None)
        nulos.append(r)
        if (i + 1) % 10 == 0 or i == 0:
            dec = time.time() - t0
            print('  %3d/%d | %.0fs decorridos, ~%.0fs restantes | ultimo: PnL %+9.0f Sharpe %+.2f'
                  % (i + 1, args.rodadas, dec, dec / (i + 1) * (args.rodadas - i - 1),
                     r['trading_pnl_sum'], r['sharpe_trading_mean']))

    pnls = np.array([r['trading_pnl_sum'] for r in nulos])
    shs = np.array([r['sharpe_trading_mean'] for r in nulos])
    trs = np.array([r['trades_total'] for r in nulos])
    blocos = np.array([r['blocos_positivos'] for r in nulos])

    print('\n' + '=' * 78)
    print('DISTRIBUICAO NULA (%d rodadas, entradas sem informacao)' % len(nulos))
    print('=' * 78)
    for rot, arr in (('PnL de trading (soma OOS)', pnls), ('Sharpe de trading (media)', shs),
                     ('trades', trs.astype(float))):
        print('  %-26s p5 %+10.2f | mediana %+10.2f | p95 %+10.2f | media %+10.2f'
              % (rot, np.percentile(arr, 5), np.median(arr), np.percentile(arr, 95), arr.mean()))
    print('  %-26s %.1f%% das rodadas nulas' % ('PnL nulo > 0:', (pnls > 0).mean() * 100))
    print('  %-26s %.1f%% das rodadas nulas' % ('Sharpe nulo > 0:', (shs > 0).mean() * 100))
    print('  %-26s %.1f%% das rodadas nulas' % ('>=3 de 4 blocos positivos:', (blocos >= 3).mean() * 100))

    print('\nONDE CAI O SINAL REAL CONTRA O NULO:')
    print('  PnL de trading    %+10.0f  -> percentil %.1f' % (pnl_real, percentil_de(pnl_real, pnls)))
    print('  Sharpe de trading %+10.2f  -> percentil %.1f' % (sh_real, percentil_de(sh_real, shs)))
    print('  (percentil 50 = indistinguivel de entradas aleatorias)')

    out = {
        'params': params, 'rodadas': len(nulos),
        'janelas': [j[0] for j in janelas],
        'referencia_real': {'trading_pnl_sum': pnl_real, 'sharpe_trading_mean': sh_real,
                            'trades_total': tr_real, 'por_janela': real_intacto},
        'nulo': {
            'trading_pnl': {'p5': float(np.percentile(pnls, 5)), 'mediana': float(np.median(pnls)),
                            'p95': float(np.percentile(pnls, 95)), 'media': float(pnls.mean()),
                            'p_maior_zero': float((pnls > 0).mean())},
            'sharpe_trading': {'p5': float(np.percentile(shs, 5)), 'mediana': float(np.median(shs)),
                               'p95': float(np.percentile(shs, 95)), 'media': float(shs.mean()),
                               'p_maior_zero': float((shs > 0).mean())},
            'trades': {'mediana': float(np.median(trs)), 'media': float(trs.mean())},
            'p_3_de_4_blocos': float((blocos >= 3).mean()),
        },
        'percentil_do_real': {'trading_pnl': percentil_de(pnl_real, pnls),
                              'sharpe_trading': percentil_de(sh_real, shs)},
        'rodadas_detalhe': nulos,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(args.saida, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\nArtefato: %s' % args.saida)


if __name__ == '__main__':
    main()
