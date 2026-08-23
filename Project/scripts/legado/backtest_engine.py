"""
Quantitative Backtest Engine for All 9 Assets with 5.0% Fixed Risk & Binance Trading Fees
Assets: SOL, SUI, ILV, NEAR, APT, GALA, INJ, PENDLE, TON (180 Days)
Fee: 0.075% on entry and 0.075% on exit (Binance Spot/Futures standard)
"""

import datetime
import os
import sys
import pandas as pd

# Garante importação do backtest_180d independentemente do CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backtest_180d import fetch_klines_extended, fetch_funding_rates_extended, fetch_fear_and_greed, compute_indicators_4h, compute_indicators_1d

def is_vesting_cliff_all(symbol, dt):
    if 'SUI' in symbol:
        next_month = dt.month + 1 if dt.month < 12 else 1
        next_year = dt.year if dt.month < 12 else dt.year + 1
        next_first = datetime.datetime(next_year, next_month, 1)
        this_first = datetime.datetime(dt.year, dt.month, 1)
        days_to_next = (next_first - dt).total_seconds() / 86400
        days_from_this = (dt - this_first).total_seconds() / 86400
        if days_to_next <= 7 or days_from_this <= 1:
            return True, "Desbloqueio de Vesting SUI > 1% (Cliff mensal no dia 1)"
    elif 'APT' in symbol:
        if 5 <= dt.day <= 13:
            return True, "Desbloqueio de Vesting APT > 1% (Cliff mensal no dia 11/12)"
    elif 'ILV' in symbol:
        if dt.month in [3, 6, 8] and 20 <= dt.day <= 28:
            return True, "Janela de Desbloqueio ILV > 1%"
    elif 'GALA' in symbol:
        if dt.month in [4, 7] and 15 <= dt.day <= 25:
            return True, "Janela de Desbloqueio GALA > 1%"
    return False, ""

