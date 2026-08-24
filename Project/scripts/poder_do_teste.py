#!/usr/bin/env python3
"""
CURVA DE PODER DO PROTOCOLO (Fase E, Etapa 1)

Responde a pergunta que o projeto nunca fez: *se existisse um edge REAL de
tamanho X, com que probabilidade este protocolo o aprovaria?*

Motivacao
---------
As Fases A e B mediram exaustivamente o risco de APROVAR DEMAIS (falso
positivo): erro de escala no DSR, Sharpe contaminado pelo cash yield, bootstrap
saturado, universo de tentativas sujo. Nenhuma linha do projeto mediu o risco de
REPROVAR DEMAIS (falso negativo).

Isso importa porque o veredito "36 configuracoes limpas, nenhuma tem edge"
sustenta o congelamento do Projeto A. Se o protocolo so consegue enxergar
efeitos gigantes, "zero aprovadas" e o resultado esperado mesmo num mundo onde
varias estrategias funcionam — e a conclusao correta passa a ser "nao consegui
medir", nao "nao existe".

Metodo
------
1. Le a FORMA EMPIRICA dos trades reais (R-multiplos, duracao, contagem por
   janela, tamanho das curvas de equity) a partir das configs limpas da familia
   swing em data/experimentos/.
2. Gera estrategias sinteticas com EXPECTANCIA VERDADEIRA CONHECIDA, por
   reamostragem em blocos daquela forma empirica + deslocamento da media. Isso
   preserva assimetria, curtose e agrupamento (win rate ~35%, perdas ancoradas
   em -1R, cauda direita longa) — a estrategia sintetica erra do mesmo jeito que
   as reais, so que com edge conhecido.
3. Constroi a curva de equity A PARTIR dos trades (mesma causalidade do motor:
   equity = cash yield + PnL dos trades distribuido no periodo de retencao).
4. Submete cada estrategia aos GATES REAIS, importando as funcoes de
   statistical_validation.py sem alterar nenhuma delas.
5. Repete N vezes por nivel de edge e reporta a TAXA DE APROVACAO = poder.

Nao altera nenhum arquivo do Projeto A. So le.

Uso:
  python scripts/poder_do_teste.py                        # curva padrao
  python scripts/poder_do_teste.py --rodadas 1000         # mais preciso
  python scripts/poder_do_teste.py --varrer-n-trials      # sensibilidade a n_trials
"""

import argparse
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistical_validation as sv  # noqa: E402  (funcoes-gate reusadas, nunca editadas)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP_DIR = os.path.join(BASE_DIR, 'data', 'experimentos')
OUT_DIR = os.path.join(BASE_DIR, 'data', 'acumulacao')

CAPITAL = 100_000.0
RISK_PCT = 0.015
OOS_NAMES = ['OOS1', 'OOS2', 'OOS3', 'OOS4']

# Limiares do protocolo vigente (analises.md secao 3).
MIN_TRADES = 30
MIN_BLOCOS_POSITIVOS = 3
BOOTSTRAP_P_PF = 0.90
DSR_P = 0.10


# --------------------------------------------------------------------------
# 1. Forma empirica
# --------------------------------------------------------------------------

