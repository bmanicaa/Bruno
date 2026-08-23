"""
MOTOR DE MOMENTUM CROSS-SECTIONAL (Fase 1 - nova familia de sinal)

Estrategia paralela ao swing engine canonico, validada com o MESMO protocolo
walk-forward (IS + 4 blocos OOS + holdout) e compativel com
scripts/statistical_validation.py (mesmo schema de experimento).

Logica (literatura: Liu & Tsyvinski 2018; Grobys & Sapkota 2021):
- Universo point-in-time: Volume Medio Diario 30d > $25M, maturidade >= 180d.
- A cada N dias (rebalance), ranquear por momentum dos ultimos M dias (dados
  de dias COMPLETOS antes do rebalance - zero lookahead).
- Comprar o top-K, peso igual, entrada no open do candle de rebalance +
  slippage 5bps; saida no rebalance seguinte (fee + slippage).
- Funding 8h cobrado durante a posse; cash yield 6% a.a. no caixa livre.
- MtM 4h para DD/Sharpe honestos.

Uso: python scripts/backtest_cs_momentum.py --mom-days 7 --reb-days 7 --top-n 10
     python scripts/backtest_cs_momentum.py --batch   (bateria de configs + resumo)
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backtest_institucional as bi

EXP_DIR = bi.EXP_DIR
OOS_NAMES = ['OOS1', 'OOS2', 'OOS3', 'OOS4']


def load_daily_map():
    dmap = {}
    coins_dir = bi.COINS_DIR
    for s in os.listdir(coins_dir):
        p = os.path.join(coins_dir, s, 'klines_1d.csv')
        if not os.path.exists(p):
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if df.empty or 'close' not in df.columns:
            continue
        df['open_time'] = pd.to_datetime(df['open_time_dt'] if 'open_time_dt' in df.columns else df['open_time'])
        df = df[['open_time', 'open', 'high', 'low', 'close']].sort_values('open_time').reset_index(drop=True)
        dmap[s] = df
    return dmap


def build_volume_map(coins_4h_map):
    vmap = {}
    for s, df in coins_4h_map.items():
        if 'daily_avg_vol_30d' not in df.columns:
            continue
        vmap[s] = df['daily_avg_vol_30d']
    return vmap


def funding_between(funding_map, s, t0, t1):
    fr = funding_map.get(s)
    if fr is None or fr.empty:
        return []
    mask = (fr['fundingTime'] > t0) & (fr['fundingTime'] <= t1)
    return fr.loc[mask, ['fundingTime', 'fundingRate']].values.tolist()


def run_cs_momentum(start_str, end_str, params, preloaded=None):
    p = {
        'top_n': params.get('top_n', 10),
        'mom_days': params.get('mom_days', 7),
        'reb_days': params.get('reb_days', 7),
        'fee_pct': params.get('fee_pct', 0.00075),
        'entry_slippage': 0.0005,
        'exit_slippage': 0.0008,
        'annual_cash_yield': 0.06,
        'ts_mom_gt0': params.get('ts_mom_gt0', False),
        'btc_ema200_filter': params.get('btc_ema200_filter', False),
    }
    start = pd.to_datetime(start_str)
    end = pd.to_datetime(end_str)

    if preloaded is None:
        print('Carregando dados (4h + 1d + funding)...')
        btc_4h, btc_1d, fng_df, coins_4h_map, funding_map, available_symbols = bi.load_all_data()
        daily_map = load_daily_map()
    else:
        btc_4h, daily_map, funding_map, coins_4h_map, available_symbols = preloaded

    btc_4h_sorted = btc_4h.sort_values('open_time').reset_index(drop=True)
    btc_times = btc_4h_sorted['open_time']
    all_ts = [t for t in btc_times if start <= t <= end]
    vol_map = build_volume_map(coins_4h_map)

    rebalance_dates = []
    t = pd.Timestamp(start.date())
    while t <= end:
        rebalance_dates.append(t)
        t += pd.Timedelta(days=p['reb_days'])

    capital = 100000.0
    positions = {}
    trades = []
    equity_curve = []
    total_cash_yield = 0.0
    total_fees = 0.0
    total_funding = 0.0
    cash_yield_per_4h = p['annual_cash_yield'] / 2190.0

    for ts in all_ts:
        if ts in rebalance_dates:
            for s in list(positions.keys()):
                pos = positions[s]
                df4 = coins_4h_map.get(s)
                if df4 is None or ts not in df4.index:
                    continue
                c_open = df4.loc[ts]['open']
                exit_price = c_open * (1 - p['exit_slippage'])
                ret = exit_price / pos['entry_price'] - 1.0
                gross = pos['allocated'] * ret
                fee = pos['allocated'] * (1 + abs(ret)) * p['fee_pct']
                pnl = gross - fee
                capital += pnl
                total_fees += fee
                trades.append({
                    'entry_date': pos['entry_date'].strftime('%Y-%m-%d %H:%M'),
                    'symbol': s,
                    'direction': 'LONG',
                    'pnl_brl': round(pnl, 4),
                    'risk_brl': round(pos['allocated'], 4),
                    'fees_paid': round(fee, 4),
                    'funding_paid': round(pos['funding_paid'], 4),
                    'stop_dist_pct': 0.0,
                    'asset_class': bi._asset_class(s),
                    'regime_macro': 'cs',
                    'rsi_1d': 0.0, 'atr_1d_pct': 0.0, 'btc_adx_1d': 0.0,
                    'exit_dates': [ts.strftime('%Y-%m-%d %H:%M')],
                    'exit_reasons': ['Rebalance Periodico'],
                })
                total_funding += pos['funding_paid']
                del positions[s]

            mom = {}
            btc_bull_ok = True
            if p['btc_ema200_filter']:
                btc_d = daily_map.get('BTCUSDT')
                if btc_d is not None:
                    btc_hist = btc_d[btc_d['open_time'] < ts]
                    if len(btc_hist) >= 201:
                        close_series = btc_hist['close']
                        ema200 = close_series.ewm(span=200, adjust=False).mean().iloc[-1]
                        btc_bull_ok = float(close_series.iloc[-1]) >= float(ema200)
                    else:
                        btc_bull_ok = False

            if btc_bull_ok:
                for s in available_symbols:
                    d1 = daily_map.get(s)
                    if d1 is None:
                        continue
                    hist = d1[d1['open_time'] < ts]
                    if len(hist) < max(180, p['mom_days'] + 2):
                        continue
                    vser = vol_map.get(s)
                    if vser is None:
                        continue
                    vsub = vser[vser.index <= ts]
                    if vsub.empty or vsub.iloc[-1] < bi.MIN_DAILY_VOLUME:
                        continue
                    close_now = float(hist['close'].iloc[-1])
                    close_prev = float(hist['close'].iloc[-1 - p['mom_days']])
                    if close_prev <= 0:
                        continue
                    m = close_now / close_prev - 1.0
                    if p['ts_mom_gt0'] and m <= 0:
                        continue
                    mom[s] = m

            if mom:
                ranked = sorted(mom.items(), key=lambda kv: kv[1], reverse=True)[:p['top_n']]
                alloc_per = capital / len(ranked)
                for s, m in ranked:
                    df4 = coins_4h_map.get(s)
                    if df4 is None or ts not in df4.index:
                        continue
                    entry_price = df4.loc[ts]['open'] * (1 + p['entry_slippage'])
                    entry_fee = alloc_per * p['fee_pct']
                    capital -= entry_fee
                    total_fees += entry_fee
                    positions[s] = {
                        'entry_date': ts,
                        'entry_price': entry_price,
                        'allocated': alloc_per,
                        'funding_paid': 0.0,
                    }

        if ts.hour in [0, 8, 16]:
            for s, pos in positions.items():
                fr = funding_map.get(s)
                if fr is None:
                    continue
                fr_sub = fr[fr['fundingTime'] == ts]
                for _, row in fr_sub.iterrows():
                    df4 = coins_4h_map.get(s)
                    if df4 is None:
                        continue
                    close_ref = df4.loc[ts]['close'] if ts in df4.index else pos['entry_price']
                    charge = bi.funding_charge(True, pos['allocated'], 1.0, pos['entry_price'],
                                               close_ref, float(row['fundingRate']))
                    capital -= charge
                    pos['funding_paid'] += charge

        allocated_total = sum(pos['allocated'] for pos in positions.values())
        free_cash = max(capital - allocated_total, 0.0)
        interest = free_cash * cash_yield_per_4h
        capital += interest
        total_cash_yield += interest

        unreal = 0.0
        for s, pos in positions.items():
            df4 = coins_4h_map.get(s)
            if df4 is not None and ts in df4.index:
                unreal += pos['allocated'] * (df4.loc[ts]['close'] / pos['entry_price'] - 1.0)
            else:
                unreal += 0.0
        equity_curve.append({'timestamp': ts, 'capital': capital + unreal})

    for s in list(positions.keys()):
        pos = positions[s]
        df4 = coins_4h_map.get(s)
        last_sub = df4[df4.index <= end] if df4 is not None else None
        if last_sub is not None and not last_sub.empty:
            c_close = last_sub.iloc[-1]['close']
            ret = c_close / pos['entry_price'] - 1.0
            gross = pos['allocated'] * ret
            fee = pos['allocated'] * (1 + abs(ret)) * p['fee_pct']
            pnl = gross - fee
            capital += pnl
            total_fees += fee
            trades.append({
                'entry_date': pos['entry_date'].strftime('%Y-%m-%d %H:%M'),
                'symbol': s, 'direction': 'LONG',
                'pnl_brl': round(pnl, 4),
                'risk_brl': round(pos['allocated'], 4),
                'fees_paid': round(fee, 4),
                'funding_paid': round(pos['funding_paid'], 4),
                'stop_dist_pct': 0.0,
                'asset_class': bi._asset_class(s), 'regime_macro': 'cs',
                'rsi_1d': 0.0, 'atr_1d_pct': 0.0, 'btc_adx_1d': 0.0,
                'exit_dates': [end.strftime('%Y-%m-%d %H:%M')],
                'exit_reasons': ['Fechamento Fim do Periodo (MtM)'],
            })
            total_funding += pos['funding_paid']

    eq_df = pd.DataFrame(equity_curve)
    eq_df['peak'] = eq_df['capital'].cummax()
    eq_df['drawdown'] = (eq_df['capital'] - eq_df['peak']) / eq_df['peak']
    max_dd = abs(eq_df['drawdown'].min() * 100) if len(eq_df) else 0.0
    eq_df['ret'] = eq_df['capital'].pct_change()
    rets = eq_df['ret'].dropna()
    sharpe = (rets.mean() / (rets.std() + 1e-9)) * np.sqrt(2190) if len(rets) else 0.0
    # Sharpe de trading: excesso sobre o cash yield modelado. Sem descontar essa
    # taxa livre de risco, uma estrategia que fica muito tempo em caixa exibe
    # Sharpe alto sem edge nenhum. Ver nota em backtest_institucional.py.
    ex_rets = rets - p.get('annual_cash_yield', 0.06) / 2190.0
    sharpe_trading = (ex_rets.mean() / (ex_rets.std() + 1e-9)) * np.sqrt(2190) if len(ex_rets) else 0.0

    trading_pnl = sum(t['pnl_brl'] for t in trades)
    net = capital - 100000.0
    wins = [t for t in trades if t['pnl_brl'] > 0.001]
    losses = [t for t in trades if t['pnl_brl'] < -0.001]
    pf = (sum(t['pnl_brl'] for t in wins) / abs(sum(t['pnl_brl'] for t in losses))) if losses and sum(t['pnl_brl'] for t in losses) < 0 else (float('inf') if wins else 0.0)
    win_rate = (len(wins) / len(trades) * 100) if trades else 0.0
    exp_r = float(np.mean([t['pnl_brl'] / max(t['risk_brl'], 1e-9) for t in trades])) if trades else 0.0

    btc_ref = None
    btc4 = coins_4h_map.get('BTCUSDT')
    if btc4 is not None:
        d_in = btc4[btc4.index >= start]
        d_out = btc4[btc4.index <= end]
        if not d_in.empty and not d_out.empty:
            btc_ref = (float(d_out.iloc[-1]['close']) / float(d_in.iloc[0]['close']) - 1) * 100

    results = {
        'engine_version': 'CS-MOM-1.0',
        'params': p,
        'start_date': start_str,
        'end_date': end_str,
        'initial_capital': 100000.0,
        'final_capital': capital,
        'net_profit_brl': net,
        'return_pct': net / 1000.0,
        'total_trades': len(trades),
        'winning_trades': len(wins),
        'losing_trades': len(losses),
        'breakeven_trades': 0,
        'win_rate_pct': win_rate,
        'win_rate_ci95_low_pct': 0.0,
        'win_rate_ci95_high_pct': 0.0,
        'min_trades_warning': len(trades) < 30,
        'profit_factor': pf,
        'max_drawdown_pct': max_dd,
        'sharpe_ratio': sharpe,
        'sharpe_trading': sharpe_trading,
        'sortino_ratio': 0.0,
        'expectancy_r': exp_r,
        'avg_mae_r': 0.0,
        'avg_mfe_r': 0.0,
        'total_cash_yield_brl': total_cash_yield,
        'total_funding_fees_brl': total_funding,
        'total_fees_brl': total_fees,
        'trading_pnl_net_brl': trading_pnl,
        'trading_pnl_gross_brl': trading_pnl + total_fees + total_funding,
        'bnh_btc_return_pct': btc_ref if btc_ref is not None else 0.0,
        'bnh_eth_return_pct': 0.0,
        'coins_scanned': len(available_symbols),
        'semester_checkpoints': {},
        'seg_by_regime': {},
        'seg_by_asset': {},
        'seg_by_exit': {},
    }
    return results, trades, eq_df


def compact(res):
    return {
        'window': f"{res['start_date']} -> {res['end_date']}",
        'trades': res['total_trades'],
        'return_pct': round(res['return_pct'], 2),
        'trading_pnl': round(res['trading_pnl_net_brl'], 2),
        'pf': round(res['profit_factor'], 2),
        'win_rate': round(res['win_rate_pct'], 1),
        'dd_pct': round(res['max_drawdown_pct'], 2),
        'sharpe': round(res['sharpe_ratio'], 2),
        'sharpe_trading': round(res['sharpe_trading'], 2),
        'cash_yield_brl': round(res['total_cash_yield_brl'], 2),
        'expectancy_r': round(res['expectancy_r'], 3),
        'bnh_btc_pct': round(res['bnh_btc_return_pct'], 2),
    }


def load_preloaded():
    """Carga unica de dados, reutilizavel entre configs (ver run_wf)."""
    btc_4h, btc_1d, fng_df, coins_4h_map, funding_map, available_symbols = bi.load_all_data()
    return (btc_4h, load_daily_map(), funding_map, coins_4h_map, available_symbols)


def run_wf(params, preloaded=None):
    if preloaded is None:
        preloaded = load_preloaded()
    wf_results, wf_detail = {}, {}
    for name, s, e in bi.WALKFORWARD_WINDOWS:
        print(f'>>> {name}: {s} -> {e}')
        res, trades, eq = run_cs_momentum(s, e, params, preloaded=preloaded)
        wf_results[name] = compact(res)
        wf_detail[name] = {
            'trades': trades,
            'equity_curve': [round(float(v), 2) for v in eq['capital'].tolist()],
        }
    oos = [wf_results[n] for n in OOS_NAMES]
    summary = {
        'config': params,
        'config_hash': bi.config_hash(params),
        'engine_version': 'CS-MOM-1.0',
        'generated_at': 'now',
        'windows': wf_results,
        'windows_detail': wf_detail,
        'oos_aggregate': {
            'trades_total': sum(w['trades'] for w in oos),
            'return_pct_sum': round(sum(w['return_pct'] for w in oos), 2),
            'trading_pnl_sum': round(sum(w['trading_pnl'] for w in oos), 2),
            'pf_mean': round(np.mean([w['pf'] for w in oos]), 2),
            'pf_median': round(float(np.median([w['pf'] for w in oos])), 2),
            'win_rate_mean': round(np.mean([w['win_rate'] for w in oos]), 1),
            'dd_max': round(max(w['dd_pct'] for w in oos), 2),
            'sharpe_mean': round(np.mean([w['sharpe'] for w in oos]), 2),
            'sharpe_trading_mean': round(np.mean([w['sharpe_trading'] for w in oos]), 2),
            'cash_yield_sum': round(sum(w['cash_yield_brl'] for w in oos), 2),
            'expectancy_r_mean': round(np.mean([w['expectancy_r'] for w in oos]), 3),
        },
    }
    out = os.path.join(EXP_DIR, f"exp_{summary['config_hash']}.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)
    hdr = f"{'Janela':<6} {'Trades':>7} {'Ret%':>9} {'TradingPnL':>12} {'PF':>6} {'Win%':>7} {'DD%':>7} {'Sharpe':>8} {'ExpR':>8} {'B&H BTC%':>9}"
    print(hdr)
    for name, m in wf_results.items():
        print(f"{name:<6} {m['trades']:>7} {m['return_pct']:>9.2f} {m['trading_pnl']:>12,.2f} {m['pf']:>6.2f} "
              f"{m['win_rate']:>7.1f} {m['dd_pct']:>7.2f} {m['sharpe']:>8.2f} {m['expectancy_r']:>8.3f} {m['bnh_btc_pct']:>9.2f}")
    oa = summary['oos_aggregate']
    print('-' * 100)
    print(f"OOS AGREGADO: trades={oa['trades_total']} ret%={oa['return_pct_sum']} pnl={oa['trading_pnl_sum']:,.0f} "
          f"PF={oa['pf_mean']} DD={oa['dd_max']} Sharpe={oa['sharpe_mean']} ExpR={oa['expectancy_r_mean']}")
    print('salvo:', out)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', action='store_true')
    parser.add_argument('--mom-days', type=int, default=7)
    parser.add_argument('--reb-days', type=int, default=7)
    parser.add_argument('--top-n', type=int, default=10)
    args = parser.parse_args()

    if args.batch:
        configs = [
            ('csm_m14r7_ts_ema', dict(top_n=10, mom_days=14, reb_days=7, ts_mom_gt0=True, btc_ema200_filter=True)),
            ('csm_m30r14_ts_ema', dict(top_n=10, mom_days=30, reb_days=14, ts_mom_gt0=True, btc_ema200_filter=True)),
            ('csm_m14r14_ts_ema', dict(top_n=10, mom_days=14, reb_days=14, ts_mom_gt0=True, btc_ema200_filter=True)),
            ('csm_m30r7_ts_ema', dict(top_n=10, mom_days=30, reb_days=7, ts_mom_gt0=True, btc_ema200_filter=True)),
        ]
        for name, params in configs:
            print('\n' + '#' * 96)
            print('CONFIG', name, json.dumps(params))
            print('#' * 96)
            run_wf(params)
    else:
        params = dict(top_n=args.top_n, mom_days=args.mom_days, reb_days=args.reb_days)
        run_wf(params)


if __name__ == '__main__':
    main()
