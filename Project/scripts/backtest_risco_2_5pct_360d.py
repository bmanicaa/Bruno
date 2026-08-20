"""
Simulação Comparativa da Carteira Dinâmica (Max 3 Posições / 20 Moedas) com Risco Fixo de 2.5%
Períodos Avaliados:
1. Período 1 (360d a 180d atrás): 24/08/2025 a 20/02/2026
2. Período 2 (180d a 0d atrás): 20/02/2026 a 19/08/2026
3. Período Total Contínuo (360d a 0d): 24/08/2025 a 19/08/2026 (1 Ano Completo)
"""

import datetime
import json
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import requests

def fetch_klines(symbol, interval='4h', total_candles=2500):
    url = 'https://api.binance.com/api/v3/klines'
    all_data = []
    end_time = None
    while len(all_data) < total_candles:
        limit = min(1000, total_candles - len(all_data))
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        if end_time:
            params['endTime'] = end_time
        try:
            r = requests.get(url, params=params, timeout=8).json()
            if not r or isinstance(r, dict):
                break
            all_data = r + all_data
            end_time = r[0][0] - 1
            if len(r) < limit:
                break
        except Exception:
            break
            
    if not all_data:
        return pd.DataFrame()
        
    cols = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
            'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignored']
    df = pd.DataFrame(all_data, columns=cols).drop_duplicates(subset=['open_time']).sort_values('open_time').reset_index(drop=True)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    for c in ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'taker_buy_base']:
        df[c] = df[c].astype(float)
    return df

def fetch_funding_rates(symbol, limit=1000):
    fut_sym = '1000PEPEUSDT' if symbol == 'PEPEUSDT' else symbol
    url = 'https://fapi.binance.com/fapi/v1/fundingRate'
    params = {'symbol': fut_sym, 'limit': limit}
    try:
        r = requests.get(url, params=params, timeout=8).json()
        df = pd.DataFrame(r)
        if not df.empty and 'fundingTime' in df.columns:
            df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
            df['fundingRate'] = df['fundingRate'].astype(float)
            return df.sort_values('fundingTime').reset_index(drop=True)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def fetch_fear_and_greed():
    try:
        url = 'https://api.alternative.me/fng/?limit=400'
        r = requests.get(url, timeout=10)
        data = r.json().get('data', [])
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
        df['value'] = df['value'].astype(float)
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()

def compute_indicators_4h(df):
    if df.empty or len(df) < 50:
        return pd.DataFrame()
    df = df.copy()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi14'] = 100 - (100 / (1 + rs))
    
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(window=14).mean()
    
    plus_dm = df['high'].diff()
    minus_dm = -df['low'].diff()
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0)
    
    tr_smooth = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, min_periods=14, adjust=False).mean() / (tr_smooth + 1e-9))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, min_periods=14, adjust=False).mean() / (tr_smooth + 1e-9))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    df['adx14'] = dx.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    
    df['swing_low_10'] = df['low'].rolling(window=10).min()
    df['swing_high_10'] = df['high'].rolling(window=10).max()
    df['vol_sma20'] = df['volume'].rolling(window=20).mean()
    df['vol_ratio'] = df['volume'] / (df['vol_sma20'] + 1e-9)
    
    df['taker_sell_base'] = df['volume'] - df['taker_buy_base']
    df['delta_vol'] = df['taker_buy_base'] - df['taker_sell_base']
    df['cvd'] = df['delta_vol'].rolling(window=6).sum()
    return df

def compute_indicators_1d(df):
    if df.empty or len(df) < 30:
        return pd.DataFrame()
    df = df.copy()
    df['ema20_1d'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50_1d'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200_1d'] = df['close'].ewm(span=200, adjust=False).mean()
    return df

