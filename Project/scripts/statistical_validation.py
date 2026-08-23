"""
VALIDACAO ESTATISTICA DO WALK-FORWARD (Fase 0.1 / 0.4)

Ferramentas de inferencia sobre os experimentos do motor canonico:
1. Block bootstrap (circular/estacionario) nos trades OOS -> IC 95% e p-valores
   para PF, expectancia, PnL total e Sharpe.
2. Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) para corrigir o vies
   de multiplos testes na selecao de configs.
3. Robustez leave-one-out por bloco OOS (ex.: remover o OOS3).

Uso:
  python scripts/statistical_validation.py --exp 9ea2dff4
  python scripts/statistical_validation.py --exp 9ea2dff4 --n-iter 4000 --block 8
"""

import argparse
import json
import math
import os
import sys

import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP_DIR = os.path.join(BASE_DIR, 'data', 'experimentos')
OOS_NAMES = ['OOS1', 'OOS2', 'OOS3', 'OOS4']

# Barras de 4h por ano — mesmo fator de anualizacao usado pelo motor.
ANNUAL_FACTOR = 2190.0
# Cash yield modelado (6% a.a.) convertido para a barra de 4h. E a taxa livre de
# risco deste ambiente: o Sharpe de edge deve medir o EXCESSO sobre ela, senao
# uma estrategia que fica parada no caixa exibe Sharpe alto sem operar nada.
CASH_YIELD_PER_BAR = 0.06 / ANNUAL_FACTOR
# Minimo de trades para o block bootstrap dizer algo. Abaixo disso o reamostrador
# devolve quase a serie original (blocos maiores que n/3) e o p-valor satura em
# 1.0 ou 0.0 — foi o que produziu "P(PF>1)=100%" com 10 trades na familia trend.
MIN_TRADES_BOOTSTRAP = 30