def carregar_forma_empirica():
    """Extrai a forma real dos trades das configs LIMPAS da familia swing."""
    r_pool, hold_pool, sharpe_trials = [], [], []
    trades_por_janela = {w: [] for w in OOS_NAMES}
    barras_por_janela = {}
    std_por_barra = []          # volatilidade real do excesso, por config
    trades_da_config = []       # para escalar a vol com o tamanho da amostra
    vistos = set()

    for path in sorted(glob.glob(os.path.join(EXP_DIR, 'exp_*.json'))):
        with open(path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        if d.get('invalid_lookahead'):
            continue
        h = d.get('config_hash')
        if h in vistos:
            continue
        vistos.add(h)

        agg = d.get('oos_aggregate', {})
        s = agg.get('sharpe_trading_mean', agg.get('sharpe_mean'))
        if s is not None:
            sharpe_trials.append(float(s))

        # A forma dos trades so vem da familia swing (as outras nao tem risk_brl
        # comparavel nem o mesmo mecanismo de 4 vagas).
        if 'risk_pct' not in d.get('config', {}) or 'windows_detail' not in d:
            continue
        n_cfg, stds_cfg = 0, []
        for w in OOS_NAMES:
            wd = d['windows_detail'].get(w)
            if not wd:
                continue
            barras_por_janela.setdefault(w, len(wd['equity_curve']))
            trades_por_janela[w].append(len(wd['trades']))
            n_cfg += len(wd['trades'])
            eq = np.asarray(wd['equity_curve'], dtype=float)
            rr = np.diff(eq) / eq[:-1] - sv.CASH_YIELD_PER_BAR
            if len(rr) > 2:
                stds_cfg.append(float(np.std(rr, ddof=1)))
            for t in wd['trades']:
                r_pool.append(t['pnl_brl'] / max(t['risk_brl'], 1e-9))
                hold_pool.append(_duracao_barras(t))
        if stds_cfg and n_cfg > 0:
            std_por_barra.append(float(np.mean(stds_cfg)))
            trades_da_config.append(n_cfg)

    return {
        'r_pool': np.array(r_pool, dtype=float),
        'hold_pool': np.array(hold_pool, dtype=int),
        'trades_por_janela': {w: int(np.median(v)) for w, v in trades_por_janela.items() if v},
        'barras_por_janela': barras_por_janela,
        'sharpe_trials': np.array(sharpe_trials, dtype=float),
        # Volatilidade por barra do excesso, medida nas curvas de equity reais.
        # Sem isto a curva sintetica fica lisa demais e o Sharpe sai inflado —
        # o que faria o protocolo parecer MAIS poderoso do que e.
        'std_barra_ref': float(np.median(std_por_barra)) if std_por_barra else 0.0022,
        'trades_ref': float(np.median(trades_da_config)) if trades_da_config else 88.0,
    }


def _duracao_barras(t):
    import datetime as dt
    try:
        e = dt.datetime.strptime(t['entry_date'], '%Y-%m-%d %H:%M')
        x = max(dt.datetime.strptime(s, '%Y-%m-%d %H:%M') for s in t['exit_dates'])
        return max(1, int((x - e).total_seconds() // (4 * 3600)))
    except Exception:
        return 37  # mediana empirica


# --------------------------------------------------------------------------
# 2. Geracao sintetica com edge conhecido
# --------------------------------------------------------------------------

def _amostra_em_blocos(rng, pool, n, block_len=4):
    """Reamostragem em blocos: preserva o agrupamento de ganhos/perdas."""
    if n <= 0:
        return np.array([], dtype=float)
    n_blocos = (n + block_len - 1) // block_len
    starts = rng.integers(0, len(pool), size=n_blocos)
    idx = np.concatenate([np.arange(s, s + block_len) % len(pool) for s in starts])
    return pool[idx[:n]]


def gerar_janela(rng, n_trades, n_bars, expectancia, forma):
    """Gera (trades, curva_de_equity) com expectancia VERDADEIRA = `expectancia` R.

    A forma (assimetria, curtose, win rate) vem dos trades reais; so a media e
    deslocada. Assim o edge injetado e conhecido e o resto e realista.
    """
    r = _amostra_em_blocos(rng, forma['r_pool'], n_trades)
    if len(r) == 0:
        return [], np.full(n_bars, CAPITAL)
    r = r - r.mean() + expectancia  # desloca a media, preserva a forma

    risco = CAPITAL * RISK_PCT
    trades = [{'pnl_brl': float(x * risco), 'risk_brl': risco} for x in r]

    # Curva de equity construida A PARTIR dos trades (mesma causalidade do motor).
    # O PnL de cada trade e distribuido no periodo de retencao como uma PONTE
    # BROWNIANA: o caminho oscila (marcacao a mercado) mas termina exatamente no
    # PnL realizado. Distribuir linearmente deixaria a curva lisa demais e
    # inflaria o Sharpe — erro que faria o protocolo parecer mais poderoso.
    incremento = np.zeros(n_bars)
    ruido = np.zeros(n_bars)
    hold = _amostra_em_blocos(rng, forma['hold_pool'].astype(float), n_trades).astype(int)
    for pnl, h in zip(r * risco, hold):
        h = int(max(1, min(h, n_bars - 1)))
        ini = int(rng.integers(0, max(1, n_bars - h)))
        incremento[ini:ini + h] += pnl / h
        z = rng.standard_normal(h)
        ruido[ini:ini + h] += z - z.mean()   # soma zero: nao altera o PnL do trade

    # Escala o ruido para que a volatilidade por barra bata com a real medida nas
    # curvas de equity do motor (escalada pela raiz do tamanho da amostra).
    alvo = forma['std_barra_ref'] * math.sqrt(max(n_trades, 1) / (forma['trades_ref'] / 4.0))
    var_alvo = (alvo * CAPITAL) ** 2
    var_det = float(np.var(incremento, ddof=1)) if n_bars > 2 else 0.0
    var_ruido = float(np.var(ruido, ddof=1)) if n_bars > 2 else 0.0
    if var_ruido > 1e-12:
        k = math.sqrt(max(0.0, var_alvo - var_det) / var_ruido)
        incremento = incremento + k * ruido

    equity = np.empty(n_bars)
    eq = CAPITAL
    for i in range(n_bars):
        eq = eq * (1 + sv.CASH_YIELD_PER_BAR) + incremento[i]
        equity[i] = eq
    return trades, equity


def simular_config(rng, expectancia, forma, escala_trades=1.0, escala_barras=None):
    """`escala_trades` multiplica o numero de trades; `escala_barras`, o de barras.

    Para simular MAIS ANOS DE DADOS os dois tem de escalar juntos: o DSR usa
    `n_obs` (barras) no termo sqrt(n_obs - 1), entao escalar so os trades
    responde "e se a estrategia operasse mais vezes no MESMO periodo?" — que e
    outra pergunta. Quando `escala_barras` e None, ela acompanha `escala_trades`.
    """
    if escala_barras is None:
        escala_barras = escala_trades
    janelas = {}
    for w in OOS_NAMES:
        n_t = max(1, int(round(forma['trades_por_janela'][w] * escala_trades)))
        n_b = max(60, int(round(forma['barras_por_janela'][w] * escala_barras)))
        tr, eq = gerar_janela(rng, n_t, n_b, expectancia, forma)
        janelas[w] = {'trades': tr, 'equity_curve': eq}
    return janelas


# --------------------------------------------------------------------------
# 3. Os gates reais
# --------------------------------------------------------------------------

def sharpe_trading_da_janela(equity):
    rets = sv._window_returns(equity, excess=True)
    if rets is None or len(rets) < 2 or np.std(rets) == 0:
        return 0.0
    return float(np.mean(rets) / np.std(rets, ddof=1) * math.sqrt(sv.ANNUAL_FACTOR))


def avaliar_protocolo(janelas, sharpe_trials, n_trials, n_iter=2000, seed=42):
    """Aplica os criterios 1-5 da secao 3 do analises.md. Usa as funcoes reais."""
    todos = [t for w in OOS_NAMES for t in janelas[w]['trades']]
    pnl_por_bloco = [sum(t['pnl_brl'] for t in janelas[w]['trades']) for w in OOS_NAMES]
    sharpes = [sharpe_trading_da_janela(janelas[w]['equity_curve']) for w in OOS_NAMES]
    sharpe_medio = float(np.mean(sharpes))

    g1 = sharpe_medio > 0
    g2 = sum(1 for p in pnl_por_bloco if p > 0) >= MIN_BLOCOS_POSITIVOS
    g3 = len(todos) >= MIN_TRADES

    bs = sv.bootstrap_trade_stats(todos, n_iter=n_iter, seed=seed)
    pnl = np.array([t['pnl_brl'] for t in todos], dtype=float)
    ganho = pnl.clip(min=0).sum()
    perda = (-pnl.clip(max=0)).sum()
    pf = ganho / perda if perda > 1e-12 else float('inf')
    g4 = pf > 1.0

    curvas = {w: janelas[w]['equity_curve'] for w in OOS_NAMES}
    rets = sv.pooled_returns(curvas, excess=True)
    ds = sv.deflated_sharpe(sharpe_medio, sharpe_trials, rets, n_trials=n_trials)
    p_pf = bs['p_pf_gt1'] if bs else 0.0
    p_dsr = ds['p_value'] if ds and ds.get('p_value') is not None else 1.0
    g5 = (p_pf >= BOOTSTRAP_P_PF) and (p_dsr < DSR_P)

    return {
        'g1_sharpe_trading_pos': g1, 'g2_blocos_positivos': g2, 'g3_min_trades': g3,
        'g4_pf_maior_1': g4, 'g5_bootstrap_e_dsr': g5,
        'aprovada': all([g1, g2, g3, g4, g5]),
        'sharpe_trading': sharpe_medio, 'pf': float(pf), 'n_trades': len(todos),
        'p_pf_gt1': float(p_pf), 'dsr_p': float(p_dsr),
        'blocos_positivos': sum(1 for p in pnl_por_bloco if p > 0),
    }


# --------------------------------------------------------------------------
# 4. Curva de poder
# --------------------------------------------------------------------------

def curva_de_poder(forma, niveis, rodadas, n_trials=None, sharpe_trials=None,
                   escala_trades=1.0, escala_barras=None, n_iter=2000, seed=7):
    sharpe_trials = forma['sharpe_trials'] if sharpe_trials is None else sharpe_trials
    n_trials = len(sharpe_trials) if n_trials is None else n_trials
    linhas = []
    for exp_r in niveis:
        rng = np.random.default_rng(seed + int(exp_r * 10_000))
        res = []
        for i in range(rodadas):
            jan = simular_config(rng, exp_r, forma, escala_trades, escala_barras)
            res.append(avaliar_protocolo(jan, sharpe_trials, n_trials,
                                         n_iter=n_iter, seed=int(rng.integers(1, 2**31))))
        linhas.append({
            'expectancia_R': exp_r,
            'sharpe_trading_medio': float(np.mean([r['sharpe_trading'] for r in res])),
            'poder': float(np.mean([r['aprovada'] for r in res])),
            'g1': float(np.mean([r['g1_sharpe_trading_pos'] for r in res])),
            'g2': float(np.mean([r['g2_blocos_positivos'] for r in res])),
            'g3': float(np.mean([r['g3_min_trades'] for r in res])),
            'g4': float(np.mean([r['g4_pf_maior_1'] for r in res])),
            'g5': float(np.mean([r['g5_bootstrap_e_dsr'] for r in res])),
            'dsr_p_mediano': float(np.median([r['dsr_p'] for r in res])),
            'p_pf_mediano': float(np.median([r['p_pf_gt1'] for r in res])),
            'n_trades_medio': float(np.mean([r['n_trades'] for r in res])),
        })
        _print_linha(linhas[-1])
    return linhas


def _print_linha(l):
    print('  E[R]=%+.3f | Sharpe~%+.2f | trades %3.0f || g1 %.2f g2 %.2f g3 %.2f g4 %.2f g5 %.2f '
          '|| PODER %.3f  (DSR p med %.3f, P(PF>1) med %.2f)' % (
              l['expectancia_R'], l['sharpe_trading_medio'], l['n_trades_medio'],
              l['g1'], l['g2'], l['g3'], l['g4'], l['g5'], l['poder'],
              l['dsr_p_mediano'], l['p_pf_mediano']))


def main():
    ap = argparse.ArgumentParser(description='Curva de poder do protocolo de aceite (Fase E)')
    ap.add_argument('--rodadas', type=int, default=400)
    ap.add_argument('--n-iter', type=int, default=2000, help='iteracoes do bootstrap')
    ap.add_argument('--varrer-n-trials', action='store_true')
    ap.add_argument('--varrer-amostra', action='store_true',
                    help='varre o tamanho de amostra (escala de trades)')
    ap.add_argument('--saida', default=os.path.join(OUT_DIR, 'poder_do_teste.json'))
    args = ap.parse_args()

    forma = carregar_forma_empirica()
    R = forma['r_pool']
    print('=' * 78)
    print('CURVA DE PODER DO PROTOCOLO — Fase E, Etapa 1')
    print('=' * 78)
    print('Forma empirica (configs limpas da familia swing):')
    print('  trades reais no pool : %d' % len(R))
    print('  R-multiplo           : media %+.4f | win rate %.1f%% | skew %.2f | curtose %.2f'
          % (R.mean(), (R > 0).mean() * 100,
             float(((R - R.mean()) ** 3).mean() / R.std() ** 3),
             float(((R - R.mean()) ** 4).mean() / R.std() ** 4)))
    print('  trades por janela OOS: %s (total %d)' % (
        forma['trades_por_janela'], sum(forma['trades_por_janela'].values())))
    print('  barras 4h por janela : %s (total %d)' % (
        forma['barras_por_janela'], sum(forma['barras_por_janela'].values())))
    print('  n_trials em vigor    : %d configs limpas e distintas' % len(forma['sharpe_trials']))
    print('  rodadas por nivel    : %d' % args.rodadas)
    print()

    niveis = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
    print('[1] PODER vs EDGE REAL (protocolo vigente: n_trials=%d, ~%d trades OOS)'
          % (len(forma['sharpe_trials']), sum(forma['trades_por_janela'].values())))
    base = curva_de_poder(forma, niveis, args.rodadas, n_iter=args.n_iter)
    out = {'forma': {k: (v.tolist() if isinstance(v, np.ndarray) else v)
                     for k, v in forma.items() if k != 'r_pool' and k != 'hold_pool'},
           'rodadas': args.rodadas, 'curva_base': base}

    if args.varrer_n_trials:
        out['varredura_n_trials'] = {}
        for nt in (10, 36, 100):
            print('\n[2] n_trials = %d (penalidade de multiplos testes)' % nt)
            st = forma['sharpe_trials']
            out['varredura_n_trials'][nt] = curva_de_poder(
                forma, niveis, args.rodadas, n_trials=nt, sharpe_trials=st,
                n_iter=args.n_iter)

    if args.varrer_amostra:
        out['varredura_amostra'] = {}
        for esc, rot in ((1.0, '3,4 anos (atual)'), (2.0, '~7 anos'),
                         (4.0, '~14 anos'), (10.0, '~34 anos')):
            print('\n[3] Tamanho de amostra: %s — trades E barras x%.0f' % (rot, esc))
            out['varredura_amostra'][rot] = curva_de_poder(
                forma, niveis, args.rodadas, escala_trades=esc, n_iter=args.n_iter)

    os.makedirs(os.path.dirname(args.saida), exist_ok=True)
    with open(args.saida, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\nArtefato: %s' % args.saida)


if __name__ == '__main__':
    main()
