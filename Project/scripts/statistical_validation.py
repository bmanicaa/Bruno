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
    pnl = np.array([t['pnl_brl'] for t in trades], dtype=float)
    risk = np.array([max(t['risk_brl'], 1e-9) for t in trades], dtype=float)
    r = pnl / risk
    rng = np.random.default_rng(seed)

    pnl_b = _resample_series(rng, pnl, n_iter, block_len)
    r_b = _resample_series(rng, r, n_iter, block_len)

    total_pnl_b = pnl_b.sum(axis=1)
    exp_r_b = r_b.mean(axis=1)
    gross_p_b = pnl_b.clip(min=0).sum(axis=1)
    gross_l_b = (-pnl_b.clip(max=0)).sum(axis=1)
    pf_b = np.where(gross_l_b > 1e-12, gross_p_b / gross_l_b, np.inf)

    def ci(x):
        return float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))

    return {
        'n_trades': len(trades),
        'n_iter': n_iter,
        'block_len': block_len,
        'total_pnl_ci95': ci(total_pnl_b),
        'p_pnl_gt0': float((total_pnl_b > 0).mean()),
        'expectancy_r_ci95': ci(exp_r_b),
        'p_expectancy_gt0': float((exp_r_b > 0).mean()),
        'pf_ci95': ci(pf_b),
        'p_pf_gt1': float((pf_b > 1.0).mean()),
        'pf_mean_boot': float(np.mean(pf_b)),
    }


def bootstrap_sharpe(windows_equity, n_iter=2000, block_len=24, seed=42, annual=2190.0):
    rng = np.random.default_rng(seed)
    per_window = {}
    for name, curve in windows_equity.items():
        eq = np.asarray(curve, dtype=float)
        if len(eq) < 50:
            continue
        rets = np.diff(eq) / eq[:-1]
        rets = rets[np.isfinite(rets)]
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
        'sharpe_mean_ci95': (float(np.percentile(agg, 2.5)), float(np.percentile(agg, 97.5))),
        'p_sharpe_gt0': float((agg > 0).mean()),
    }


def pooled_returns(windows_equity):
    all_rets = []
    for curve in windows_equity.values():
        eq = np.asarray(curve, dtype=float)
        if len(eq) < 50:
            continue
        rets = np.diff(eq) / eq[:-1]
        rets = rets[np.isfinite(rets)]
        all_rets.append(rets)
    return np.concatenate(all_rets) if all_rets else np.array([])


