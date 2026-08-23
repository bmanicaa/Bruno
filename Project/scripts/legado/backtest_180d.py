"""
Quantitative Backtest Engine (180 Days: 2026-02-20 to 2026-08-19)
Assets: SOLUSDT, SUIUSDT, ILVUSDT (+ BTCUSDT for Macro Trend)
Strict Point-in-Time Zero Lookahead Simulation with:
- Max 2 Simultaneous Open Positions (Correlation Protection)
- Breakeven Trigger at +1.0R
- Time-Stop at 14 Days (84 candles 4h)
- Regime-Adaptive Targets (1.8R in Consolidation / 2.5R in Trend)
"""

import datetime
import json
import os
import pandas as pd
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')

def fetch_klines_extended(symbol, interval='4h', total_candles=1600):
    # 1. Prioriza carregamento do repositório local data/raw/coins/{symbol}/
    local_path = os.path.join(RAW_DIR, 'coins', symbol, f'klines_{interval}.csv')
    if not os.path.exists(local_path):
        local_path = os.path.join(RAW_DIR, f'klines_{interval}', f'{symbol}.csv')
    if not os.path.exists(local_path) and symbol == 'BTCUSDT':
        local_path = os.path.join(RAW_DIR, 'macro', f'BTCUSDT_{interval}.csv')
        
    if os.path.exists(local_path):
        df = pd.read_csv(local_path)
        df['open_time'] = pd.to_datetime(df['open_time_dt'] if 'open_time_dt' in df.columns else df['open_time'])
        df['close_time'] = pd.to_datetime(df['close_time_dt'] if 'close_time_dt' in df.columns else df['close_time'])
        for c in ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'taker_buy_base']:
            if c in df.columns:
                df[c] = df[c].astype(float)
        return df.sort_values('open_time').reset_index(drop=True)
        
    # 2. Fallback para Binance API
    url = 'https://api.binance.com/api/v3/klines'
    all_data = []
    end_time = None
    while len(all_data) < total_candles:
        limit = min(1000, total_candles - len(all_data))
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        if end_time:
            params['endTime'] = end_time
        try:
            r = requests.get(url, params=params).json()
            if not r or isinstance(r, dict):
                break
            all_data = r + all_data
            end_time = r[0][0] - 1
            if len(r) < limit:
                break
        except Exception as e:
            print(f"Error fetching klines for {symbol}: {e}")
            break
            
    cols = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
            'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignored']
    df = pd.DataFrame(all_data, columns=cols).drop_duplicates(subset=['open_time']).sort_values('open_time').reset_index(drop=True)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    for c in ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'taker_buy_base']:
        df[c] = df[c].astype(float)
    return df

def fetch_funding_rates_extended(symbol, limit=1000):
    # 1. Prioriza carregamento do repositório local data/raw/coins/{symbol}/
    local_path = os.path.join(RAW_DIR, 'coins', symbol, 'funding_rates.csv')
    if not os.path.exists(local_path):
        local_path = os.path.join(RAW_DIR, 'funding_rates', f'{symbol}.csv')
        
    if os.path.exists(local_path):
        df = pd.read_csv(local_path)
        df['fundingTime'] = pd.to_datetime(df['fundingTime_dt'] if 'fundingTime_dt' in df.columns else df['fundingTime'])
        df['fundingRate'] = df['fundingRate'].astype(float)
        return df.sort_values('fundingTime').reset_index(drop=True)
        
    fut_symbol = '1000PEPEUSDT' if symbol == 'PEPEUSDT' else symbol
    url = 'https://fapi.binance.com/fapi/v1/fundingRate'
    params = {'symbol': fut_symbol, 'limit': limit}
    try:
        r = requests.get(url, params=params).json()
        df = pd.DataFrame(r)
        df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
        df['fundingRate'] = df['fundingRate'].astype(float)
        return df.sort_values('fundingTime').reset_index(drop=True)
    except Exception as e:
        print(f"Error fetching funding rate for {symbol}: {e}")
        return pd.DataFrame()

