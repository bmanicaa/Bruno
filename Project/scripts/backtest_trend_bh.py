"""
TIME-SERIES TREND (modelo Faber) em BTC/ETH - Fase 1

Semanal/mensal: se close 1D > EMA(N) do dia COMPLETO anterior -> comprado (peso
igual BTC/ETH); senao caixa remunerado. Custos reais + funding + cash yield.
Validacao: mesmas janelas walk-forward + schema compativel com o bootstrap.

Uso: python scripts/backtest_trend_bh.py --batch
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backtest_institucional as bi

OOS_NAMES = ['OOS1', 'OOS2', 'OOS3', 'OOS4']


def run_trend(start_str, end_str, params, preloaded=None):
    p = {
        'ema_span': params.get('ema_span', 200),
        'check_days': params.get('check_days', 7),
        'assets': params.get('assets', ['BTCUSDT']),
        'fee_pct': params.get('fee_pct', 0.00075),
        'entry_slippage': 0.0005,
        'exit_slippage': 0.0008,
        'annual_cash_yield': 0.06,
    }
    start, end = pd.to_datetime(start_str), pd.to_datetime(end_str)
    if preloaded is None:
        btc_4h, btc_1d, fng_df, coins_4h_map, funding_map, available_symbols = bi.load_all_data()
    else:
        btc_4h, coins_4h_map, funding_map, available_symbols = preloaded

    daily = {}
    for a in p['assets']:
        path = os.path.join(bi.MACRO_DIR, f'{a}_1d.csv')
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        df['open_time'] = pd.to_datetime(df['open_time_dt'] if 'open_time_dt' in df.columns else df['open_time'])
        df['ema'] = df['close'].ewm(span=p['ema_span'], adjust=False).mean()
        daily[a] = df[['open_time', 'close', 'ema']].sort_values('open_time').reset_index(drop=True)

    btc_times = btc_4h.sort_values('open_time')['open_time']
    all_ts = [t for t in btc_times if start <= t <= end]
    check_dates = []
    t = pd.Timestamp(start.date())
    while t <= end:
        check_dates.append(t)
        t += pd.Timedelta(days=p['check_days'])

    capital = 100000.0
    positions = {}
    trades = []
    equity = []
    total_cash_yield = 0.0
    cash_per_4h = p['annual_cash_yield'] / 2190.0

    for ts in all_ts:
        if ts in check_dates:
            signals = {}
            for a, df in daily.items():
                hist = df[df['open_time'] < ts]
                if len(hist) < p['ema_span'] + 5:
                    signals[a] = False
                    continue
                signals[a] = float(hist['close'].iloc[-1]) > float(hist['ema'].iloc[-1])

            for a in list(positions.keys()):
                if signals.get(a, False):
                    continue
                pos = positions[a]
                df4 = coins_4h_map.get(a)
                if df4 is None or ts not in df4.index:
                    continue
                exit_price = df4.loc[ts]['open'] * (1 - p['exit_slippage'])
                ret = exit_price / pos['entry_price'] - 1.0
                gross = pos['allocated'] * ret
                fee = pos['allocated'] * (1 + abs(ret)) * p['fee_pct']
                capital += gross - fee
                trades.append({
                    'entry_date': pos['entry_date'].strftime('%Y-%m-%d %H:%M'),
                    'symbol': a, 'direction': 'LONG',
                    'pnl_brl': round(gross - fee, 4),
                    'risk_brl': round(pos['allocated'], 4),
                    'fees_paid': round(fee, 4),
                    'funding_paid': round(pos['funding_paid'], 4),
                    'stop_dist_pct': 0.0, 'asset_class': bi._asset_class(a),
                    'regime_macro': 'ts', 'rsi_1d': 0.0, 'atr_1d_pct': 0.0, 'btc_adx_1d': 0.0,
                    'exit_dates': [ts.strftime('%Y-%m-%d %H:%M')],
                    'exit_reasons': ['Sinal de Saida (Trend)'],
                })
                del positions[a]

            buy_list = [a for a, sig in signals.items() if sig and a not in positions]
            if buy_list:
                alloc = capital * 0.5 / len(buy_list)
                for a in buy_list:
                    df4 = coins_4h_map.get(a)
                    if df4 is None or ts not in df4.index:
                        continue
                    entry_price = df4.loc[ts]['open'] * (1 + p['entry_slippage'])
                    entry_fee = alloc * p['fee_pct']
                    capital -= entry_fee
                    positions[a] = {'entry_date': ts, 'entry_price': entry_price,
                                    'allocated': alloc, 'funding_paid': 0.0}

        if ts.hour in [0, 8, 16]:
            for a, pos in positions.items():
                fr = funding_map.get(a)
                if fr is None:
                    continue
                sub = fr[fr['fundingTime'] == ts]
                for _, row in sub.iterrows():
                    df4 = coins_4h_map.get(a)
                    close_ref = df4.loc[ts]['close'] if df4 is not None and ts in df4.index else pos['entry_price']
                    charge = bi.funding_charge(True, pos['allocated'], 1.0, pos['entry_price'],
                                               close_ref, float(row['fundingRate']))
                    capital -= charge
                    pos['funding_paid'] += charge

        free_cash = max(capital - sum(pos['allocated'] for pos in positions.values()), 0.0)
        interest = free_cash * cash_per_4h
        capital += interest
        total_cash_yield += interest

        unreal = 0.0
        for a, pos in positions.items():
            df4 = coins_4h_map.get(a)
            if df4 is not None and ts in df4.index:
                unreal += pos['allocated'] * (df4.loc[ts]['close'] / pos['entry_price'] - 1.0)
        equity.append({'timestamp': ts, 'capital': capital + unreal})

    for a in list(positions.keys()):
        pos = positions[a]
        df4 = coins_4h_map.get(a)
        last_sub = df4[df4.index <= end] if df4 is not None else None
        if last_sub is not None and not last_sub.empty:
            c_close = last_sub.iloc[-1]['close']
            ret = c_close / pos['entry_price'] - 1.0
            gross = pos['allocated'] * ret
            fee = pos['allocated'] * (1 + abs(ret)) * p['fee_pct']
            capital += gross - fee
            trades.append({
                'entry_date': pos['entry_date'].strftime('%Y-%m-%d %H:%M'),
                'symbol': a, 'direction': 'LONG',
                'pnl_brl': round(gross - fee, 4),
                'risk_brl': round(pos['allocated'], 4),
                'fees_paid': round(fee, 4),
                'funding_paid': round(pos['funding_paid'], 4),
                'stop_dist_pct': 0.0, 'asset_class': bi._asset_class(a),
                'regime_macro': 'ts', 'rsi_1d': 0.0, 'atr_1d_pct': 0.0, 'btc_adx_1d': 0.0,
                'exit_dates': [end.strftime('%Y-%m-%d %H:%M')],
                'exit_reasons': ['Fechamento Fim do Periodo (MtM)'],
            })

    eq_df = pd.DataFrame(equity)
    eq_df['peak'] = eq_df['capital'].cummax()
    eq_df['dd'] = (eq_df['capital'] - eq_df['peak']) / eq_df['peak']
    dd = abs(eq_df['dd'].min() * 100) if len(eq_df) else 0.0
    eq_df['ret'] = eq_df['capital'].pct_change()
    rets = eq_df['ret'].dropna()
    sharpe = (rets.mean() / (rets.std() + 1e-9)) * np.sqrt(2190) if len(rets) else 0.0
    wins = [t for t in trades if t['pnl_brl'] > 0.001]
    losses = [t for t in trades if t['pnl_brl'] < -0.001]
    pf = (sum(t['pnl_brl'] for t in wins) / abs(sum(t['pnl_brl'] for t in losses))) if losses else float('inf')
    trading_pnl = sum(t['pnl_brl'] for t in trades)
    net = capital - 100000.0
    btc_ref = 0.0
    b4 = coins_4h_map.get('BTCUSDT')
    if b4 is not None:
        d_in, d_out = b4[b4.index >= start], b4[b4.index <= end]
        if not d_in.empty and not d_out.empty:
            btc_ref = (float(d_out.iloc[-1]['close']) / float(d_in.iloc[0]['close']) - 1) * 100

    results = {
        'engine_version': 'TS-TREND-1.0', 'params': p,
        'start_date': start_str, 'end_date': end_str,
        'initial_capital': 100000.0, 'final_capital': capital,
        'net_profit_brl': net, 'return_pct': net / 1000.0,
        'total_trades': len(trades), 'winning_trades': len(wins), 'losing_trades': len(losses),
        'breakeven_trades': 0,
        'win_rate_pct': (len(wins) / len(trades) * 100) if trades else 0.0,
        'win_rate_ci95_low_pct': 0.0, 'win_rate_ci95_high_pct': 0.0,
        'min_trades_warning': len(trades) < 30,
        'profit_factor': pf, 'max_drawdown_pct': dd,
        'sharpe_ratio': sharpe, 'sortino_ratio': 0.0,
        'expectancy_r': float(np.mean([t['pnl_brl'] / max(t['risk_brl'], 1e-9) for t in trades])) if trades else 0.0,
        'avg_mae_r': 0.0, 'avg_mfe_r': 0.0,
        'total_cash_yield_brl': total_cash_yield,
        'total_funding_fees_brl': sum(t['funding_paid'] for t in trades),
        'total_fees_brl': sum(t['fees_paid'] for t in trades),
        'trading_pnl_net_brl': trading_pnl,
        'trading_pnl_gross_brl': trading_pnl + sum(t['fees_paid'] for t in trades) + sum(t['funding_paid'] for t in trades),
        'bnh_btc_return_pct': btc_ref, 'bnh_eth_return_pct': 0.0,
        'coins_scanned': len(p['assets']), 'semester_checkpoints': {},
        'seg_by_regime': {}, 'seg_by_asset': {}, 'seg_by_exit': {},
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
        'expectancy_r': round(res['expectancy_r'], 3),
        'bnh_btc_pct': round(res['bnh_btc_return_pct'], 2),
    }


def run_wf(params):
    btc_4h, btc_1d, fng_df, coins_4h_map, funding_map, available_symbols = bi.load_all_data()
    preloaded = (btc_4h, coins_4h_map, funding_map, available_symbols)
    wf_results, wf_detail = {}, {}
    for name, s, e in bi.WALKFORWARD_WINDOWS:
        res, trades, eq = run_trend(s, e, params, preloaded=preloaded)
        wf_results[name] = compact(res)
        wf_detail[name] = {'trades': trades, 'equity_curve': [round(float(v), 2) for v in eq['capital'].tolist()]}
    oos = [wf_results[n] for n in OOS_NAMES]
    summary = {
        'config': params, 'config_hash': bi.config_hash(params), 'engine_version': 'TS-TREND-1.0',
        'generated_at': 'now', 'windows': wf_results, 'windows_detail': wf_detail,
        'oos_aggregate': {
            'trades_total': sum(w['trades'] for w in oos),
            'return_pct_sum': round(sum(w['return_pct'] for w in oos), 2),
            'trading_pnl_sum': round(sum(w['trading_pnl'] for w in oos), 2),
            'pf_mean': round(np.mean([w['pf'] for w in oos]), 2),
            'pf_median': round(float(np.median([w['pf'] for w in oos])), 2),
            'win_rate_mean': round(np.mean([w['win_rate'] for w in oos]), 1),
            'dd_max': round(max(w['dd_pct'] for w in oos), 2),
            'sharpe_mean': round(np.mean([w['sharpe'] for w in oos]), 2),
            'expectancy_r_mean': round(np.mean([w['expectancy_r'] for w in oos]), 3),
        },
    }
    out = os.path.join(bi.EXP_DIR, f"exp_{summary['config_hash']}.json")
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)
    for name, m in wf_results.items():
        print(f"{name:<6} {m['trades']:>5} {m['return_pct']:>9.2f} {m['trading_pnl']:>12,.2f} {m['pf']:>6.2f} "
              f"{m['win_rate']:>6.1f} {m['dd_pct']:>7.2f} {m['sharpe']:>8.2f} {m['expectancy_r']:>8.3f} {m['bnh_btc_pct']:>9.2f}")
    oa = summary['oos_aggregate']
    print(f"OOS: trades={oa['trades_total']} ret%={oa['return_pct_sum']} pnl={oa['trading_pnl_sum']:,.0f} "
          f"PF={oa['pf_mean']} DD={oa['dd_max']} Sharpe={oa['sharpe_mean']} ExpR={oa['expectancy_r_mean']}")
    print('salvo:', out)
    return summary


def main():
    configs = [
        ('ts_btc_e200_w', dict(ema_span=200, check_days=7, assets=['BTCUSDT'])),
        ('ts_btc_e252_w', dict(ema_span=252, check_days=7, assets=['BTCUSDT'])),
        ('ts_btceth_e200_w', dict(ema_span=200, check_days=7, assets=['BTCUSDT', 'ETHUSDT'])),
        ('ts_btceth_e252_w', dict(ema_span=252, check_days=7, assets=['BTCUSDT', 'ETHUSDT'])),
    ]
    for name, params in configs:
        print('\n' + '#' * 90)
        print('CONFIG', name, json.dumps(params))
        print('#' * 90)
        run_wf(params)


if __name__ == '__main__':
    main()