def deflated_sharpe(sr_obs, sr_trials, returns, n_trials=None):
    sr_trials = np.asarray(sr_trials, dtype=float)
    returns = np.asarray(returns, dtype=float)
    n_trials = len(sr_trials) if n_trials is None else int(n_trials)
    n_obs = len(returns)
    if n_trials < 2 or n_obs < 30:
        return None
    v_sr = float(np.var(sr_trials, ddof=1))
    euler = 0.5772156649
    emax = (1 - euler) * _inv_norm_cdf(1 - 1.0 / n_trials) + euler * _inv_norm_cdf(
        1 - 1.0 / (n_trials * math.e))
    sr0 = math.sqrt(v_sr) * emax
    if np.std(returns) == 0:
        return {'sr_obs': sr_obs, 'sr0': sr0, 'z': None, 'p_value': None}
    skew = float(_skew(returns))
    kurt = float(_kurt(returns))
    denom = math.sqrt(1 - skew * sr_obs + (kurt - 1) / 4 * sr_obs ** 2)
    denom = denom if denom > 0 else 1e-12
    z = (sr_obs - sr0) * math.sqrt(n_obs - 1) / denom
    return {
        'sr_obs': sr_obs,
        'sr0': sr0,
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
    return {
        'trades': sum(w['trades'] for w in oos.values()),
        'return_pct_sum': round(sum(w['return_pct'] for w in oos.values()), 2),
        'trading_pnl_sum': round(sum(w['trading_pnl'] for w in oos.values()), 2),
        'pf_mean': round(np.mean([w['pf'] for w in oos.values()]), 2),
        'sharpe_mean': round(np.mean([w['sharpe'] for w in oos.values()]), 2),
        'dd_max': round(max(w['dd_pct'] for w in oos.values()), 2),
    }


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
    trials = []
    if os.path.isdir(EXP_DIR):
        for fn in sorted(os.listdir(EXP_DIR)):
            if fn.startswith('exp_') and fn.endswith('.json'):
                with open(os.path.join(EXP_DIR, fn), 'r', encoding='utf-8') as f:
                    try:
                        summ = json.load(f)
                    except json.JSONDecodeError:
                        continue
                oa = summ.get('oos_aggregate', {})
                trials.append({
                    'hash': summ.get('config_hash', fn[4:-5]),
                    'sharpe_mean': oa.get('sharpe_mean'),
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
    sharpe_trials = [t['sharpe_mean'] for t in trials if t['sharpe_mean'] is not None]
    rets = pooled_returns(windows_equity)
    if sharpe_trials and len(rets) > 30:
        sr_obs = float(np.mean([summary['windows'][n]['sharpe'] for n in OOS_NAMES]))
        report['deflated_sharpe'] = deflated_sharpe(
            sr_obs, sharpe_trials, rets, n_trials=len(sharpe_trials))
    else:
        report['deflated_sharpe'] = None

    print('=' * 96)
    print('VALIDACAO ESTATISTICA WALK-FORWARD | config:', summary.get('config_hash'),
          '|', json.dumps(summary.get('config', {}), ensure_ascii=False))
    print('=' * 96)
    print('\n[1] LEAVE-ONE-OUT (robustez por bloco OOS)')
    for k, v in report['leave_one_out'].items():
        print('  %-16s trades=%3d ret%%=%8.2f tradingPnL=%10.0f PFmed=%5.2f Sharpe=%5.2f DD=%6.2f' % (
            k, v['trades'], v['return_pct_sum'], v['trading_pnl_sum'], v['pf_mean'],
            v['sharpe_mean'], v['dd_max']))
    bt = report['bootstraps']['oos_trades']
    if bt:
        print('\n[2] BOOTSTRAP DE TRADES OOS (block=%d, %d iter, %d trades)' % (
            bt['block_len'], bt['n_iter'], bt['n_trades']))
        print('  PnL total IC95:  [%10.0f , %10.0f] | P(PnL>0) = %.1f%%' % (
            bt['total_pnl_ci95'][0], bt['total_pnl_ci95'][1], bt['p_pnl_gt0'] * 100))
        print('  Expectancia IC95: [%+.3fR , %+.3fR] | P(Exp>0) = %.1f%%' % (
            bt['expectancy_r_ci95'][0], bt['expectancy_r_ci95'][1], bt['p_expectancy_gt0'] * 100))
        print('  PF IC95:         [%.2f , %.2f] | P(PF>1) = %.1f%%' % (
            bt['pf_ci95'][0], bt['pf_ci95'][1], bt['p_pf_gt1'] * 100))
    bs = report['bootstraps']['oos_sharpe']
    if bs:
        print('\n[3] BOOTSTRAP DE SHARPE OOS (media dos blocos)')
        print('  Sharpe IC95: [%.2f , %.2f] | P(Sharpe>0) = %.1f%%' % (
            bs['sharpe_mean_ci95'][0], bs['sharpe_mean_ci95'][1], bs['p_sharpe_gt0'] * 100))
    ds = report['deflated_sharpe']
    if ds:
        print('\n[4] DEFLATED SHARPE (multi-testes, %d configs historicas)' % ds['n_trials'])
        print('  SR observado=%.2f | SR0 (piso de ruido)=%.2f | Z=%.2f | p-valor=%.3f' % (
            ds['sr_obs'], ds['sr0'], ds['z'], ds['p_value']))
    print('=' * 96)

    out_path = args.out or os.path.join(EXP_DIR, f'stat_{summary.get("config_hash")}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False, default=str)
    print('Relatorio salvo:', out_path)


if __name__ == '__main__':
    main()