def is_vesting_cliff(symbol, dt):
    if 'SUI' in symbol:
        next_month = dt.month + 1 if dt.month < 12 else 1
        next_year = dt.year if dt.month < 12 else dt.year + 1
        next_first = datetime.datetime(next_year, next_month, 1)
        this_first = datetime.datetime(dt.year, dt.month, 1)
        days_to_next = (next_first - dt).total_seconds() / 86400
        days_from_this = (dt - this_first).total_seconds() / 86400
        if days_to_next <= 7 or days_from_this <= 1:
            return True, "Desbloqueio SUI > 1% (Cliff mensal dia 1)"
    elif 'APT' in symbol:
        if 5 <= dt.day <= 13:
            return True, "Desbloqueio APT > 1% (Cliff mensal dia 11/12)"
    elif 'ARB' in symbol:
        if 9 <= dt.day <= 17:
            return True, "Desbloqueio ARB > 1% (Cliff mensal dia 16)"
    elif 'OP' in symbol and not 'PEPE' in symbol:
        if dt.day >= 24:
            return True, "Desbloqueio OP > 1% (Cliff no fim do mês)"
    elif 'GALA' in symbol:
        if dt.month in [4, 7, 10, 1] and 15 <= dt.day <= 25:
            return True, "Janela de Emissão GALA > 1%"
    return False, ""