def run_single_asset_backtest_5pct(symbol, btc_4h, btc_1d, fng_df, risk_pct=0.05, fee_pct=0.00075):
    df_4h = compute_indicators_4h(fetch_klines_extended(symbol, interval='4h', total_candles=1600))
    df_1d = compute_indicators_1d(fetch_klines_extended(symbol, interval='1d', total_candles=400))
    funding_data = fetch_funding_rates_extended(symbol)
    
    start_date = pd.to_datetime("2026-02-20 00:00:00")
    end_date = pd.to_datetime("2026-08-19 23:59:59")
    
    initial_capital = 200.0
    capital = initial_capital
    
    trades = []
    active_pos = None
    
    all_timestamps = df_4h[(df_4h['open_time'] >= start_date) & (df_4h['open_time'] <= end_date)]['open_time'].tolist()
    equity_curve = [{'timestamp': start_date, 'capital': capital}]
    
    p_start = df_4h[df_4h['open_time'] >= start_date].iloc[0]['open']
    p_end = df_4h[df_4h['open_time'] <= end_date].iloc[-1]['close']
    bnh_return = (p_end - p_start) / p_start * 100
    
    for current_time in all_timestamps:
        btc_sub_1d = btc_1d[btc_1d['open_time'] < current_time]  # LOOKAHEAD FIX: BTC macro
        btc_sub_4h = btc_4h[btc_4h['open_time'] < current_time]  # LOOKAHEAD FIX: BTC macro
        if len(btc_sub_1d) == 0 or len(btc_sub_4h) == 0:
            continue
            
        btc_last_1d = btc_sub_1d.iloc[-1]
        btc_last_4h = btc_sub_4h.iloc[-1]
        btc_macro_bullish = btc_last_1d['close'] >= btc_last_1d['ema50_1d']
        btc_macro_support_lost = btc_last_1d['close'] < btc_last_1d['ema50_1d'] * 0.97
        
        fng_val = 50.0
        if not fng_df.empty:
            fng_sub = fng_df[fng_df['timestamp'] <= current_time]
            if not fng_sub.empty:
                fng_val = fng_sub.iloc[-1]['value']
                
        # 1. Manage Active Position
        if active_pos is not None:
            current_candle = df_4h[df_4h['open_time'] == current_time]
            if not current_candle.empty:
                candle = current_candle.iloc[0]
                c_high = candle['high']
                c_low = candle['low']
                c_close = candle['close']
                c_ema20 = candle['ema20']
                c_rsi = candle['rsi14']
                
                fr_val = 0.0001
                if not funding_data.empty:
                    fr_sub = funding_data[funding_data['fundingTime'] <= current_time]
                    if not fr_sub.empty:
                        fr_val = fr_sub.iloc[-1]['fundingRate']
                        
                entry_price = active_pos['entry_price']
                stop_loss = active_pos['stop_loss']
                target_1 = active_pos['target_1']
                target_2 = active_pos['target_2']
                be_trigger_price = active_pos['be_trigger_price']
                allocated_capital = active_pos['allocated_capital']
                
                active_pos['candles_held'] += 1
                
                # Custo de Financiamento (Funding Rate) a cada 8h (00:00, 08:00, 16:00 UTC)
                if current_time.hour in [0, 8, 16] and not funding_data.empty:
                    rem_pct_funding = 0.5 if active_pos['partial_taken'] else 1.0
                    current_notional = (allocated_capital * rem_pct_funding) * (c_close / entry_price)
                    funding_fee = current_notional * fr_val
                    capital -= funding_fee
                    active_pos['pnl_brl'] -= funding_fee
                    active_pos['funding_paid'] = active_pos.get('funding_paid', 0.0) + funding_fee
                
                # Abordagem Pessimista: Stop Loss tem prioridade MÁXIMA sobre qualquer saída intra-candle.
                # Se c_low <= stop na mesma vela que RSI > 75, assume-se que o stop foi atingido primeiro.
                if c_low <= active_pos['stop_loss']:
                    stop_slippage = 0.0008  # 8 bps de slippage adverso na ordem Stop-Market em dump rápido
                    stop_exec_price = active_pos['stop_loss'] * (1 - stop_slippage)
                    if not active_pos['partial_taken']:
                        pct_loss = (stop_exec_price - entry_price) / entry_price
                        gross_pnl = allocated_capital * pct_loss
                        exit_fee = (allocated_capital * (1 + pct_loss)) * fee_pct
                        pnl_brl = gross_pnl - exit_fee
                        capital += pnl_brl
                        active_pos['exit_dates'].append(current_time)
                        active_pos['exit_prices'].append(stop_exec_price)
                        active_pos['exit_reasons'].append("Stop no Breakeven (Pessimista)" if active_pos['be_moved'] else "Stop Loss Inicial (Pessimista)")
                        active_pos['pnl_brl'] += pnl_brl
                        active_pos['final_capital'] = capital
                        active_pos['status'] = 'CLOSED'
                        trades.append(active_pos)
                        active_pos = None
                    else:
                        pct_loss = (stop_exec_price - entry_price) / entry_price
                        gross_pnl = (allocated_capital * 0.5) * pct_loss
                        exit_fee = (allocated_capital * 0.5 * (1 + pct_loss)) * fee_pct
                        pnl_brl = gross_pnl - exit_fee
                        capital += pnl_brl
                        active_pos['pnl_brl'] += pnl_brl
                        active_pos['exit_dates'].append(current_time)
                        active_pos['exit_prices'].append(stop_exec_price)
                        active_pos['exit_reasons'].append("Stop Breakeven 0x0 2ª metade (Pessimista)")
                        active_pos['final_capital'] = capital
                        active_pos['status'] = 'CLOSED'
                        trades.append(active_pos)
                        active_pos = None
                elif c_rsi > 75 and fr_val > 0.0004:
                    pct_return = (c_close - entry_price) / entry_price
                    remaining_pct = 0.5 if active_pos['partial_taken'] else 1.0
                    gross_pnl = (allocated_capital * remaining_pct) * pct_return
                    exit_fee = (allocated_capital * remaining_pct * (1 + pct_return)) * fee_pct
                    pnl_brl = gross_pnl - exit_fee
                    capital += pnl_brl
                    active_pos['exit_dates'].append(current_time)
                    active_pos['exit_prices'].append(c_close)
                    active_pos['exit_reasons'].append("Exaustão RSI > 75 & FR Alto")
                    active_pos['pnl_brl'] += pnl_brl
                    active_pos['final_capital'] = capital
                    active_pos['status'] = 'CLOSED'
                    trades.append(active_pos)
                    active_pos = None
                elif active_pos['candles_held'] >= 84 and not active_pos['partial_taken']:
                    pct_return = (c_close - entry_price) / entry_price
                    gross_pnl = allocated_capital * pct_return
                    exit_fee = (allocated_capital * (1 + pct_return)) * fee_pct
                    pnl_brl = gross_pnl - exit_fee
                    capital += pnl_brl
                    active_pos['exit_dates'].append(current_time)
                    active_pos['exit_prices'].append(c_close)
                    active_pos['exit_reasons'].append("Time-Stop (14d)")
                    active_pos['pnl_brl'] += pnl_brl
                    active_pos['final_capital'] = capital
                    active_pos['status'] = 'CLOSED'
                    trades.append(active_pos)
                    active_pos = None
                else:
                    # Movimenta Breakeven SE não foi estopado
                    if not active_pos['be_moved'] and c_high >= be_trigger_price:
                        active_pos['be_moved'] = True
                        active_pos['stop_loss'] = entry_price
                        
                    if not active_pos['partial_taken']:
                        if c_high >= target_1:
                            active_pos['partial_taken'] = True
                            active_pos['be_moved'] = True
                            active_pos['stop_loss'] = entry_price
                            pct_gain_1 = (target_1 - entry_price) / entry_price
                            gross_pnl_1 = (allocated_capital * 0.5) * pct_gain_1
                            exit_fee_1 = (allocated_capital * 0.5 * (1 + pct_gain_1)) * fee_pct
                            pnl_1 = gross_pnl_1 - exit_fee_1
                            capital += pnl_1
                            active_pos['pnl_brl'] += pnl_1
                            active_pos['exit_dates'].append(current_time)
                            active_pos['exit_prices'].append(target_1)
                            active_pos['exit_reasons'].append(f"Alvo 1 ({active_pos['rr_target1']}R)")
                            
                            if c_high >= target_2:
                                pct_gain_2 = (target_2 - entry_price) / entry_price
                                gross_pnl_2 = (allocated_capital * 0.5) * pct_gain_2
                                exit_fee_2 = (allocated_capital * 0.5 * (1 + pct_gain_2)) * fee_pct
                                pnl_2 = gross_pnl_2 - exit_fee_2
                                capital += pnl_2
                                active_pos['pnl_brl'] += pnl_2
                                active_pos['exit_dates'].append(current_time)
                                active_pos['exit_prices'].append(target_2)
                                active_pos['exit_reasons'].append("Alvo 2")
                                active_pos['final_capital'] = capital
                                active_pos['status'] = 'CLOSED'
                                trades.append(active_pos)
                                active_pos = None
                    else:
                        if c_high >= target_2:
                            pct_gain_2 = (target_2 - entry_price) / entry_price
                            gross_pnl_2 = (allocated_capital * 0.5) * pct_gain_2
                            exit_fee_2 = (allocated_capital * 0.5 * (1 + pct_gain_2)) * fee_pct
                            pnl_2 = gross_pnl_2 - exit_fee_2
                            capital += pnl_2
                            active_pos['pnl_brl'] += pnl_2
                            active_pos['exit_dates'].append(current_time)
                            active_pos['exit_prices'].append(target_2)
                            active_pos['exit_reasons'].append("Alvo 2")
                            active_pos['final_capital'] = capital
                            active_pos['status'] = 'CLOSED'
                            trades.append(active_pos)
                            active_pos = None
                        elif c_close < c_ema20:
                            pct_gain_trail = (c_close - entry_price) / entry_price
                            gross_pnl_trail = (allocated_capital * 0.5) * pct_gain_trail
                            exit_fee_trail = (allocated_capital * 0.5 * (1 + pct_gain_trail)) * fee_pct
                            pnl_trail = gross_pnl_trail - exit_fee_trail
                            capital += pnl_trail
                            active_pos['pnl_brl'] += pnl_trail
                            active_pos['exit_dates'].append(current_time)
                            active_pos['exit_prices'].append(c_close)
                            active_pos['exit_reasons'].append("Trailing EMA20")
                            active_pos['final_capital'] = capital
                            active_pos['status'] = 'CLOSED'
                            trades.append(active_pos)
                            active_pos = None
                            
        # 2. Evaluate Signals
        if active_pos is None:
            sub_4h = df_4h[df_4h['open_time'] < current_time]  # LOOKAHEAD FIX
            sub_1d = df_1d[df_1d['open_time'] < current_time]  # LOOKAHEAD FIX
            if len(sub_4h) >= 50 and len(sub_1d) >= 30:
                current_open_candle = df_4h[df_4h['open_time'] == current_time]
                if current_open_candle.empty:
                    continue
                entry_candle_open = current_open_candle.iloc[0]['open']

                candle = sub_4h.iloc[-1]  # This is now the PREVIOUS closed candle (current_time - 4h)
                prev_candle = sub_4h.iloc[-2]
                candle_1d = sub_1d.iloc[-1]
                
                veto_reasons = []
                is_vest, _ = is_vesting_cliff_all(symbol, current_time)
                if is_vest: veto_reasons.append("Vesting")
                fr_val = 0.0001
                if not funding_data.empty:
                    fr_sub = funding_data[funding_data['fundingTime'] <= current_time]
                    if not fr_sub.empty: fr_val = fr_sub.iloc[-1]['fundingRate']
                if fr_val > 0.0003: veto_reasons.append("Funding")
                if btc_macro_support_lost: veto_reasons.append("BTC Support Lost")
                if candle['close'] < candle['ema50'] and candle['vol_ratio'] < 1.3: veto_reasons.append("EMA50 vol")
                
                macro_score = 12 if btc_macro_bullish else (8 if btc_last_4h['close'] >= btc_last_4h['ema20'] else 0)
                macro_score += 8 if fng_val >= 40 else (4 if fng_val >= 25 else 0)
                ema_aligned = (candle['ema20'] > candle['ema50']) and (candle['close'] > candle['ema20'])
                ema_major_aligned = (candle['ema50'] > candle['ema200']) or (candle['close'] > candle['ema200'])
                tech_score = 12 if (ema_aligned and ema_major_aligned) else (7 if candle['close'] > candle['ema20'] else 0)
                
                rsi_val, adx_val = candle['rsi14'], candle['adx14']
                if 45 <= rsi_val <= 65: tech_score += 10
                elif rsi_val < 40 and candle['close'] > candle['open'] and candle['low'] <= candle['swing_low_10'] * 1.01: tech_score += 8
                elif 65 < rsi_val <= 70: tech_score += 5
                tech_score += 8 if candle_1d['close'] > candle_1d['ema50_1d'] else (4 if candle_1d['close'] > candle_1d['ema20_1d'] else 0)
                deriv_score = 15 if fr_val <= 0.0001 else (8 if fr_val <= 0.0002 else 0)
                deriv_score += 10 if (candle['cvd'] > 0 and candle['vol_ratio'] > 1.0) else (6 if candle['cvd'] > 0 else 0)
                onchain_score = 25
                total_score = macro_score + tech_score + deriv_score + onchain_score
                
                entry_price = entry_candle_open * 1.0005  # LOOKAHEAD FIX + Slippage de 5 bps
                stop_loss = candle['swing_low_10'] - (1.5 * candle['atr14'])
                stop_dist = entry_price - stop_loss
                if stop_dist <= 0:
                    continue  # Guard: stop acima do entry — trade inválido
                stop_dist_pct = stop_dist / entry_price
                if stop_dist_pct < 0.012:
                    stop_loss = entry_price * 0.985
                    stop_dist = entry_price - stop_loss
                    stop_dist_pct = 0.015
                    
                is_strong_trend = btc_macro_bullish and (adx_val > 20)
                rr_target1 = 2.5 if is_strong_trend else 1.8
                rr_target2 = 4.0 if is_strong_trend else 2.8
                be_trigger_price = entry_price + stop_dist
                target_1 = entry_price + (rr_target1 * stop_dist)
                target_2 = entry_price + (rr_target2 * stop_dist)
                
                trend_trigger = (candle['close'] > candle['ema20']) and (candle['close'] > prev_candle['high']) and (48 <= rsi_val <= 68) and (candle['close'] > candle['ema50'])
                reversal_trigger = (prev_candle['rsi14'] < 40) and (candle['close'] > prev_candle['high']) and (candle['close'] > candle['open'])
                
                if (trend_trigger or reversal_trigger) and total_score >= 75 and len(veto_reasons) == 0:
                    risk_brl = capital * risk_pct # 5% risk
                    allocated_capital = min(risk_brl / stop_dist_pct, capital * 2.5) # max 2.5x leverage
                    entry_fee = allocated_capital * fee_pct
                    capital -= entry_fee # Pay entry fee
                    
                    active_pos = {
                        'symbol': symbol, 'entry_date': current_time, 'entry_price': entry_price,
                        'stop_loss': stop_loss, 'stop_dist': stop_dist, 'stop_dist_pct': stop_dist_pct,
                        'be_trigger_price': be_trigger_price, 'be_moved': False,
                        'target_1': target_1, 'target_2': target_2, 'rr_target1': rr_target1,
                        'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                        'score': total_score, 'candles_held': 0, 'partial_taken': False,
                        'exit_dates': [], 'exit_prices': [], 'exit_reasons': [], 'pnl_brl': -entry_fee, 'status': 'OPEN',
                        'funding_paid': 0.0
                    }
                    
        # Curva de Patrimônio Mark-to-Market (Capital Realizado + PnL Não-Realizado a cada 4h)
        unrealized_pnl = 0.0
        if active_pos is not None:
            c_curr_cand = df_4h[df_4h['open_time'] == current_time]
            if not c_curr_cand.empty:
                c_close_now = c_curr_cand.iloc[0]['close']
                rem_pct_now = 0.5 if active_pos['partial_taken'] else 1.0
                pct_ret_now = (c_close_now - active_pos['entry_price']) / active_pos['entry_price']
                unrealized_pnl = (active_pos['allocated_capital'] * rem_pct_now) * pct_ret_now
                
        total_mtm_equity = capital + unrealized_pnl
        equity_curve.append({
            'timestamp': current_time,
            'capital': total_mtm_equity,
            'realized_capital': capital,
            'unrealized_pnl': unrealized_pnl
        })
        
    if active_pos is not None:
        last_candle = df_4h[df_4h['open_time'] <= end_date].iloc[-1]
        c_close = last_candle['close']
        remaining_pct = 0.5 if active_pos['partial_taken'] else 1.0
        pct_return = (c_close - active_pos['entry_price']) / active_pos['entry_price']
        gross_pnl = (active_pos['allocated_capital'] * remaining_pct) * pct_return
        exit_fee = (active_pos['allocated_capital'] * remaining_pct * (1 + pct_return)) * fee_pct
        pnl_brl = gross_pnl - exit_fee
        capital += pnl_brl
        active_pos['pnl_brl'] += pnl_brl
        trades.append(active_pos)
        
    total_trades = len(trades)
    winning_trades = [t for t in trades if t['pnl_brl'] > 0.001]
    losing_trades = [t for t in trades if t['pnl_brl'] < -0.001]
    breakeven_trades = [t for t in trades if abs(t['pnl_brl']) <= 0.001]
    
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    gross_profits = sum(t['pnl_brl'] for t in winning_trades)
    gross_losses = abs(sum(t['pnl_brl'] for t in losing_trades))
    profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else (float('inf') if gross_profits > 0 else 0.0)
    
    equity_df = pd.DataFrame(equity_curve)
    equity_df['peak'] = equity_df['capital'].cummax()
    equity_df['drawdown'] = (equity_df['capital'] - equity_df['peak']) / equity_df['peak']
    max_drawdown_pct = abs(equity_df['drawdown'].min() * 100)
    
    net_profit_brl = capital - initial_capital
    return_pct = (net_profit_brl / initial_capital) * 100
    
    return {
        'symbol': symbol.replace('USDT', ''),
        'initial_capital': initial_capital,
        'final_capital': capital,
        'net_profit_brl': net_profit_brl,
        'return_pct': return_pct,
        'bnh_return_pct': bnh_return,
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'breakeven_trades': len(breakeven_trades),
        'win_rate_pct': win_rate,
        'profit_factor': profit_factor,
        'max_drawdown_pct': max_drawdown_pct
    }

def main():
    symbols = ['SOLUSDT', 'SUIUSDT', 'ILVUSDT', 'NEARUSDT', 'APTUSDT', 'GALAUSDT', 'INJUSDT', 'PENDLEUSDT', 'TONUSDT']
    btc_4h = compute_indicators_4h(fetch_klines_extended('BTCUSDT', interval='4h', total_candles=1600))
    btc_1d = compute_indicators_1d(fetch_klines_extended('BTCUSDT', interval='1d', total_candles=400))
    fng_df = fetch_fear_and_greed()
    
    results = []
    for s in symbols:
        res = run_single_asset_backtest_5pct(s, btc_4h, btc_1d, fng_df, risk_pct=0.05, fee_pct=0.00075)
        results.append(res)
        
    df_res = pd.DataFrame(results)
    df_res.to_csv('resultado_9_moedas_risco_5pct_com_taxas.csv', index=False)
    print("="*80)
    print("RESULTADO INDIVIDUAL POR MOEDA (RISCO 5.0% + TAXAS BINANCE DESCONTADAS)")
    print("="*80)
    print(df_res.to_string(index=False))

if __name__ == '__main__':
    main()