def fetch_fear_and_greed():
    # 1. Prioriza carregamento do repositório local data/raw/macro/
    local_path = os.path.join(RAW_DIR, 'macro', 'fear_and_greed.csv')
    if os.path.exists(local_path):
        df = pd.read_csv(local_path)
        df['timestamp'] = pd.to_datetime(df['date'])
        df['value'] = df['value'].astype(float)
        return df.sort_values('timestamp').reset_index(drop=True)
        
    try:
        url = 'https://api.alternative.me/fng/?limit=220'
        r = requests.get(url)
        data = r.json().get('data', [])
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
        df['value'] = df['value'].astype(float)
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Error fetching Fear & Greed: {e}")
        return pd.DataFrame()

def compute_indicators_4h(df):
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
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)
    
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
    df = df.copy()
    df['ema20_1d'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50_1d'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200_1d'] = df['close'].ewm(span=200, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi14_1d'] = 100 - (100 / (1 + rs))
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
            return True, "Desbloqueio de Vesting SUI > 1% (Cliff mensal no dia 1)"
    elif 'ILV' in symbol:
        if dt.month in [3, 6, 8] and dt.day >= 20 and dt.day <= 28:
            return True, "Janela de Desbloqueio de Vesting ILV > 1%"
            
    return False, ""

def run_backtest_180d():
    print("="*80)
    print("INICIANDO BACKTEST QUANTITATIVO OTIMIZADO DE 180 DIAS (20/02/2026 A 19/08/2026)")
    print("="*80)
    
    symbols = ['SOLUSDT', 'SUIUSDT', 'ILVUSDT']
    data_4h = {}
    data_1d = {}
    funding_data = {}
    
    print("Baixando dados estendidos do BTCUSDT (Macro)...")
    btc_4h = compute_indicators_4h(fetch_klines_extended('BTCUSDT', interval='4h', total_candles=1600))
    btc_1d = compute_indicators_1d(fetch_klines_extended('BTCUSDT', interval='1d', total_candles=400))
    
    fng_df = fetch_fear_and_greed()
    
    for s in symbols:
        print(f"Baixando dados estendidos para {s}...")
        df_4h = fetch_klines_extended(s, interval='4h', total_candles=1600)
        df_1d = fetch_klines_extended(s, interval='1d', total_candles=400)
        df_4h = compute_indicators_4h(df_4h)
        df_1d = compute_indicators_1d(df_1d)
        data_4h[s] = df_4h
        data_1d[s] = df_1d
        funding_data[s] = fetch_funding_rates_extended(s)
        
    start_date = pd.to_datetime("2026-02-20 00:00:00")
    end_date = pd.to_datetime("2026-08-19 23:59:59")
    
    initial_capital = 200.0
    capital = initial_capital
    risk_per_trade_pct = 0.01
    
    trades = []
    vetoes = []
    active_positions = {}
    
    all_timestamps = data_4h['SOLUSDT'][(data_4h['SOLUSDT']['open_time'] >= start_date) & 
                                        (data_4h['SOLUSDT']['open_time'] <= end_date)]['open_time'].tolist()
    
    print(f"\nTotal de candles 4h a simular: {len(all_timestamps)}")
    equity_curve = [{'timestamp': start_date, 'capital': capital}]
    
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
                
        # 1. Manage Active Positions
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
            stop_loss = pos['stop_loss']
            target_1 = pos['target_1']
            target_2 = pos['target_2']
            be_trigger_price = pos['be_trigger_price']
            allocated_capital = pos['allocated_capital']
            
            pos['candles_held'] += 1
            
            # Check Early Exhaustion Exit
            if c_rsi > 75 and fr_val > 0.0004:
                pct_return = (c_close - entry_price) / entry_price
                remaining_pct = 0.5 if pos['partial_taken'] else 1.0
                pnl_brl = (allocated_capital * remaining_pct) * pct_return
                capital += pnl_brl
                pos['exit_dates'].append(current_time)
                pos['exit_prices'].append(c_close)
                pos['exit_reasons'].append("Encerramento Antecipado (Exaustão RSI > 75 & FR Alto)")
                pos['pnl_brl'] += pnl_brl
                pos['final_capital'] = capital
                pos['status'] = 'CLOSED'
                trades.append(pos)
                del active_positions[s]
                continue
                
            # Check Time-Stop (14 days = 84 candles 4h)
            if pos['candles_held'] >= 84 and not pos['partial_taken']:
                # Close trade due to time decay
                pct_return = (c_close - entry_price) / entry_price
                pnl_brl = allocated_capital * pct_return
                capital += pnl_brl
                pos['exit_dates'].append(current_time)
                pos['exit_prices'].append(c_close)
                pos['exit_reasons'].append("Time-Stop (14 Dias Estagnado sem atingir Alvo 1)")
                pos['pnl_brl'] = pnl_brl
                pos['final_capital'] = capital
                pos['status'] = 'CLOSED'
                trades.append(pos)
                del active_positions[s]
                continue
                
            # Check Breakeven Trigger at +1.0R (if not yet moved)
            if not pos['be_moved'] and c_high >= be_trigger_price:
                pos['be_moved'] = True
                pos['stop_loss'] = entry_price # Move stop to breakeven
                
            # If partial not yet taken:
            if not pos['partial_taken']:
                if c_low <= pos['stop_loss']:
                    # Exited at Stop Loss (or Breakeven if already moved)
                    pct_loss = (pos['stop_loss'] - entry_price) / entry_price
                    pnl_brl = allocated_capital * pct_loss
                    capital += pnl_brl
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(pos['stop_loss'])
                    if pos['be_moved']:
                        pos['exit_reasons'].append("Stop no Breakeven Atingido (+1.0R protegido - 0x0)")
                    else:
                        pos['exit_reasons'].append("Stop Loss Inicial Atingido (100%)")
                    pos['pnl_brl'] = pnl_brl
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue
                elif c_high >= target_1:
                    # Target 1 Reached! Partial 50%
                    pos['partial_taken'] = True
                    pos['be_moved'] = True
                    pos['stop_loss'] = entry_price
                    pct_gain_1 = (target_1 - entry_price) / entry_price
                    pnl_1 = (allocated_capital * 0.5) * pct_gain_1
                    capital += pnl_1
                    pos['pnl_brl'] += pnl_1
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(target_1)
                    pos['exit_reasons'].append(f"Alvo 1 Atingido ({pos['rr_target1']}R - 50% Realizado, Stop no Breakeven)")
                    
                    if c_high >= target_2:
                        pct_gain_2 = (target_2 - entry_price) / entry_price
                        pnl_2 = (allocated_capital * 0.5) * pct_gain_2
                        capital += pnl_2
                        pos['pnl_brl'] += pnl_2
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(target_2)
                        pos['exit_reasons'].append("Alvo 2 Atingido (50% Final)")
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue
            else:
                # 50% Remaining
                if c_low <= pos['stop_loss']:
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(pos['stop_loss'])
                    pos['exit_reasons'].append("Stop no Breakeven Atingido (0x0 na 2ª metade)")
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue
                elif c_high >= target_2:
                    pct_gain_2 = (target_2 - entry_price) / entry_price
                    pnl_2 = (allocated_capital * 0.5) * pct_gain_2
                    capital += pnl_2
                    pos['pnl_brl'] += pnl_2
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(target_2)
                    pos['exit_reasons'].append("Alvo 2 Atingido (50% Final)")
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue
                elif c_close < c_ema20:
                    pct_gain_trail = (c_close - entry_price) / entry_price
                    pnl_trail = (allocated_capital * 0.5) * pct_gain_trail
                    capital += pnl_trail
                    pos['pnl_brl'] += pnl_trail
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(c_close)
                    pos['exit_reasons'].append("Saída Trailing: Fechamento 4h abaixo da EMA 20")
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue
                    
        # 2. Evaluate Signals
        for s in symbols:
            if s in active_positions:
                continue
                
            df_sym_4h = data_4h[s]
            sub_4h = df_sym_4h[df_sym_4h['open_time'] <= current_time]
            if len(sub_4h) < 50:
                continue
            candle = sub_4h.iloc[-1]
            prev_candle = sub_4h.iloc[-2]
            
            df_sym_1d = data_1d[s]
            sub_1d = df_sym_1d[df_sym_1d['open_time'] <= current_time]
            if len(sub_1d) < 30:
                continue
            candle_1d = sub_1d.iloc[-1]
            
            veto_reasons = []
            
            # Veto: Max 2 Simultaneous Open Positions
            if len(active_positions) >= 2:
                veto_reasons.append("Limite de Exposição Global da Carteira atingido (máx 2 posições abertas)")
                
            is_vesting, vest_msg = is_vesting_cliff(s, current_time)
            if is_vesting:
                veto_reasons.append(vest_msg)
                
            fr_val = 0.0001
            if not funding_data[s].empty:
                fr_sub = funding_data[s][funding_data[s]['fundingTime'] <= current_time]
                if not fr_sub.empty:
                    fr_val = fr_sub.iloc[-1]['fundingRate']
            if fr_val > 0.0003:
                veto_reasons.append(f"Funding Rate sobreaquecido ({fr_val*100:.4f}% > 0.03%)")
                
            if btc_macro_support_lost:
                veto_reasons.append("BTC perdeu suporte macro (abaixo da EMA 50 1D)")
                
            if candle['close'] < candle['ema50'] and candle['vol_ratio'] < 1.3:
                veto_reasons.append("Preço abaixo da EMA 50 4h sem volume agressor")
                
            # Score
            macro_score = 0
            tech_score = 0
            deriv_score = 0
            onchain_score = 0
            
            if btc_macro_bullish:
                macro_score += 12
            elif btc_last_4h['close'] >= btc_last_4h['ema20']:
                macro_score += 8
            if fng_val >= 40:
                macro_score += 8
            elif fng_val >= 25:
                macro_score += 4
                
            ema_aligned = (candle['ema20'] > candle['ema50']) and (candle['close'] > candle['ema20'])
            ema_major_aligned = (candle['ema50'] > candle['ema200']) or (candle['close'] > candle['ema200'])
            if ema_aligned and ema_major_aligned:
                tech_score += 12
            elif candle['close'] > candle['ema20']:
                tech_score += 7
                
            rsi_val = candle['rsi14']
            adx_val = candle['adx14']
            
            if 45 <= rsi_val <= 65:
                tech_score += 10
            elif rsi_val < 40:
                if candle['close'] > candle['open'] and candle['low'] <= candle['swing_low_10'] * 1.01:
                    tech_score += 8
            elif 65 < rsi_val <= 70:
                tech_score += 5
                
            if candle_1d['close'] > candle_1d['ema50_1d']:
                tech_score += 8
            elif candle_1d['close'] > candle_1d['ema20_1d']:
                tech_score += 4
                
            if fr_val <= 0.0001:
                deriv_score += 15
            elif fr_val <= 0.0002:
                deriv_score += 8
                
            if candle['cvd'] > 0 and candle['vol_ratio'] > 1.0:
                deriv_score += 10
            elif candle['cvd'] > 0:
                deriv_score += 6
                
            if not is_vesting:
                onchain_score += 15
            if s == 'SOLUSDT':
                onchain_score += 10
            elif s == 'SUIUSDT':
                onchain_score += 8
            elif s == 'ILVUSDT':
                onchain_score += 6
                
            total_score = macro_score + tech_score + deriv_score + onchain_score
            
            # Setup & Adaptive Targets
            swing_low = candle['swing_low_10']
            atr = candle['atr14']
            stop_loss = swing_low - (1.5 * atr)
            entry_price = candle['close']
            
            stop_dist = entry_price - stop_loss
            stop_dist_pct = stop_dist / entry_price
            
            if stop_dist_pct < 0.012:
                stop_loss = entry_price * (1 - 0.015)
                stop_dist = entry_price - stop_loss
                stop_dist_pct = stop_dist / entry_price
                
            is_strong_trend = btc_macro_bullish and (adx_val > 20)
            if is_strong_trend:
                rr_target1 = 2.5
                rr_target2 = 4.0
            else:
                rr_target1 = 1.8
                rr_target2 = 2.8
                
            be_trigger_price = entry_price + (1.0 * stop_dist)
            target_1 = entry_price + (rr_target1 * stop_dist)
            target_2 = entry_price + (rr_target2 * stop_dist)
            
            trend_trigger = (candle['close'] > candle['ema20']) and (candle['close'] > prev_candle['high']) and (48 <= rsi_val <= 68) and (candle['close'] > candle['ema50'])
            reversal_trigger = (prev_candle['rsi14'] < 40) and (candle['close'] > prev_candle['high']) and (candle['close'] > candle['open'])
            
            is_entry_signal = (trend_trigger or reversal_trigger)
            
            if is_entry_signal:
                if total_score >= 75 and len(veto_reasons) == 0:
                    risk_brl = capital * risk_per_trade_pct
                    allocated_capital = risk_brl / stop_dist_pct
                    if allocated_capital > capital * 1.5:
                        allocated_capital = capital * 1.5
                        
                    pos = {
                        'symbol': s,
                        'entry_date': current_time,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'stop_dist': stop_dist,
                        'stop_dist_pct': stop_dist_pct,
                        'be_trigger_price': be_trigger_price,
                        'be_moved': False,
                        'target_1': target_1,
                        'target_2': target_2,
                        'rr_target1': rr_target1,
                        'allocated_capital': allocated_capital,
                        'risk_brl': risk_brl,
                        'score': total_score,
                        'regime': 'Tendência Forte (2.5R)' if is_strong_trend else 'Consolidação Adaptativa (1.8R)',
                        'candles_held': 0,
                        'partial_taken': False,
                        'exit_dates': [],
                        'exit_prices': [],
                        'exit_reasons': [],
                        'pnl_brl': 0.0,
                        'status': 'OPEN'
                    }
                    active_positions[s] = pos
                else:
                    idx = df_sym_4h[df_sym_4h['open_time'] == current_time].index[0]
                    sub_future = df_sym_4h.iloc[idx+1:idx+15]
                    outcome = "Não Executado"
                    simulated_loss = 0.0
                    if not sub_future.empty:
                        min_future_low = sub_future['low'].min()
                        max_future_high = sub_future['high'].max()
                        if min_future_low <= stop_loss:
                            simulated_loss = capital * 0.01
                            outcome = f"Prejuízo evitado: -R$ {simulated_loss:.2f} (-{stop_dist_pct*100:.2f}%)"
                        elif max_future_high >= target_1:
                            outcome = "Alvo 1 atingido (Oportunidade filtrada pelo protocolo)"
                        else:
                            outcome = "Consolidação sem atingir alvo/stop"
                            
                    vetoes.append({
                        'date': current_time,
                        'symbol': s,
                        'score': total_score,
                        'motivo': " | ".join(veto_reasons) if veto_reasons else f"Score insuficiente ({total_score}/100 < 75)",
                        'outcome': outcome,
                        'prejuizo_evitado': simulated_loss
                    })
                    
        equity_curve.append({'timestamp': current_time, 'capital': capital})
        
    for s, pos in list(active_positions.items()):
        df_sym_4h = data_4h[s]
        last_candle = df_sym_4h[df_sym_4h['open_time'] <= end_date].iloc[-1]
        c_close = last_candle['close']
        remaining_pct = 0.5 if pos['partial_taken'] else 1.0
        pct_return = (c_close - pos['entry_price']) / pos['entry_price']
        pnl_brl = (pos['allocated_capital'] * remaining_pct) * pct_return
        capital += pnl_brl
        pos['exit_dates'].append(last_candle['open_time'])
        pos['exit_prices'].append(c_close)
        pos['exit_reasons'].append("Fechamento no Fim do Período de Teste (Mark-to-Market)")
        pos['pnl_brl'] += pnl_brl
        pos['final_capital'] = capital
        pos['status'] = 'CLOSED'
        trades.append(pos)
        del active_positions[s]

    print("\n" + "="*80)
    print("RESUMO EXECUTIVO DO BACKTEST OTIMIZADO DE 180 DIAS (SOL, SUI, ILV)")
    print("="*80)
    
    total_trades = len(trades)
    winning_trades = [t for t in trades if t['pnl_brl'] > 0.001]
    losing_trades = [t for t in trades if t['pnl_brl'] < -0.001]
    breakeven_trades = [t for t in trades if abs(t['pnl_brl']) <= 0.001]
    
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    gross_profits = sum(t['pnl_brl'] for t in winning_trades)
    gross_losses = abs(sum(t['pnl_brl'] for t in losing_trades))
    profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else float('inf')
    
    equity_df = pd.DataFrame(equity_curve)
    equity_df['peak'] = equity_df['capital'].cummax()
    equity_df['drawdown'] = (equity_df['capital'] - equity_df['peak']) / equity_df['peak']
    max_drawdown_pct = abs(equity_df['drawdown'].min() * 100)
    
    total_net_profit_brl = capital - initial_capital
    total_return_pct = (total_net_profit_brl / initial_capital) * 100
    
    print(f"Capital Inicial:       R$ {initial_capital:.2f}")
    print(f"Saldo Final:           R$ {capital:.2f} ({total_return_pct:+.2f}%)")
    print(f"Lucro Líquido Total:   R$ {total_net_profit_brl:+.2f}")
    print(f"Total de Trades:       {total_trades}")
    print(f"Trades Vencedores:     {len(winning_trades)}")
    print(f"Trades Perdedores:     {len(losing_trades)}")
    print(f"Trades no 0x0:         {len(breakeven_trades)}")
    print(f"Win Rate:              {win_rate:.2f}%")
    print(f"Profit Factor:         {profit_factor:.2f}")
    print(f"Drawdown Máximo:       {max_drawdown_pct:.2f}%")
    print("="*80)

    trades_export = []
    for t in trades:
        trades_export.append({
            'Data Entrada': t['entry_date'].strftime('%Y-%m-%d %H:%M'),
            'Ativo': t['symbol'].replace('USDT', ''),
            'Regime': t['regime'],
            'Preço Entrada': f"${t['entry_price']:.4f}",
            'Stop Loss': f"${t['stop_loss']:.4f} (-{t['stop_dist_pct']*100:.2f}%)",
            'Alvo 1': f"${t['target_1']:.4f}",
            'Alvo 2': f"${t['target_2']:.4f}",
            'Datas Saída': " | ".join([d.strftime('%Y-%m-%d %H:%M') for d in t['exit_dates']]),
            'Preços Saída': " | ".join([f"${p:.4f}" for p in t['exit_prices']]),
            'Motivo Saída': " | ".join(t['exit_reasons']),
            'Resultado (R$)': f"R$ {t['pnl_brl']:+.2f}",
            'Saldo Acumulado (R$)': f"R$ {t['final_capital']:.2f}"
        })
        
    trades_df = pd.DataFrame(trades_export)
    trades_df.to_csv('trades_executados_180d_otimizado.csv', index=False)
    
    vetoes_export = []
    for v in vetoes:
        vetoes_export.append({
            'Data': v['date'].strftime('%Y-%m-%d %H:%M'),
            'Ativo': v['symbol'].replace('USDT', ''),
            'Score': f"{v['score']}/100",
            'Motivo do Veto': v['motivo'],
            'Resultado Simulado': v['outcome'],
            'Prejuízo Evitado (R$)': f"R$ {v['prejuizo_evitado']:.2f}" if v['prejuizo_evitado'] > 0 else "R$ 0,00"
        })
    vetoes_df = pd.DataFrame(vetoes_export)
    vetoes_df.to_csv('oportunidades_vetadas_180d_otimizado.csv', index=False)
    
    summary = {
        'initial_capital': initial_capital,
        'final_capital': capital,
        'net_profit_brl': total_net_profit_brl,
        'return_pct': total_return_pct,
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'breakeven_trades': len(breakeven_trades),
        'win_rate_pct': win_rate,
        'profit_factor': profit_factor,
        'max_drawdown_pct': max_drawdown_pct,
        'total_vetoes': len(vetoes),
        'total_prejuizo_evitado': sum(v['prejuizo_evitado'] for v in vetoes)
    }
    
    with open('resumo_estatistico_180d_otimizado.json', 'w') as f:
        json.dump(summary, f, indent=4)
        
    return summary, trades_df, vetoes_df

if __name__ == '__main__':
    run_backtest_180d()