def simulate_engine(data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, start_date, end_date, initial_capital=200.0, risk_pct=0.025, fee_pct=0.00075, max_positions=3):
    capital = initial_capital
    trades = []
    vetoes = []
    active_positions = {}
    
    ref_sym = 'BTCUSDT'
    all_timestamps = data_4h[ref_sym][(data_4h[ref_sym]['open_time'] >= start_date) & 
                                      (data_4h[ref_sym]['open_time'] <= end_date)]['open_time'].tolist()
                                      
    equity_curve = [{'timestamp': start_date, 'capital': capital, 'active_count': 0}]
    
    for current_time in all_timestamps:
        btc_sub_1d = btc_1d[btc_1d['open_time'] <= current_time]
        btc_sub_4h = btc_4h[btc_4h['open_time'] <= current_time]
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
                
        # 1. Gerenciar Posições Abertas
        for s in list(active_positions.keys()):
            pos = active_positions[s]
            df_sym_4h = data_4h[s]
            current_candle = df_sym_4h[df_sym_4h['open_time'] == current_time]
            if current_candle.empty:
                continue
            candle = current_candle.iloc[0]
            
            c_high = candle['high']
            c_low = candle['low']
            c_close = candle['close']
            c_ema20 = candle['ema20']
            c_rsi = candle['rsi14']
            
            fr_val = 0.0001
            if not funding_data[s].empty:
                fr_sub = funding_data[s][funding_data[s]['fundingTime'] <= current_time]
                if not fr_sub.empty:
                    fr_val = fr_sub.iloc[-1]['fundingRate']
                    
            entry_price = pos['entry_price']
            target_1 = pos['target_1']
            target_2 = pos['target_2']
            be_trigger_price = pos['be_trigger_price']
            allocated_capital = pos['allocated_capital']
            
            pos['candles_held'] += 1
            
            if c_rsi > 75 and fr_val > 0.0004:
                pct_return = (c_close - entry_price) / entry_price
                remaining_pct = 0.5 if pos['partial_taken'] else 1.0
                gross_pnl = (allocated_capital * remaining_pct) * pct_return
                exit_fee = (allocated_capital * remaining_pct * (1 + pct_return)) * fee_pct
                pnl_brl = gross_pnl - exit_fee
                capital += pnl_brl
                pos['exit_dates'].append(current_time)
                pos['exit_prices'].append(c_close)
                pos['exit_reasons'].append("Exaustão RSI > 75 & FR Alto")
                pos['pnl_brl'] += pnl_brl
                pos['final_capital'] = capital
                pos['status'] = 'CLOSED'
                trades.append(pos)
                del active_positions[s]
            elif pos['candles_held'] >= 84 and not pos['partial_taken']:
                pct_return = (c_close - entry_price) / entry_price
                gross_pnl = allocated_capital * pct_return
                exit_fee = (allocated_capital * (1 + pct_return)) * fee_pct
                pnl_brl = gross_pnl - exit_fee
                capital += pnl_brl
                pos['exit_dates'].append(current_time)
                pos['exit_prices'].append(c_close)
                pos['exit_reasons'].append("Time-Stop (14d)")
                pos['pnl_brl'] += pnl_brl
                pos['final_capital'] = capital
                pos['status'] = 'CLOSED'
                trades.append(pos)
                del active_positions[s]
            else:
                if not pos['be_moved'] and c_high >= be_trigger_price:
                    pos['be_moved'] = True
                    pos['stop_loss'] = entry_price
                    
                if not pos['partial_taken']:
                    if c_low <= pos['stop_loss']:
                        pct_loss = (pos['stop_loss'] - entry_price) / entry_price
                        gross_pnl = allocated_capital * pct_loss
                        exit_fee = (allocated_capital * (1 + pct_loss)) * fee_pct
                        pnl_brl = gross_pnl - exit_fee
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(pos['stop_loss'])
                        pos['exit_reasons'].append("Stop no Breakeven" if pos['be_moved'] else "Stop Loss Inicial")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                    elif c_high >= target_1:
                        pos['partial_taken'] = True
                        pos['be_moved'] = True
                        pos['stop_loss'] = entry_price
                        pct_gain_1 = (target_1 - entry_price) / entry_price
                        gross_pnl_1 = (allocated_capital * 0.5) * pct_gain_1
                        exit_fee_1 = (allocated_capital * 0.5 * (1 + pct_gain_1)) * fee_pct
                        pnl_1 = gross_pnl_1 - exit_fee_1
                        capital += pnl_1
                        pos['pnl_brl'] += pnl_1
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(target_1)
                        pos['exit_reasons'].append(f"Alvo 1 ({pos['rr_target1']}R)")
                        
                        if c_high >= target_2:
                            pct_gain_2 = (target_2 - entry_price) / entry_price
                            gross_pnl_2 = (allocated_capital * 0.5) * pct_gain_2
                            exit_fee_2 = (allocated_capital * 0.5 * (1 + pct_gain_2)) * fee_pct
                            pnl_2 = gross_pnl_2 - exit_fee_2
                            capital += pnl_2
                            pos['pnl_brl'] += pnl_2
                            pos['exit_dates'].append(current_time)
                            pos['exit_prices'].append(target_2)
                            pos['exit_reasons'].append("Alvo 2")
                            pos['final_capital'] = capital
                            pos['status'] = 'CLOSED'
                            trades.append(pos)
                            del active_positions[s]
                else:
                    if c_low <= pos['stop_loss']:
                        exit_fee = (allocated_capital * 0.5) * fee_pct
                        pnl_brl = -exit_fee
                        capital += pnl_brl
                        pos['pnl_brl'] += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(pos['stop_loss'])
                        pos['exit_reasons'].append("Stop Breakeven (0x0 na 2ª metade)")
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                    elif c_high >= target_2:
                        pct_gain_2 = (target_2 - entry_price) / entry_price
                        gross_pnl_2 = (allocated_capital * 0.5) * pct_gain_2
                        exit_fee_2 = (allocated_capital * 0.5 * (1 + pct_gain_2)) * fee_pct
                        pnl_2 = gross_pnl_2 - exit_fee_2
                        capital += pnl_2
                        pos['pnl_brl'] += pnl_2
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(target_2)
                        pos['exit_reasons'].append("Alvo 2")
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                    elif c_close < c_ema20:
                        pct_gain_trail = (c_close - entry_price) / entry_price
                        gross_pnl_trail = (allocated_capital * 0.5) * pct_gain_trail
                        exit_fee_trail = (allocated_capital * 0.5 * (1 + pct_gain_trail)) * fee_pct
                        pnl_trail = gross_pnl_trail - exit_fee_trail
                        capital += pnl_trail
                        pos['pnl_brl'] += pnl_trail
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(c_close)
                        pos['exit_reasons'].append("Trailing EMA20")
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        
        # 2. Avaliar e Rankear Candidatos
        candidates = []
        for s in data_4h.keys():
            if s == 'BTCUSDT' or s in active_positions:
                continue
                
            df_sym_4h = data_4h[s]
            df_sym_1d = data_1d[s]
            sub_4h = df_sym_4h[df_sym_4h['open_time'] <= current_time]
            sub_1d = df_sym_1d[df_sym_1d['open_time'] <= current_time]
            if len(sub_4h) < 50 or len(sub_1d) < 30:
                continue
                
            candle = sub_4h.iloc[-1]
            prev_candle = sub_4h.iloc[-2]
            candle_1d = sub_1d.iloc[-1]
            
            veto_reasons = []
            is_vest, vest_msg = is_vesting_cliff(s, current_time)
            if is_vest:
                veto_reasons.append(f"Vesting ({vest_msg})")
                
            fr_val = 0.0001
            if not funding_data[s].empty:
                fr_sub = funding_data[s][funding_data[s]['fundingTime'] <= current_time]
                if not fr_sub.empty:
                    fr_val = fr_sub.iloc[-1]['fundingRate']
            if fr_val > 0.0003:
                veto_reasons.append(f"Funding Rate Alto ({fr_val*100:.4f}% > 0.03%)")
            if btc_macro_support_lost:
                veto_reasons.append("Suporte Macro do BTC Perdido (< EMA50 1D -3%)")
            if candle['close'] < candle['ema50'] and candle['vol_ratio'] < 1.3:
                veto_reasons.append("Preço < EMA50 4h sem Volume Agressor (Ratio < 1.3)")
                
            macro_score = 12 if btc_macro_bullish else (8 if btc_last_4h['close'] >= btc_last_4h['ema20'] else 0)
            macro_score += 8 if fng_val >= 40 else (4 if fng_val >= 25 else 0)
            
            ema_aligned = (candle['ema20'] > candle['ema50']) and (candle['close'] > candle['ema20'])
            ema_major_aligned = (candle['ema50'] > candle['ema200']) or (candle['close'] > candle['ema200'])
            tech_score = 12 if (ema_aligned and ema_major_aligned) else (7 if candle['close'] > candle['ema20'] else 0)
            
            rsi_val, adx_val = candle['rsi14'], candle['adx14']
            if 45 <= rsi_val <= 65:
                tech_score += 10
            elif rsi_val < 40 and candle['close'] > candle['open'] and candle['low'] <= candle['swing_low_10'] * 1.01:
                tech_score += 8
            elif 65 < rsi_val <= 70:
                tech_score += 5
            tech_score += 8 if candle_1d['close'] > candle_1d['ema50_1d'] else (4 if candle_1d['close'] > candle_1d['ema20_1d'] else 0)
            
            deriv_score = 15 if fr_val <= 0.0001 else (8 if fr_val <= 0.0002 else 0)
            deriv_score += 10 if (candle['cvd'] > 0 and candle['vol_ratio'] > 1.0) else (6 if candle['cvd'] > 0 else 0)
            
            onchain_score = 25
            total_score = macro_score + tech_score + deriv_score + onchain_score
            
            entry_price = candle['close']
            stop_loss = candle['swing_low_10'] - (1.5 * candle['atr14'])
            stop_dist = entry_price - stop_loss
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
            
            regime_str = "Tendência (2.5R)" if is_strong_trend else "Consolidação (1.8R)"
            
            if (trend_trigger or reversal_trigger):
                if total_score >= 75 and len(veto_reasons) == 0:
                    candidates.append({
                        'symbol': s, 'score': total_score, 'entry_price': entry_price,
                        'stop_loss': stop_loss, 'stop_dist': stop_dist, 'stop_dist_pct': stop_dist_pct,
                        'be_trigger_price': be_trigger_price, 'target_1': target_1, 'target_2': target_2,
                        'rr_target1': rr_target1, 'regime': regime_str
                    })
                else:
                    vetoes.append(1)
                    
        # 3. Alocação
        if candidates and len(active_positions) < max_positions:
            candidates.sort(key=lambda x: x['score'], reverse=True)
            available_slots = max_positions - len(active_positions)
            selected_candidates = candidates[:available_slots]
            
            for c in selected_candidates:
                risk_brl = capital * risk_pct  # Risco de 2.5%
                allocated_capital = min(risk_brl / c['stop_dist_pct'], capital * 2.5)
                entry_fee = allocated_capital * fee_pct
                capital -= entry_fee
                
                active_positions[c['symbol']] = {
                    'symbol': c['symbol'], 'entry_date': current_time, 'entry_price': c['entry_price'],
                    'stop_loss': c['stop_loss'], 'stop_dist': c['stop_dist'], 'stop_dist_pct': c['stop_dist_pct'],
                    'be_trigger_price': c['be_trigger_price'], 'be_moved': False,
                    'target_1': c['target_1'], 'target_2': c['target_2'], 'rr_target1': c['rr_target1'], 'regime': c['regime'],
                    'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                    'score': c['score'], 'candles_held': 0, 'partial_taken': False,
                    'exit_dates': [], 'exit_prices': [], 'exit_reasons': [], 'pnl_brl': -entry_fee, 'status': 'OPEN'
                }
                
        equity_curve.append({
            'timestamp': current_time,
            'capital': capital,
            'active_count': len(active_positions)
        })
        
    for s, pos in list(active_positions.items()):
        df_sym_4h = data_4h[s]
        last_candle = df_sym_4h[df_sym_4h['open_time'] <= end_date].iloc[-1]
        c_close = last_candle['close']
        remaining_pct = 0.5 if pos['partial_taken'] else 1.0
        pct_return = (c_close - pos['entry_price']) / pos['entry_price']
        gross_pnl = (pos['allocated_capital'] * remaining_pct) * pct_return
        exit_fee = (pos['allocated_capital'] * remaining_pct * (1 + pct_return)) * fee_pct
        pnl_brl = gross_pnl - exit_fee
        capital += pnl_brl
        pos['exit_dates'].append(last_candle['open_time'])
        pos['exit_prices'].append(c_close)
        pos['exit_reasons'].append("Fechamento Fim do Período (MtM)")
        pos['pnl_brl'] += pnl_brl
        pos['final_capital'] = capital
        pos['status'] = 'CLOSED'
        trades.append(pos)
        del active_positions[s]
        
    total_trades = len(trades)
    winning_trades = [t for t in trades if t['pnl_brl'] > 0.001]
    losing_trades = [t for t in trades if t['pnl_brl'] < -0.001]
    
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    gross_profits = sum(t['pnl_brl'] for t in winning_trades)
    gross_losses = abs(sum(t['pnl_brl'] for t in losing_trades))
    profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else (float('inf') if gross_profits > 0 else 0.0)
    
    equity_df = pd.DataFrame(equity_curve)
    equity_df['peak'] = equity_df['capital'].cummax()
    equity_df['drawdown'] = (equity_df['capital'] - equity_df['peak']) / equity_df['peak']
    max_drawdown_pct = abs(equity_df['drawdown'].min() * 100)
    peak_capital = equity_df['capital'].max()
    
    net_profit_brl = capital - initial_capital
    return_pct = (net_profit_brl / initial_capital) * 100
    
    return {
        'initial_capital': initial_capital,
        'final_capital': capital,
        'net_profit_brl': net_profit_brl,
        'return_pct': return_pct,
        'peak_capital': peak_capital,
        'peak_gain_pct': ((peak_capital - initial_capital) / initial_capital) * 100,
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate_pct': win_rate,
        'profit_factor': profit_factor,
        'max_drawdown_pct': max_drawdown_pct,
        'total_vetoes': len(vetoes)
    }