def load_experiment(hash_or_path):
    if os.path.exists(hash_or_path):
        with open(hash_or_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    path = os.path.join(EXP_DIR, f'exp_{hash_or_path}.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _block_starts(rng, n, block_len):
    return rng.integers(0, n, size=(n + block_len - 1) // block_len)


def _resample_series(rng, values, n_iter, block_len):
    values = np.asarray(values, dtype=float)
    n = len(values)
    out = np.empty((n_iter, n))
    for it in range(n_iter):
        starts = _block_starts(rng, n, block_len)
        idx = np.concatenate([np.arange(s, s + block_len) % n for s in starts])
        out[it] = values[idx[:n]]
    return out


def bootstrap_trade_stats(trades, n_iter=2000, block_len=8, seed=42):
    if not trades:
        return None
    n = len(trades)
    # Blocos maiores que ~n/3 fazem cada reamostra repetir quase a serie inteira,
    # o que colapsa a variancia e satura os p-valores. Encolhe o bloco e sinaliza
    # amostra insuficiente em vez de devolver um numero falsamente confiante.
    effective_block = max(1, min(block_len, n // 3))
    pnl = np.array([t['pnl_brl'] for t in trades], dtype=float)
    risk = np.array([max(t['risk_brl'], 1e-9) for t in trades], dtype=float)
    r = pnl / risk
    rng = np.random.default_rng(seed)

    pnl_b = _resample_series(rng, pnl, n_iter, effective_block)
    r_b = _resample_series(rng, r, n_iter, effective_block)

    total_pnl_b = pnl_b.sum(axis=1)
    exp_r_b = r_b.mean(axis=1)
    gross_p_b = pnl_b.clip(min=0).sum(axis=1)
    gross_l_b = (-pnl_b.clip(max=0)).sum(axis=1)
    pf_b = np.where(gross_l_b > 1e-12, gross_p_b / gross_l_b, np.inf)

    def ci(x):
        return float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))

    return {
        'n_trades': n,
        'n_iter': n_iter,
        'block_len': effective_block,
        'block_len_requested': block_len,
        'insufficient_sample': n < MIN_TRADES_BOOTSTRAP,
        'total_pnl_ci95': ci(total_pnl_b),
        'p_pnl_gt0': float((total_pnl_b > 0).mean()),
        'expectancy_r_ci95': ci(exp_r_b),
        'p_expectancy_gt0': float((exp_r_b > 0).mean()),
        'pf_ci95': ci(pf_b),
        'p_pf_gt1': float((pf_b > 1.0).mean()),
        'pf_mean_boot': float(np.mean(pf_b)),
    }


def bootstrap_sharpe(windows_equity, n_iter=2000, block_len=24, seed=42, annual=ANNUAL_FACTOR,
                     excess=True):
    rng = np.random.default_rng(seed)
    per_window = {}
    for name, curve in windows_equity.items():
        rets = _window_returns(curve, excess=excess)
        if rets is None:
            continue
        per_window[name] = rets
    if not per_window:
        return None
    window_names = list(per_window.keys())
    boot = np.empty((n_iter, len(window_names)))
    for j, name in enumerate(window_names):
        rets = per_window[name]
        resampled = _resample_series(rng, rets, n_iter, block_len)
        means = resampled.mean(axis=1)
        stds = resampled.std(axis=1, ddof=1)
        boot[:, j] = means / (stds + 1e-12) * math.sqrt(annual)
    agg = boot.mean(axis=1)
    return {
        'windows': window_names,
        'excess_over_cash_yield': excess,
        'sharpe_mean_ci95': (float(np.percentile(agg, 2.5)), float(np.percentile(agg, 97.5))),
        'p_sharpe_gt0': float((agg > 0).mean()),
    }


def _window_returns(curve, excess=True):
    """Retornos por barra de uma curva de equity.

    Com excess=True subtrai o cash yield modelado (a taxa livre de risco deste
    ambiente). Sem isso, o Sharpe de uma estrategia que passa a maior parte do
    tempo em caixa mede o rendimento da poupanca, nao a habilidade de operar.
    """
    eq = np.asarray(curve, dtype=float)
    if len(eq) < 50:
        return None
    rets = np.diff(eq) / eq[:-1]
    rets = rets[np.isfinite(rets)]
    if excess:
        rets = rets - CASH_YIELD_PER_BAR
    return rets


def pooled_returns(windows_equity, excess=True):
    all_rets = []
    for curve in windows_equity.values():
        rets = _window_returns(curve, excess=excess)
        if rets is None:
            continue
        all_rets.append(rets)
    return np.concatenate(all_rets) if all_rets else np.array([])


def deflated_sharpe(sr_obs, sr_trials, returns, n_trials=None, annual_factor=ANNUAL_FACTOR):
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014).

    ATENCAO A ESCALA (bug corrigido em 24/08/2026): a formula do DSR exige que o
    Sharpe e o numero de observacoes estejam na MESMA escala temporal. `sr_obs`
    e `sr_trials` chegam ANUALIZADOS (o motor multiplica por sqrt(2190)), mas
    `n_obs` conta barras de 4h. Usar os dois juntos multiplicava o Z por
    sqrt(2190) ~= 46.8 e produzia p-valores absurdos (ex.: p=1e-12 para uma
    config cujo bootstrap dava apenas 60% de P(PF>1)).

    A correcao desanualiza tudo para a escala por barra antes de aplicar a
    formula. sr0 e reportado nas duas escalas para leitura humana.
    """
    sr_trials = np.asarray(sr_trials, dtype=float)
    returns = np.asarray(returns, dtype=float)
    n_trials = len(sr_trials) if n_trials is None else int(n_trials)
    n_obs = len(returns)
    if n_trials < 2 or n_obs < 30:
        return None

    # Desanualiza para a escala por observacao (barra de 4h), coerente com n_obs.
    sqrt_af = math.sqrt(annual_factor)
    sr_obs_per = float(sr_obs) / sqrt_af
    sr_trials_per = sr_trials / sqrt_af

    v_sr = float(np.var(sr_trials_per, ddof=1))
    euler = 0.5772156649
    emax = (1 - euler) * _inv_norm_cdf(1 - 1.0 / n_trials) + euler * _inv_norm_cdf(
        1 - 1.0 / (n_trials * math.e))
    sr0_per = math.sqrt(v_sr) * emax
    if np.std(returns) == 0:
        return {'sr_obs': sr_obs, 'sr0': sr0_per * sqrt_af, 'z': None, 'p_value': None}
    skew = float(_skew(returns))
    kurt = float(_kurt(returns))
    denom = math.sqrt(1 - skew * sr_obs_per + (kurt - 1) / 4 * sr_obs_per ** 2)
    denom = denom if denom > 0 else 1e-12
    z = (sr_obs_per - sr0_per) * math.sqrt(n_obs - 1) / denom
    return {
        'sr_obs': sr_obs,
        'sr0': sr0_per * sqrt_af,
        'sr_obs_per_bar': sr_obs_per,
        'sr0_per_bar': sr0_per,
        'annual_factor': annual_factor,
        'n_trials': n_trials,
        'n_obs': n_obs,
        'skew': skew,
        'kurt': kurt,
        'z': z,
        'p_value': float(1 - _norm_cdf(z)),
    }


def leave_one_out(summary):
    windows = summary['windows']
    oos = {k: v for k, v in windows.items() if k in OOS_NAMES}
    base = _aggregate(oos)
    out = {'base': base}
    for drop in OOS_NAMES:
        reduced = {k: v for k, v in oos.items() if k != drop}
        out[f'without_{drop}'] = _aggregate(reduced)
    return out


def _aggregate(oos):
    if not oos:
        return {}
    out = {
        'trades': sum(w['trades'] for w in oos.values()),
        'return_pct_sum': round(sum(w['return_pct'] for w in oos.values()), 2),
        'trading_pnl_sum': round(sum(w['trading_pnl'] for w in oos.values()), 2),
        'pf_mean': round(np.mean([w['pf'] for w in oos.values()]), 2),
        'sharpe_mean': round(np.mean([w['sharpe'] for w in oos.values()]), 2),
        'dd_max': round(max(w['dd_pct'] for w in oos.values()), 2),
    }
    # Experimentos reprocessados apos a Fase A trazem o Sharpe de trading; e ele
    # que deve ser lido, nao o `sharpe_mean` (que inclui o cash yield).
    if all('sharpe_trading' in w for w in oos.values()):
        out['sharpe_trading_mean'] = round(np.mean([w['sharpe_trading'] for w in oos.values()]), 2)
    # Concentracao em um unico bloco foi o modo de falha da g3: agregado positivo
    # com 3 de 4 blocos negativos. Expor a contagem evita repetir a leitura errada.
    out['blocos_pnl_positivo'] = sum(1 for w in oos.values() if w['trading_pnl'] > 0)
    return out


def _inv_norm_cdf(p):
    return float(_norm_ppf(p))


def _norm_ppf(p):
    from math import log, sqrt, erf
    a1, a2, a3 = -3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02
    a4, a5, a6 = 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00
    b1, b2, b3 = -5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02
    b4, b5 = 6.680131188771972e+01, -1.328068155288572e+01
    c1, c2, c3 = -7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00
    c4, c5, c6 = -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00
    d1, d2, d3, d4 = 7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00
    p_low, p_high = 0.02425, 1 - 0.02425
    if p < p_low:
        q = sqrt(-2 * log(p))
        return (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / ((((d1 * q + d2) * q + d3) * q + d4) * q + 1)
    if p > p_high:
        q = sqrt(-2 * log(1 - p))
        return -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / ((((d1 * q + d2) * q + d3) * q + d4) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q / (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1)


def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _skew(x):
    x = np.asarray(x)
    mu = x.mean()
    s = x.std(ddof=1)
    return float(np.mean(((x - mu) / s) ** 3)) if s > 1e-12 else 0.0


def _kurt(x):
    x = np.asarray(x)
    mu = x.mean()
    s = x.std(ddof=1)
    return float(np.mean(((x - mu) / s) ** 4)) if s > 1e-12 else 3.0


def collect_all_experiments():
    """Universo de tentativas para a correcao de multiplos testes do DSR.

    Duas exclusoes deliberadas (corrigidas em 24/08/2026):
    1. Experimentos marcados com `invalid_lookahead` — rodados antes da correcao
       V2.3. Seus Sharpes inflados distorcem a variancia entre tentativas e, pior,
       faziam n_trials variar conforme os arquivos presentes na pasta, tornando o
       DSR nao reproduzivel (a mesma config recebeu n_trials=28 e 42 em execucoes
       diferentes).
    2. Configs duplicadas — o mesmo `config_hash` contava duas vezes e inflava
       n_trials sem trazer informacao nova.
    """
    trials = []
    seen = set()
    if os.path.isdir(EXP_DIR):
        for fn in sorted(os.listdir(EXP_DIR)):
            if not (fn.startswith('exp_') and fn.endswith('.json')):
                continue
            with open(os.path.join(EXP_DIR, fn), 'r', encoding='utf-8') as f:
                try:
                    summ = json.load(f)
                except json.JSONDecodeError:
                    continue
            if summ.get('invalid_lookahead'):
                continue
            h = summ.get('config_hash', fn[4:-5])
            if h in seen:
                continue
            seen.add(h)
            oa = summ.get('oos_aggregate', {})
            # Prefere o Sharpe de trading (excesso sobre o cash yield). Arquivos
            # antigos so tem `sharpe_mean` (com o caixa dentro) — ficam marcados
            # para que a mistura de escalas seja visivel no relatorio.
            sharpe_trading = oa.get('sharpe_trading_mean')
            trials.append({
                'hash': h,
                'file': fn,
                'sharpe_mean': oa.get('sharpe_mean'),
                'sharpe_trading_mean': sharpe_trading,
                'legacy_sharpe': sharpe_trading is None,
                'trading_pnl_sum': oa.get('trading_pnl_sum'),
                'pf_mean': oa.get('pf_mean'),
                'params': summ.get('config', {}),
            })
    return trials


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp', required=True, help='hash ou caminho do experimento enriquecido')
    parser.add_argument('--n-iter', type=int, default=2000)
    parser.add_argument('--block', type=int, default=8)
    parser.add_argument('--out', default=None)
    args = parser.parse_args()

    summary = load_experiment(args.exp)
    detail = summary.get('windows_detail', {})
    if not detail:
        print('ERRO: experimento sem "windows_detail" — rode o walk-forward com o motor atualizado.')
        sys.exit(1)

    report = {
        'config': summary.get('config'),
        'config_hash': summary.get('config_hash'),
        'leave_one_out': leave_one_out(summary),
        'bootstraps': {},
    }

    all_trades = []
    windows_equity = {}
    for name in OOS_NAMES:
        wd = detail.get(name, {})
        all_trades.extend(wd.get('trades', []))
        if wd.get('equity_curve'):
            windows_equity[name] = wd['equity_curve']

    report['bootstraps']['oos_trades'] = bootstrap_trade_stats(
        all_trades, n_iter=args.n_iter, block_len=args.block)
    report['bootstraps']['oos_sharpe'] = bootstrap_sharpe(
        windows_equity, n_iter=args.n_iter, block_len=args.block * 3)

    trials = collect_all_experiments()

    # O DSR precisa comparar peras com peras: se ESTE experimento ja tem o Sharpe
    # de trading, o universo de tentativas tambem tem de usa-lo. Se algum arquivo
    # antigo so tiver o Sharpe com caixa, cai-se na metrica legada para todos e o
    # relatorio avisa — melhor um numero coerente e sinalizado do que uma mistura
    # silenciosa de duas escalas.
    wins = summary['windows']
    has_trading_sharpe = all('sharpe_trading' in wins.get(n, {}) for n in OOS_NAMES)
    n_legacy = sum(1 for t in trials if t['legacy_sharpe'])
    use_trading = has_trading_sharpe and n_legacy == 0

    if use_trading:
        sharpe_field, sr_field = 'sharpe_trading_mean', 'sharpe_trading'
    else:
        sharpe_field, sr_field = 'sharpe_mean', 'sharpe'

    sharpe_trials = [t[sharpe_field] for t in trials if t.get(sharpe_field) is not None]
    rets = pooled_returns(windows_equity, excess=use_trading)
    if sharpe_trials and len(rets) > 30:
        sr_obs = float(np.mean([wins[n][sr_field] for n in OOS_NAMES]))
        ds = deflated_sharpe(sr_obs, sharpe_trials, rets, n_trials=len(sharpe_trials))
        if ds is not None:
            ds['sharpe_basis'] = 'trading (excesso sobre cash yield)' if use_trading else 'total (INCLUI cash yield)'
            ds['legacy_trials'] = n_legacy
        report['deflated_sharpe'] = ds
    else:
        report['deflated_sharpe'] = None

    print('=' * 96)
    print('VALIDACAO ESTATISTICA WALK-FORWARD | config:', summary.get('config_hash'),
          '|', json.dumps(summary.get('config', {}), ensure_ascii=False))
    print('=' * 96)
    print('\n[1] LEAVE-ONE-OUT (robustez por bloco OOS)')
    for k, v in report['leave_one_out'].items():
        st = v.get('sharpe_trading_mean')
        st_txt = ('%6.2f' % st) if st is not None else '   n/d'
        print('  %-16s trades=%3d ret%%=%8.2f tradingPnL=%10.0f PFmed=%5.2f Shrp=%5.2f ShrpTrd=%s DD=%6.2f'
              % (k, v['trades'], v['return_pct_sum'], v['trading_pnl_sum'], v['pf_mean'],
                 v['sharpe_mean'], st_txt, v['dd_max']))
    base = report['leave_one_out'].get('base', {})
    if 'blocos_pnl_positivo' in base:
        bp = base['blocos_pnl_positivo']
        print('  -> blocos OOS com trading PnL positivo: %d/4%s' % (
            bp, '   *** CONCENTRADO: o agregado nao representa o comportamento tipico ***'
            if bp < 3 else ''))
    bt = report['bootstraps']['oos_trades']
    if bt:
        print('\n[2] BOOTSTRAP DE TRADES OOS (block=%d, %d iter, %d trades)' % (
            bt['block_len'], bt['n_iter'], bt['n_trades']))
        if bt['insufficient_sample']:
            print('  *** AMOSTRA INSUFICIENTE: %d trades (< %d). Os p-valores abaixo NAO sao'
                  % (bt['n_trades'], MIN_TRADES_BOOTSTRAP))
            print('      conclusivos — com poucos trades o reamostrador repete quase a serie')
            print('      original e os p-valores saturam perto de 0%% ou 100%%. ***')
        print('  PnL total IC95:  [%10.0f , %10.0f] | P(PnL>0) = %.1f%%' % (
            bt['total_pnl_ci95'][0], bt['total_pnl_ci95'][1], bt['p_pnl_gt0'] * 100))
        print('  Expectancia IC95: [%+.3fR , %+.3fR] | P(Exp>0) = %.1f%%' % (
            bt['expectancy_r_ci95'][0], bt['expectancy_r_ci95'][1], bt['p_expectancy_gt0'] * 100))
        print('  PF IC95:         [%.2f , %.2f] | P(PF>1) = %.1f%%' % (
            bt['pf_ci95'][0], bt['pf_ci95'][1], bt['p_pf_gt1'] * 100))
    bs = report['bootstraps']['oos_sharpe']
    if bs:
        basis = 'EXCESSO sobre cash yield' if bs['excess_over_cash_yield'] else 'total, com caixa'
        print('\n[3] BOOTSTRAP DE SHARPE OOS (media dos blocos | base: %s)' % basis)
        print('  Sharpe IC95: [%.2f , %.2f] | P(Sharpe>0) = %.1f%%' % (
            bs['sharpe_mean_ci95'][0], bs['sharpe_mean_ci95'][1], bs['p_sharpe_gt0'] * 100))
    ds = report['deflated_sharpe']
    if ds:
        print('\n[4] DEFLATED SHARPE (multi-testes, %d configs limpas e distintas)' % ds['n_trials'])
        print('  Base do Sharpe: %s' % ds['sharpe_basis'])
        if ds.get('legacy_trials'):
            print('  AVISO: %d experimento(s) sem `sharpe_trading_mean` (rodados antes da correcao).'
                  % ds['legacy_trials'])
            print('         O DSR caiu na metrica legada (com cash yield) para manter a escala')
            print('         coerente. Re-rode o walk-forward dessas configs para eliminar o aviso.')
        print('  SR observado=%.2f | SR0 (piso de ruido)=%.2f | Z=%.2f | p-valor=%.4f' % (
            ds['sr_obs'], ds['sr0'], ds['z'], ds['p_value']))
        print('  VEREDITO DSR: %s (criterio do protocolo: p < 0.10)' % (
            'PASSA' if ds['p_value'] < 0.10 else 'REPROVA'))
    print('=' * 96)

    out_path = args.out or os.path.join(EXP_DIR, f'stat_{summary.get("config_hash")}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False, default=str)
    print('Relatorio salvo:', out_path)


if __name__ == '__main__':
    main()