def main():
    symbols = [
        'SOLUSDT', 'ETHUSDT', 'BNBUSDT', 'NEARUSDT', 'AVAXUSDT', 'SUIUSDT', 'APTUSDT', 'ARBUSDT',
        'OPUSDT', 'RENDERUSDT', 'FETUSDT', 'ONDOUSDT', 'LINKUSDT', 'AAVEUSDT', 'INJUSDT',
        'PENDLEUSDT', 'TIAUSDT', 'PEPEUSDT', 'GALAUSDT', 'TONUSDT'
    ]
    
    print("="*80)
    print("EXECUTANDO SIMULAÇÃO DE RISCO 2.5% PARA TODOS OS HORIZONTES TEMPORAIS")
    print("================================================================================")
    
    print("\n1. Baixando histórico completo de 360 dias...")
    btc_4h = compute_indicators_4h(fetch_klines('BTCUSDT', interval='4h', total_candles=2500))
    btc_1d = compute_indicators_1d(fetch_klines('BTCUSDT', interval='1d', total_candles=600))
    fng_df = fetch_fear_and_greed()
    
    data_4h = {}
    data_1d = {}
    funding_data = {}
    
    def download_sym(sym):
        try:
            df4 = fetch_klines(sym, interval='4h', total_candles=2500)
            df1 = fetch_klines(sym, interval='1d', total_candles=600)
            fr = fetch_funding_rates(sym)
            ind4 = compute_indicators_4h(df4)
            ind1 = compute_indicators_1d(df1)
            return sym, ind4, ind1, fr
        except Exception:
            return sym, None, None, None
            
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(download_sym, symbols))
        
    for sym, ind4, ind1, fr in results:
        if ind4 is not None and not ind4.empty and ind1 is not None and not ind1.empty:
            data_4h[sym] = ind4
            data_1d[sym] = ind1
            funding_data[sym] = fr
            
    data_4h['BTCUSDT'] = btc_4h
    data_1d['BTCUSDT'] = btc_1d
    
    # Datas
    d_360 = pd.to_datetime("2025-08-24 00:00:00")
    d_180 = pd.to_datetime("2026-02-20 00:00:00")
    d_0   = pd.to_datetime("2026-08-19 23:59:59")
    
    print("\n2. Executando Período 1 (360d a 180d atrás: 24/08/2025 a 20/02/2026)...")
    res_p1_base = simulate_engine(data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, d_360, d_180, initial_capital=200.0, risk_pct=0.025)
    res_p1_100k = simulate_engine(data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, d_360, d_180, initial_capital=100000.0, risk_pct=0.025)
    
    print("3. Executando Período 2 (180d a 0d atrás: 20/02/2026 a 19/08/2026)...")
    res_p2_base = simulate_engine(data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, d_180, d_0, initial_capital=200.0, risk_pct=0.025)
    res_p2_100k = simulate_engine(data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, d_180, d_0, initial_capital=100000.0, risk_pct=0.025)
    
    print("4. Executando Período Total Contínuo (360d a 0d: 24/08/2025 a 19/08/2026 - 1 Ano Completo)...")
    res_full_base = simulate_engine(data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, d_360, d_0, initial_capital=200.0, risk_pct=0.025)
    res_full_100k = simulate_engine(data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, d_360, d_0, initial_capital=100000.0, risk_pct=0.025)
    
    comparison = {
        'periodo_1_360d_a_180d': {
            'base_200': res_p1_base,
            'escala_100k': res_p1_100k
        },
        'periodo_2_180d_a_0d': {
            'base_200': res_p2_base,
            'escala_100k': res_p2_100k
        },
        'periodo_total_360d_a_0d_continuo': {
            'base_200': res_full_base,
            'escala_100k': res_full_100k
        }
    }
    
    with open('data/resumo_estatistico_risco_2_5pct_360d.json', 'w') as f:
        json.dump(comparison, f, indent=4)
        
    print("\n" + "="*80)
    print("TABELA CONSOLIDADA — RISCO MODERADO DE 2.5% POR TRADE")
    print("="*80)
    print(f"{'Período Histórico':<35} | {'Capital Inicial':<15} | {'Saldo Final':<15} | {'Retorno (%)':<12} | {'Drawdown Máx':<12} | {'Profit Factor':<12}")
    print("-"*110)
    p1_cap = f"R$ {res_p1_100k['final_capital']:,.2f}"
    p1_ret = f"{res_p1_100k['return_pct']:+.2f}%"
    p1_dd  = f"{res_p1_100k['max_drawdown_pct']:.2f}%"
    p1_pf  = f"{res_p1_100k['profit_factor']:.2f}"
    
    p2_cap = f"R$ {res_p2_100k['final_capital']:,.2f}"
    p2_ret = f"{res_p2_100k['return_pct']:+.2f}%"
    p2_dd  = f"{res_p2_100k['max_drawdown_pct']:.2f}%"
    p2_pf  = f"{res_p2_100k['profit_factor']:.2f}"
    
    pf_cap = f"R$ {res_full_100k['final_capital']:,.2f}"
    pf_ret = f"{res_full_100k['return_pct']:+.2f}%"
    pf_dd  = f"{res_full_100k['max_drawdown_pct']:.2f}%"
    pf_pf  = f"{res_full_100k['profit_factor']:.2f}"

    print(f"{'1. 360d a 180d (Ago/25 a Fev/26)':<35} | {'R$ 100.000,00':<15} | {p1_cap:<15} | {p1_ret:<12} | {p1_dd:<12} | {p1_pf:<12}")
    print(f"{'2. 180d a 0d (Fev/26 a Ago/26)':<35} | {'R$ 100.000,00':<15} | {p2_cap:<15} | {p2_ret:<12} | {p2_dd:<12} | {p2_pf:<12}")
    print(f"{'3. Total 360d Contínuo (1 Ano)':<35} | {'R$ 100.000,00':<15} | {pf_cap:<15} | {pf_ret:<12} | {pf_dd:<12} | {pf_pf:<12}")
    print("="*80)

if __name__ == '__main__':
    main()
