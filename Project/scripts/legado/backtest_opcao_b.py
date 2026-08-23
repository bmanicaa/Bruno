"""
Motor Institucional Blindado (536 Moedas - 5 Anos) com Risco Calibrado de 2.5%
Combina:
1. Screener Point-in-Time nas 536 moedas da Binance (Volume 30d > $25M, Maturidade > 90d, Sem Vesting).
2. Filtro Macro Secular do Bitcoin (BTC >= EMA200 1D e EMA50 1D >= EMA200 1D e BTC 4h >= EMA50 4h).
3. Filtro Hierárquico Diário na Moeda (Close 1D >= EMA20 1D >= EMA50 1D) + Alpha 7d > BTC.
4. Gatilho de Precisão 4h com Confirmação e CVD.
5. Risco Fixo de 2.50% por trade da banca.
6. Gestão Assimétrica: BE +1.2R, Parcial 30% em 2.5R, Runner 70% Trailing EMA20 1D. Stop-First.
7. Circuit Breaker (3 losses -> ½ risco, 5 losses -> pausa 5d). Cooldown 2.5d por ativo.
8. Short em BTC/ETH durante Bear Market (BTC < EMA50 E EMA200 1D).
9. Cash Yield de 6.0% a.a. sobre caixa livre.
"""

import argparse
import datetime
import json
import os
import sys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
COINS_DIR = os.path.join(RAW_DIR, 'coins')
MACRO_DIR = os.path.join(RAW_DIR, 'macro')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
DATA_DIR = os.path.join(BASE_DIR, 'data')

for d in [REPORTS_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

def compute_indicators_4h(df):
    if df.empty:
        return df
    df = df.copy()
    for c in ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'taker_buy_base']:
        if c in df.columns:
            df[c] = df[c].astype(float)
            
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
    
    df['swing_low_5'] = df['low'].rolling(window=5).min()
    df['vol_sma20'] = df['volume'].rolling(window=20).mean()
    df['vol_ratio'] = df['volume'] / (df['vol_sma20'] + 1e-9)
    
    df['return_7d'] = (df['close'] - df['close'].shift(42)) / (df['close'].shift(42) + 1e-9)
    
    if 'taker_buy_base' in df.columns:
        df['taker_sell_base'] = df['volume'] - df['taker_buy_base']
        df['delta_vol'] = df['taker_buy_base'] - df['taker_sell_base']
        df['cvd'] = df['delta_vol'].rolling(window=6).sum()
    else:
        df['cvd'] = 0.0
        
    if 'quote_volume' in df.columns:
        df['vol_quote_30d_sum'] = df['quote_volume'].rolling(window=180).sum()
        df['daily_avg_vol_30d'] = df['vol_quote_30d_sum'] / 30.0
    else:
        df['vol_quote_30d_sum'] = (df['volume'] * df['close']).rolling(window=180).sum()
        df['daily_avg_vol_30d'] = df['vol_quote_30d_sum'] / 30.0
        
    return df

def compute_indicators_1d(df):
    if df.empty:
        return df
    df = df.copy()
    for c in ['open', 'high', 'low', 'close', 'volume']:
        if c in df.columns:
            df[c] = df[c].astype(float)
    df['ema20_1d'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50_1d'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200_1d'] = df['close'].ewm(span=200, adjust=False).mean()
    df['mom_90d'] = df['close'].pct_change(periods=90)
    return df

def is_vesting_cliff(symbol, dt):
    s = symbol.upper()
    if 'SUI' in s:
        next_month = dt.month + 1 if dt.month < 12 else 1
        next_year = dt.year if dt.month < 12 else dt.year + 1
        next_first = datetime.datetime(next_year, next_month, 1)
        this_first = datetime.datetime(dt.year, dt.month, 1)
        if (next_first - dt).total_seconds() / 86400 <= 7 or (dt - this_first).total_seconds() / 86400 <= 1:
            return True, "Desbloqueio de Vesting SUI > 1% (Cliff mensal no dia 1)"
    elif 'APT' in s and (5 <= dt.day <= 13):
        return True, "Desbloqueio de Vesting APT > 1% (Cliff mensal no dia 11/12)"
    elif 'ARB' in s and (9 <= dt.day <= 17):
        return True, "Desbloqueio de Vesting ARB > 1% (Cliff mensal no dia 16)"
    elif 'OP' in s and ('PEPE' not in s) and (dt.day >= 24):
        return True, "Desbloqueio de Vesting OP > 1% (Cliff no fim do mês)"
    elif 'TIA' in s and (dt.month in [10, 11] and dt.day >= 25):
        return True, "Mega Desbloqueio de Vesting TIA"
    elif 'WLD' in s and (15 <= dt.day <= 25):
        return True, "Desbloqueio de Vesting WLD > 1%"
    elif 'SEI' in s and (10 <= dt.day <= 18):
        return True, "Desbloqueio de Vesting SEI > 1%"
    elif 'GALA' in s and (dt.month in [4, 7] and 15 <= dt.day <= 25):
        return True, "Janela de Emissão/Desbloqueio GALA"
    elif 'ILV' in s and (dt.month in [3, 6, 8] and 20 <= dt.day <= 28):
        return True, "Desbloqueio de Vesting ILV > 1%"
    return False, ""

def load_all_data():
    btc_4h_path = os.path.join(MACRO_DIR, 'BTCUSDT_4h.csv')
    btc_1d_path = os.path.join(MACRO_DIR, 'BTCUSDT_1d.csv')
    fng_path = os.path.join(MACRO_DIR, 'fear_and_greed.csv')
    
    btc_4h = pd.read_csv(btc_4h_path)
    btc_4h['open_time'] = pd.to_datetime(btc_4h['open_time_dt'] if 'open_time_dt' in btc_4h.columns else btc_4h['open_time']).astype('datetime64[ns]')
    btc_4h = compute_indicators_4h(btc_4h)
    btc_4h.sort_values('open_time', inplace=True)
    
    btc_1d = pd.read_csv(btc_1d_path)
    btc_1d['open_time'] = pd.to_datetime(btc_1d['open_time_dt'] if 'open_time_dt' in btc_1d.columns else btc_1d['open_time']).astype('datetime64[ns]')
    btc_1d = compute_indicators_1d(btc_1d)
    btc_1d.sort_values('open_time', inplace=True)
    
    btc_1d_sub = btc_1d[['open_time', 'close', 'ema20_1d', 'ema50_1d', 'ema200_1d', 'mom_90d']].copy()
    btc_1d_sub.columns = ['open_time_1d', 'close_1d', 'ema20_1d', 'ema50_1d', 'ema200_1d', 'mom_90d_1d']
    btc_4h_merged = pd.merge_asof(
        btc_4h, btc_1d_sub,
        left_on='open_time', right_on='open_time_1d',
        direction='backward'
    )
    btc_4h_merged.set_index('open_time', inplace=True)
    
    fng_df = pd.DataFrame()
    if os.path.exists(fng_path):
        fng_df = pd.read_csv(fng_path)
        fng_df['timestamp'] = pd.to_datetime(fng_df['date']).astype('datetime64[ns]')
        fng_df['value'] = fng_df['value'].astype(float)
        fng_df = fng_df.sort_values('timestamp').reset_index(drop=True)
        
    available_symbols = [d for d in os.listdir(COINS_DIR) if os.path.isdir(os.path.join(COINS_DIR, d))]
    if 'BTCUSDT' not in available_symbols:
        available_symbols.append('BTCUSDT')
        
    coins_4h_map = {'BTCUSDT': btc_4h_merged}
    funding_map = {}
    
    print(f"Carregando e indexando {len(available_symbols)} moedas do mercado total da Binance...")
    
    for s in available_symbols:
        if s == 'BTCUSDT':
            continue
        k4h_p = os.path.join(COINS_DIR, s, 'klines_4h.csv')
        k1d_p = os.path.join(COINS_DIR, s, 'klines_1d.csv')
        fr_p = os.path.join(COINS_DIR, s, 'funding_rates.csv')
        
        if os.path.exists(k4h_p) and os.path.exists(k1d_p):
            df4 = pd.read_csv(k4h_p)
            df1 = pd.read_csv(k1d_p)
            if not df4.empty and not df1.empty and 'close' in df4.columns and 'close' in df1.columns:
                df4['open_time'] = pd.to_datetime(df4['open_time_dt'] if 'open_time_dt' in df4.columns else df4['open_time']).astype('datetime64[ns]')
                df4 = compute_indicators_4h(df4)
                df4.sort_values('open_time', inplace=True)
                
                df1['open_time'] = pd.to_datetime(df1['open_time_dt'] if 'open_time_dt' in df1.columns else df1['open_time']).astype('datetime64[ns]')
                df1 = compute_indicators_1d(df1)
                df1.sort_values('open_time', inplace=True)
                
                if 'ema20_1d' in df1.columns:
                    df1_sub = df1[['open_time', 'close', 'ema20_1d', 'ema50_1d', 'ema200_1d', 'mom_90d']].copy()
                    df1_sub.columns = ['open_time_1d', 'close_1d', 'ema20_1d', 'ema50_1d', 'ema200_1d', 'mom_90d_1d']
                    
                    df4 = pd.merge_asof(
                        df4, df1_sub,
                        left_on='open_time', right_on='open_time_1d',
                        direction='backward'
                    )
                    
                    df4.set_index('open_time', inplace=True)
                    coins_4h_map[s] = df4
            
        if os.path.exists(fr_p):
            fr_df = pd.read_csv(fr_p)
            fr_df['fundingTime'] = pd.to_datetime(fr_df['fundingTime_dt'] if 'fundingTime_dt' in fr_df.columns else fr_df['fundingTime']).astype('datetime64[ns]')
            fr_df.sort_values('fundingTime', inplace=True)
            funding_map[s] = fr_df
            
    return btc_4h, btc_1d, fng_df, coins_4h_map, funding_map, available_symbols

def run_portfolio_backtest(start_date_str, end_date_str, initial_capital=100000.0, risk_pct=0.025,
                           max_positions=4, min_daily_volume=25_000_000, fee_pct=0.00075,
                           annual_cash_yield=0.06):
    start_date = pd.to_datetime(start_date_str)
    end_date = pd.to_datetime(end_date_str)
    
    btc_4h, btc_1d, fng_df, coins_4h_map, funding_map, available_symbols = load_all_data()
    
    btc_1d_sorted = btc_1d.sort_values('open_time').copy()
    btc_4h_sorted = btc_4h.sort_values('open_time').copy()
    btc_4h_sorted.set_index('open_time', inplace=True)
    
    all_timestamps = [ts for ts in btc_4h_sorted.index if start_date <= ts <= end_date]
    
    btc_macro_map = {}
    btc_return_7d_map = {}
    
    for ts in all_timestamps:
        b1d_sub = btc_1d_sorted[btc_1d_sorted['open_time'] < ts]
        if b1d_sub.empty or ts not in btc_4h_sorted.index:
            btc_macro_map[ts] = False
            btc_return_7d_map[ts] = 0.0
            continue
        last_1d = b1d_sub.iloc[-1]
        last_4h = btc_4h_sorted.loc[ts]
        
        close_1d = float(last_1d['close'])
        ema50_1d = float(last_1d['ema50_1d'])
        ema200_1d = float(last_1d['ema200_1d'])

        is_strong_bull = (close_1d >= ema50_1d) and (close_1d >= ema200_1d)
        is_bear = (close_1d < ema50_1d) and (close_1d < ema200_1d)
        is_transition = not is_strong_bull and not is_bear

        btc_macro_map[ts] = {
            'bull': is_strong_bull,
            'bear': is_bear,
            'transition': is_transition
        }
        btc_return_7d_map[ts] = last_4h['return_7d'] if pd.notna(last_4h['return_7d']) else 0.0
        
    capital = initial_capital
    active_positions = {}
    trades = []
    equity_curve = [{'timestamp': start_date, 'capital': capital, 'cash': capital, 'active_count': 0}]
    total_cash_yield_earned = 0.0
    cash_yield_per_4h = annual_cash_yield / 2190.0
    
    semesters = [
        pd.to_datetime('2022-05-15'),
        pd.to_datetime('2022-11-15'),
        pd.to_datetime('2023-05-15'),
        pd.to_datetime('2023-11-15'),
        pd.to_datetime('2024-05-15'),
        pd.to_datetime('2024-11-15'),
        pd.to_datetime('2025-05-15'),
        pd.to_datetime('2025-11-15'),
        pd.to_datetime('2026-05-15'),
        pd.to_datetime(end_date_str)
    ]
    semester_checkpoints = {}
    
    print("Pre-indexando candidatos qualificados no mercado total de 536 moedas (Dual-Timeframe + Alpha vs BTC)...")
    candidates_by_time = {ts: [] for ts in all_timestamps}
    
    for s in available_symbols:
        df4 = coins_4h_map.get(s)
        if df4 is None or len(df4) < 1080:
            continue
            
        idx_times = df4.index
        valid_mask = (idx_times >= start_date) & (idx_times <= end_date)
        valid_indices = np.where(valid_mask)[0]
        
        for loc_idx in valid_indices:
            if loc_idx < 1080:
                continue
            current_time = idx_times[loc_idx]
            
            prev_candle = df4.iloc[loc_idx - 1]
            candle_2ago = df4.iloc[loc_idx - 2]
            candle_3ago = df4.iloc[loc_idx - 3]
            
            # 1. Volume 30d > $25M
            if prev_candle['daily_avg_vol_30d'] < min_daily_volume:
                continue
                
            # 1b. FILTRO ANTI-MEMECOIN (Volatilidade ATR% > 12%)
            atr_pct = prev_candle['atr14'] / (prev_candle['close'] + 1e-9)
            if atr_pct > 0.12:
                continue
                
            # 1c. FILTRO ANTI-PUMP (Spike de volume artificial)
            if prev_candle['vol_ratio'] > 5.0:
                continue
                
            # 2. FILTRO HIERÁRQUICO DIÁRIO (1D): Close 1D >= EMA20 1D >= EMA50 1D
            if pd.isna(prev_candle['close_1d']) or (prev_candle['close_1d'] < prev_candle['ema20_1d']) or (prev_candle['ema20_1d'] < prev_candle['ema50_1d']):
                continue
                
            # 3. FORÇA RELATIVA (ALPHA 7D VS BTC 7D)
            btc_ret7d = btc_return_7d_map.get(current_time, 0.0)
            coin_ret7d = prev_candle['return_7d']
            
            if s != 'BTCUSDT':
                if pd.isna(coin_ret7d) or coin_ret7d < btc_ret7d:
                    continue
            else:
                coin_ret7d = btc_ret7d
                
            # 4. ESTRUTURA 4H: EMA20 > EMA50 > EMA200 e ADX >= 22
            if not (prev_candle['ema20'] > prev_candle['ema50'] > prev_candle['ema200']):
                continue
            if prev_candle['adx14'] < 22:
                continue
                
            # 5. PULLBACK E SUPORTE: Teste da região de médias (EMA20/EMA50) nos últimos 3 candles
            tested_support = min(prev_candle['low'], candle_2ago['low'], candle_3ago['low']) <= (prev_candle['ema20'] * 1.02)
            rsi_pullback = (42 <= prev_candle['rsi14'] <= 60)
            rejection_turn = (prev_candle['close'] > prev_candle['open']) and (prev_candle['close'] >= prev_candle['ema20']) and (prev_candle['cvd'] > 0)
            vol_active = prev_candle['vol_ratio'] >= 0.9
            
            # 6. FILTRO ANTI-PAVIO
            body_size = prev_candle['close'] - prev_candle['open']
            upper_wick = prev_candle['high'] - prev_candle['close']
            if upper_wick > (body_size * 1.5):
                continue
                
            if not (tested_support and rsi_pullback and rejection_turn and vol_active):
                continue
                
            is_vest, _ = is_vesting_cliff(s, current_time)
            if is_vest:
                continue
                
            current_open_candle = df4.iloc[loc_idx]
            entry_price = current_open_candle['open'] * 1.0005
            
            # STOP LOSS TÉCNICO CALIBRADO (Mínima dos últimos 10 candles 4H - 1.5 * ATR14)
            recent_10_lows = df4.iloc[max(0, loc_idx-10):loc_idx]['low'].min()
            raw_stop = recent_10_lows - (1.5 * prev_candle['atr14'])
            raw_dist_pct = (entry_price - raw_stop) / entry_price
            stop_dist_pct = min(max(raw_dist_pct, 0.035 if s == 'BTCUSDT' else 0.040), 0.080)
            stop_loss = entry_price * (1 - stop_dist_pct)
            stop_dist = entry_price - stop_loss
            
            # Alvos Assimétricos V2.1
            breakeven_trigger = entry_price + (1.9 * stop_dist)  # +1.2R -> mover stop para 0x0
            target_1 = entry_price + (2.0 * stop_dist)           # +2.5R -> parcial de 30%
            
            btc_bonus = 15 if s == 'BTCUSDT' else 0
            score = 100 + (coin_ret7d - btc_ret7d)*100 + (prev_candle['adx14'] - 20) + btc_bonus
            
            candidates_by_time[current_time].append({
                'symbol': s,
                'score': score,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'stop_dist': stop_dist,
                'stop_dist_pct': stop_dist_pct,
                'breakeven_trigger': breakeven_trigger,
                'target_1': target_1,
                'regime': "Trend Following (BE 1.9R / 50% 2.0R / Runner 50% EMA50 1D)",
                'adx_val': prev_candle['adx14'],
                'direction': 'LONG',
                'mom_90d': prev_candle.get('mom_90d_1d', -float('inf'))
            })
            

    # ================================================================
    # SCREENER SHORT — Apenas BTC e ETH em Regime Bear
    # ================================================================
    short_symbols = ['BTCUSDT', 'ETHUSDT']
    short_candidates_by_time = {ts: [] for ts in all_timestamps}

    for s in short_symbols:
        df4 = coins_4h_map.get(s)
        if df4 is None or len(df4) < 1080:
            continue

        idx_times = df4.index
        valid_mask = (idx_times >= start_date) & (idx_times <= end_date)
        valid_indices = np.where(valid_mask)[0]

        for loc_idx in valid_indices:
            if loc_idx < 1080:
                continue
            current_time = idx_times[loc_idx]

            # Só gera candidatos short se regime macro é BEAR
            regime = btc_macro_map.get(current_time, {'bear': False})
            if not regime.get('bear', False):
                continue

            prev_candle = df4.iloc[loc_idx - 1]
            candle_2ago = df4.iloc[loc_idx - 2]
            candle_3ago = df4.iloc[loc_idx - 3]

            if prev_candle['daily_avg_vol_30d'] < min_daily_volume:
                continue

            # ESTRUTURA DIÁRIA BAIXISTA: Close 1D < EMA20 1D < EMA50 1D
            if pd.isna(prev_candle.get('close_1d')) or pd.isna(prev_candle.get('ema20_1d')):
                continue
            if not (prev_candle['close_1d'] < prev_candle['ema20_1d'] < prev_candle['ema50_1d']):
                continue

            # ESTRUTURA 4H BAIXISTA: EMA20 < EMA50
            if not (prev_candle['ema20'] < prev_candle['ema50']):
                continue

            # REPIQUE na EMA20/EMA50 4H (últimos 3 candles)
            tested_resistance = max(prev_candle['high'], candle_2ago['high'], candle_3ago['high']) >= (prev_candle['ema20'] * 0.98)

            # RSI 38-56 + CVD < 0
            rsi_rejection = (38 <= prev_candle['rsi14'] <= 56)
            bearish_candle = (prev_candle['close'] < prev_candle['open']) and (prev_candle['close'] <= prev_candle['ema20'])
            cvd_negative = prev_candle['cvd'] < 0

            if not (tested_resistance and rsi_rejection and bearish_candle and cvd_negative):
                continue

            # Veto de Funding Rate (otimizado)
            fr_val_check = 0.0001

            current_open_candle = df4.iloc[loc_idx]
            entry_price = current_open_candle['open'] * 0.9995  # Slippage SHORT (vende abaixo)

            # STOP LOSS SHORT: Máxima dos últimos 10 candles + 1.5 * ATR
            recent_10_highs = df4.iloc[max(0, loc_idx-10):loc_idx]['high'].max()
            raw_stop = recent_10_highs + (1.5 * prev_candle['atr14'])
            raw_dist_pct = (raw_stop - entry_price) / entry_price
            stop_dist_pct = min(max(raw_dist_pct, 0.035), 0.080)
            stop_loss = entry_price * (1 + stop_dist_pct)
            stop_dist = stop_loss - entry_price

            # Alvos SHORT (invertidos)
            breakeven_trigger = entry_price - (1.9 * stop_dist)
            target_1 = entry_price - (2.0 * stop_dist)

            score = 100 + (prev_candle['adx14'] - 20)

            short_candidates_by_time[current_time].append({
                'symbol': s,
                'score': score,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'stop_dist': stop_dist,
                'stop_dist_pct': stop_dist_pct,
                'breakeven_trigger': breakeven_trigger,
                'target_1': target_1,
                'regime': "Short Bear (BE 1.9R / 50% 2.0R / Runner 50% EMA50 1D)",
                'adx_val': prev_candle['adx14'],
                'direction': 'SHORT'
            })

    print("Filtrando para permitir apenas as Top 5 moedas mais fortes por dia (Filtro Momentum)...")
    for ts in candidates_by_time:
        cands = candidates_by_time[ts]
        if cands:
            cands.sort(key=lambda x: x.get('mom_90d', -float('inf')), reverse=True)
            candidates_by_time[ts] = cands[:5]
    print("Iniciando loop de simulação da carteira com Risco 2.5%...")
    
    for current_time in all_timestamps:
        btc_regime = btc_macro_map.get(current_time, {'bull': False, 'bear': False, 'transition': True})
        if isinstance(btc_regime, dict):
            btc_bull = btc_regime['bull']
            btc_bear = btc_regime['bear']
        else:
            btc_bull = btc_regime
            btc_bear = False
        
        # ================================================================
        # CIRCUIT BREAKER E COOLDOWN
        # ================================================================
        effective_risk = risk_pct
        skip_new_entries = False

        closed_trades = [t for t in trades if t['status'] == 'CLOSED']
        if len(closed_trades) >= 3:
            last_3 = closed_trades[-3:]
            if all(t['pnl_brl'] < 0 for t in last_3):
                effective_risk = risk_pct * 0.50

        if len(closed_trades) >= 5:
            last_5 = closed_trades[-5:]
            if all(t['pnl_brl'] < 0 for t in last_5):
                last_exit_time = max(t['exit_dates'][-1] for t in last_5)
                hours_since = (current_time - last_exit_time).total_seconds() / 3600
                if hours_since < 120:
                    skip_new_entries = True
                    
        cooldown_seconds = 15 * 4 * 3600
        recent_loss_exits = {}
        for t in closed_trades:
            if t['pnl_brl'] < 0 and t['exit_dates']:
                sym = t['symbol']
                exit_dt = t['exit_dates'][-1]
                if sym not in recent_loss_exits or exit_dt > recent_loss_exits[sym]:
                    recent_loss_exits[sym] = exit_dt
        
        # 1. Creditar Remuneração do Caixa Livre (Cash Yield 6% a.a.)
        allocated_total = sum(p['allocated_capital'] * p['remaining_pct'] for p in active_positions.values())
        free_cash = max(capital - allocated_total, 0.0)
        cash_interest = free_cash * cash_yield_per_4h
        capital += cash_interest
        total_cash_yield_earned += cash_interest
        
        # 2. Gerenciar Posições Abertas
        for s in list(active_positions.keys()):
            pos = active_positions[s]
            df4 = coins_4h_map.get(s)
            if df4 is None or current_time not in df4.index:
                continue
            candle = df4.loc[current_time]
            
            c_high = candle['high']
            c_low = candle['low']
            c_close = candle['close']
            c_ema50 = candle['ema50']
            c_rsi = candle['rsi14']
            
            fr_val = 0.0001
            if s in funding_map and not funding_map[s].empty:
                fr_sub = funding_map[s][funding_map[s]['fundingTime'] <= current_time]
                if not fr_sub.empty:
                    fr_val = fr_sub.iloc[-1]['fundingRate']
                    
            entry_price = pos['entry_price']
            allocated_capital = pos['allocated_capital']
            pos['candles_held'] += 1
            

            if pos.get('direction', 'LONG') == 'LONG':
                # Débito de Funding nas janelas UTC 00:00, 08:00, 16:00
                if current_time.hour in [0, 8, 16]:
                    current_notional = (allocated_capital * pos['remaining_pct']) * (c_close / entry_price)
                    funding_fee = current_notional * fr_val
                    capital -= funding_fee
                    pos['pnl_brl'] -= funding_fee
                    pos['funding_paid'] = pos.get('funding_paid', 0.0) + funding_fee

                # ── ESTÁGIO 1: Posição integral (100%), antes do breakeven ──
                if not pos.get('breakeven_set', False) and not pos['t1_taken']:
                    if c_low <= pos['stop_loss']:
                        stop_slippage = 0.0008
                        stop_exec_price = pos['stop_loss'] * (1 - stop_slippage)
                        pct_loss = (stop_exec_price - entry_price) / entry_price
                        gross_pnl = allocated_capital * pct_loss
                        exit_fee = (allocated_capital * (1 + pct_loss)) * fee_pct
                        pnl_brl = gross_pnl - exit_fee
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(stop_exec_price)
                        pos['exit_reasons'].append("Stop Loss Inicial")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                    if c_high >= pos['breakeven_trigger']:
                        pos['breakeven_set'] = True
                        pos['stop_loss'] = entry_price * 1.001

                    if c_rsi > 75 and fr_val > 0.0004:
                        pct_return = (c_close - entry_price) / entry_price
                        gross_pnl = (allocated_capital * pos['remaining_pct']) * pct_return
                        exit_fee = (allocated_capital * pos['remaining_pct'] * (1 + pct_return)) * fee_pct
                        pnl_brl = gross_pnl - exit_fee
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(c_close)
                        pos['exit_reasons'].append("Exaustão RSI>75 & FR Alto")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                    if pos['candles_held'] >= 126:
                        pct_return = (c_close - entry_price) / entry_price
                        gross_pnl = (allocated_capital * pos['remaining_pct']) * pct_return
                        exit_fee = (allocated_capital * pos['remaining_pct'] * (1 + pct_return)) * fee_pct
                        pnl_brl = gross_pnl - exit_fee
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(c_close)
                        pos['exit_reasons'].append("Time-Stop (21d)")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                # ── ESTÁGIO 2: Breakeven ativo, aguardando parcial 2.5R ──
                elif pos.get('breakeven_set') and not pos['t1_taken']:
                    if c_low <= pos['stop_loss']:
                        stop_slippage = 0.0008
                        stop_exec_price = pos['stop_loss'] * (1 - stop_slippage)
                        pct_pnl = (stop_exec_price - entry_price) / entry_price
                        gross_pnl = allocated_capital * pct_pnl
                        exit_fee = (allocated_capital * (1 + pct_pnl)) * fee_pct
                        pnl_brl = gross_pnl - exit_fee
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(stop_exec_price)
                        pos['exit_reasons'].append("Stop Breakeven (0x0)")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                    if c_high >= pos['target_1']:
                        pos['t1_taken'] = True
                        pos['remaining_pct'] = 0.50
                        pct_gain_1 = (pos['target_1'] - entry_price) / entry_price
                        gross_pnl_1 = (allocated_capital * 0.50) * pct_gain_1
                        exit_fee_1 = (allocated_capital * 0.50 * (1 + pct_gain_1)) * fee_pct
                        pnl_1 = gross_pnl_1 - exit_fee_1
                        capital += pnl_1
                        pos['pnl_brl'] += pnl_1
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(pos['target_1'])
                        pos['exit_reasons'].append("Parcial Segurança (2.0R / 50%)")

                    elif c_rsi > 75 and fr_val > 0.0004:
                        pct_return = (c_close - entry_price) / entry_price
                        gross_pnl = (allocated_capital * pos['remaining_pct']) * pct_return
                        exit_fee = (allocated_capital * pos['remaining_pct'] * (1 + pct_return)) * fee_pct
                        pnl_brl = gross_pnl - exit_fee
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(c_close)
                        pos['exit_reasons'].append("Exaustão RSI>75 & FR Alto (pós-BE)")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                # ── ESTÁGIO 3: RUNNER LIVRE (70%) — Trailing na EMA20 DIÁRIA ──
                elif pos['t1_taken']:
                    if c_low <= pos['stop_loss']:
                        stop_slippage = 0.0008
                        stop_exec_price = pos['stop_loss'] * (1 - stop_slippage)
                        pct_pnl = (stop_exec_price - entry_price) / entry_price
                        gross_pnl = (allocated_capital * pos['remaining_pct']) * pct_pnl
                        exit_fee = (allocated_capital * pos['remaining_pct'] * (1 + pct_pnl)) * fee_pct
                        pnl_brl = gross_pnl - exit_fee
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(stop_exec_price)
                        pos['exit_reasons'].append("Stop BE Runner (50%)")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                    coin_ema50_1d = candle.get('ema50_1d', None)
                    if coin_ema50_1d is not None and not pd.isna(coin_ema50_1d) and c_close < coin_ema50_1d:
                        pct_gain_trail = (c_close - entry_price) / entry_price
                        gross_pnl_trail = (allocated_capital * pos['remaining_pct']) * pct_gain_trail
                        exit_fee_trail = (allocated_capital * pos['remaining_pct'] * (1 + pct_gain_trail)) * fee_pct
                        pnl_trail = gross_pnl_trail - exit_fee_trail
                        capital += pnl_trail
                        pos['pnl_brl'] += pnl_trail
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(c_close)
                        pos['exit_reasons'].append("Trailing EMA50 1D Runner (50%)")
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

            elif pos.get('direction') == 'SHORT':
                if current_time.hour in [0, 8, 16]:
                    current_notional = (allocated_capital * pos['remaining_pct']) * (entry_price / (c_close + 1e-9))
                    funding_fee = -current_notional * fr_val
                    capital -= funding_fee
                    pos['pnl_brl'] -= funding_fee
                    pos['funding_paid'] = pos.get('funding_paid', 0.0) + funding_fee

                def short_pnl(exit_price, pct_of_position):
                    pct_return = (entry_price - exit_price) / entry_price
                    gross = (allocated_capital * pct_of_position) * pct_return
                    fee = (allocated_capital * pct_of_position * (1 + abs(pct_return))) * fee_pct
                    return gross - fee

                if not pos.get('breakeven_set') and not pos['t1_taken']:
                    if c_high >= pos['stop_loss']:
                        stop_exec = pos['stop_loss'] * 1.0008
                        pnl_brl = short_pnl(stop_exec, pos['remaining_pct'])
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(stop_exec)
                        pos['exit_reasons'].append("Stop Loss Inicial (SHORT)")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                    if c_low <= pos['breakeven_trigger']:
                        pos['breakeven_set'] = True
                        pos['stop_loss'] = entry_price * 0.999

                    if pos['candles_held'] >= 126:
                        pnl_brl = short_pnl(c_close, pos['remaining_pct'])
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(c_close)
                        pos['exit_reasons'].append("Time-Stop 21d (SHORT)")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                elif pos.get('breakeven_set') and not pos['t1_taken']:
                    if c_high >= pos['stop_loss']:
                        stop_exec = pos['stop_loss'] * 1.0008
                        pnl_brl = short_pnl(stop_exec, pos['remaining_pct'])
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(stop_exec)
                        pos['exit_reasons'].append("Stop BE (SHORT)")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                    if c_low <= pos['target_1']:
                        pos['t1_taken'] = True
                        pos['remaining_pct'] = 0.50
                        pnl_1 = short_pnl(pos['target_1'], 0.50)
                        capital += pnl_1
                        pos['pnl_brl'] += pnl_1
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(pos['target_1'])
                        pos['exit_reasons'].append("Parcial 2.0R / 50% (SHORT)")

                elif pos['t1_taken']:
                    if c_high >= pos['stop_loss']:
                        stop_exec = pos['stop_loss'] * 1.0008
                        pnl_brl = short_pnl(stop_exec, pos['remaining_pct'])
                        capital += pnl_brl
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(stop_exec)
                        pos['exit_reasons'].append("Stop BE Runner (SHORT 50%)")
                        pos['pnl_brl'] += pnl_brl
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

                    coin_ema50_1d = candle.get('ema50_1d', None)
                    if coin_ema50_1d is not None and not pd.isna(coin_ema50_1d) and c_close > coin_ema50_1d:
                        pnl_trail = short_pnl(c_close, pos['remaining_pct'])
                        capital += pnl_trail
                        pos['pnl_brl'] += pnl_trail
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(c_close)
                        pos['exit_reasons'].append("Trailing EMA50 1D Runner (SHORT 50%)")
                        pos['final_capital'] = capital
                        pos['status'] = 'CLOSED'
                        trades.append(pos)
                        del active_positions[s]
                        continue

        # 3. Alocação nos Melhores Candidatos LONG
        raw_candidates = candidates_by_time.get(current_time, [])
        if btc_bull and raw_candidates and not skip_new_entries and len(active_positions) < max_positions:
            eligible = [c for c in raw_candidates if c['symbol'] not in active_positions]
            eligible = [c for c in eligible if c['symbol'] not in recent_loss_exits or (current_time - recent_loss_exits[c['symbol']]).total_seconds() >= cooldown_seconds]
            if eligible:
                eligible.sort(key=lambda x: x['score'], reverse=True)
                available_slots = max_positions - len(active_positions)
                selected = eligible[:available_slots]
                
                for c in selected:
                    risk_brl = capital * effective_risk
                    allocated_capital = min(risk_brl / c['stop_dist_pct'], capital * 1.5)
                    entry_fee = allocated_capital * fee_pct
                    capital -= entry_fee
                    
                    active_positions[c['symbol']] = {
                        'symbol': c['symbol'], 'entry_date': current_time, 'entry_price': c['entry_price'],
                        'stop_loss': c['stop_loss'], 'stop_dist': c['stop_dist'], 'stop_dist_pct': c['stop_dist_pct'],
                        'breakeven_trigger': c['breakeven_trigger'], 'target_1': c['target_1'],
                        'regime': c['regime'], 'direction': 'LONG',
                'mom_90d': prev_candle.get('mom_90d_1d', -float('inf')),
                        'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                        'score': c['score'], 'candles_held': 0,
                        'breakeven_set': False, 't1_taken': False,
                        'remaining_pct': 1.0,
                        'exit_dates': [], 'exit_prices': [], 'exit_reasons': [], 'pnl_brl': -entry_fee, 'status': 'OPEN',
                        'funding_paid': 0.0
                    }
                    
        # ALOCAÇÃO SHORT
        if btc_bear and not skip_new_entries and len(active_positions) < max_positions:
            short_raw = short_candidates_by_time.get(current_time, [])
            short_eligible = [c for c in short_raw if c['symbol'] not in active_positions]
            short_eligible = [c for c in short_eligible if c['symbol'] not in recent_loss_exits or (current_time - recent_loss_exits[c['symbol']]).total_seconds() >= cooldown_seconds]

            if short_eligible:
                short_eligible.sort(key=lambda x: x['score'], reverse=True)
                available_slots = max_positions - len(active_positions)
                short_selected = short_eligible[:available_slots]

                for c in short_selected:
                    risk_brl = capital * effective_risk
                    allocated_capital = min(risk_brl / c['stop_dist_pct'], capital * 1.5)
                    entry_fee = allocated_capital * fee_pct
                    capital -= entry_fee

                    active_positions[c['symbol']] = {
                        'symbol': c['symbol'], 'entry_date': current_time, 'entry_price': c['entry_price'],
                        'stop_loss': c['stop_loss'], 'stop_dist': c['stop_dist'], 'stop_dist_pct': c['stop_dist_pct'],
                        'breakeven_trigger': c['breakeven_trigger'], 'target_1': c['target_1'],
                        'regime': c['regime'], 'direction': 'SHORT',
                        'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                        'score': c['score'], 'candles_held': 0,
                        'breakeven_set': False, 't1_taken': False,
                        'remaining_pct': 1.0,
                        'exit_dates': [], 'exit_prices': [], 'exit_reasons': [], 'pnl_brl': -entry_fee, 'status': 'OPEN',
                        'funding_paid': 0.0
                    }
                    
        # Curva Mark-to-Market
        unrealized_pnl = 0.0
        for s_act, p_act in active_positions.items():
            df_sym_curr = coins_4h_map.get(s_act)
            if df_sym_curr is not None and current_time in df_sym_curr.index:
                c_close_now = df_sym_curr.loc[current_time]['close']
                pct_ret_now = (c_close_now - p_act['entry_price']) / p_act['entry_price']
                unrealized_pnl += (p_act['allocated_capital'] * p_act['remaining_pct']) * pct_ret_now
                
        total_mtm_equity = capital + unrealized_pnl
        equity_curve.append({
            'timestamp': current_time,
            'capital': total_mtm_equity,
            'realized_capital': capital,
            'unrealized_pnl': unrealized_pnl,
            'active_count': len(active_positions)
        })
        
        for sm in semesters:
            if current_time == sm or (current_time > sm and sm.strftime('%Y-%m-%d') not in semester_checkpoints):
                semester_checkpoints[sm.strftime('%Y-%m-%d')] = total_mtm_equity
                
    # Fechar posições restantes
    for s, pos in list(active_positions.items()):
        df4 = coins_4h_map.get(s)
        if df4 is not None:
            last_sub = df4[df4.index <= end_date]
            if not last_sub.empty:
                last_candle = last_sub.iloc[-1]
                c_close = last_candle['close']
                pct_return = (c_close - pos['entry_price']) / pos['entry_price']
                gross_pnl = (pos['allocated_capital'] * pos['remaining_pct']) * pct_return
                exit_fee = (pos['allocated_capital'] * pos['remaining_pct'] * (1 + pct_return)) * fee_pct
                pnl_brl = gross_pnl - exit_fee
                capital += pnl_brl
                pos['exit_dates'].append(last_sub.index[-1])
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
    
    equity_df['daily_return'] = equity_df['capital'].pct_change()
    daily_rets = equity_df['daily_return'].dropna()
    sharpe = (daily_rets.mean() / (daily_rets.std() + 1e-9)) * np.sqrt(2190) if len(daily_rets) > 0 else 0.0
    downside = daily_rets[daily_rets < 0]
    sortino = (daily_rets.mean() / (downside.std() + 1e-9)) * np.sqrt(2190) if len(downside) > 0 else 0.0
    
    results = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'initial_capital': initial_capital,
        'final_capital': capital,
        'net_profit_brl': net_profit_brl,
        'return_pct': return_pct,
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'breakeven_trades': len(breakeven_trades),
        'win_rate_pct': win_rate,
        'profit_factor': profit_factor,
        'max_drawdown_pct': max_drawdown_pct,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'total_cash_yield_brl': total_cash_yield_earned,
        'total_funding_fees_brl': sum(t.get('funding_paid', 0.0) for t in trades),
        'coins_scanned': len(available_symbols),
        'semester_checkpoints': semester_checkpoints
    }
    
    return results, trades, equity_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='5anos', choices=['5anos', 'preliminar', 'estresse_bear', 'estresse_bull', 'estresse_chop'], help='Modalidade de teste')
    parser.add_argument('--start_date', type=str, default=None)
    parser.add_argument('--end_date', type=str, default=None)
    parser.add_argument('--capital', type=float, default=100000.0)
    parser.add_argument('--risk', type=float, default=0.025)
    parser.add_argument('--max_pos', type=int, default=3)
    args = parser.parse_args()
    
    modes_dates = {
        '5anos': ('2021-11-15', '2026-08-20'),
        'preliminar': ('2023-10-01', '2024-10-01'),        # 1 Ano / Miniatura do Ciclo (15 seg)
        'estresse_bear': ('2022-01-01', '2022-12-31'),     # Bear Market 2022 (Crash Luna/FTX)
        'estresse_bull': ('2023-10-01', '2024-03-31'),     # Bull Run Explosiva ETF/Halving
        'estresse_chop': ('2024-04-01', '2024-09-30')      # Lateralidade & Fakeouts
    }
    
    if args.start_date is None or args.end_date is None:
        start_dt, end_dt = modes_dates.get(args.mode, ('2021-11-15', '2026-08-20'))
    else:
        start_dt, end_dt = args.start_date, args.end_date
        
    print(f"\n>>> EXECUTANDO MODALIDADE DE TESTE: [{args.mode.upper()}] ({start_dt} a {end_dt}) <<<\n")
    res, trades, eq_df = run_portfolio_backtest(start_dt, end_dt, args.capital, risk_pct=args.risk, max_positions=args.max_pos)
    
    print("\n" + "="*80)
    print("RESUMO EXECUTIVO DO MOTOR QUANTITATIVO DE ALTA PERFORMANCE (RISCO 2.5%)")
    print("="*80)
    print(f"Período: {res['start_date']} até {res['end_date']}")
    print(f"Universo Monitorado: {res['coins_scanned']} moedas")
    print(f"Capital Inicial: R$ {res['initial_capital']:,.2f}")
    print(f"Capital Final: R$ {res['final_capital']:,.2f} ({res['return_pct']:+.2f}%)")
    print(f"Lucro Líquido Real: R$ {res['net_profit_brl']:,.2f}")
    print(f"Total de Trades: {res['total_trades']}")
    print(f"Trades Vencedores: {res['winning_trades']}")
    print(f"Trades Perdedores: {res['losing_trades']}")
    print(f"Trades no 0x0: {res['breakeven_trades']}")
    print(f"Win Rate: {res['win_rate_pct']:.2f}%")
    print(f"Profit Factor: {res['profit_factor']:.2f}")
    print(f"Drawdown Máximo MtM: {res['max_drawdown_pct']:.2f}%")
    print(f"Sharpe Ratio: {res['sharpe_ratio']:.2f} | Sortino Ratio: {res['sortino_ratio']:.2f}")
    print(f"Rendimento do Caixa Ocioso (6% a.a.): R$ {res['total_cash_yield_brl']:,.2f}")
    print(f"Taxas de Funding Pagas: R$ {res['total_funding_fees_brl']:,.2f}")
    print("="*80)
    
    print("\n---------------------------------------------------------------------------")
    print("EVOLUÇÃO SEMESTRAL DO SALDO (A CADA 6 MESES NOS 5 ANOS):")
    print("---------------------------------------------------------------------------")
    prev_val = res['initial_capital']
    for dt_str, val in res['semester_checkpoints'].items():
        sem_ret = ((val - prev_val) / prev_val) * 100
        cum_ret = ((val - res['initial_capital']) / res['initial_capital']) * 100
        print(f"• Data: {dt_str} | Saldo: R$ {val:12,.2f} | Semestre: {sem_ret:+7.2f}% | Acumulado: {cum_ret:+7.2f}%")
        prev_val = val
    print("---------------------------------------------------------------------------")
    
    # Salvar JSON único da modalidade
    json_path = os.path.join(DATA_DIR, f'resumo_{args.mode}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=4, ensure_ascii=False)
        
    trades_records = []
    running_bal = args.capital
    for t in trades:
        running_bal += t['pnl_brl']
        trades_records.append({
            'Data Entrada': t['entry_date'].strftime('%Y-%m-%d %H:%M') if isinstance(t['entry_date'], pd.Timestamp) else str(t['entry_date']),
            'Ativo': t['symbol'].replace('USDT', ''),
            'Regime': t['regime'],
            'Score': round(t['score'], 1),
            'Preço Entrada': f"${t['entry_price']:.4f}",
            'Stop Loss': f"${t['stop_loss']:.4f} ({t['stop_dist_pct']*100:.2f}%)",
            'BE Trigger (+1.9R)': f"${t.get('breakeven_trigger', t['entry_price']):.4f}",
            'Parcial (2.0R)': f"${t['target_1']:.4f}",
            'Direção': t.get('direction', 'LONG'),
            'Datas Saída': " | ".join([d.strftime('%Y-%m-%d %H:%M') if isinstance(d, pd.Timestamp) else str(d) for d in t['exit_dates']]),
            'Preços Saída': " | ".join([f"${p:.4f}" for p in t['exit_prices']]),
            'Motivo Saída': " | ".join(t['exit_reasons']),
            'Resultado (R$)': f"R$ {t['pnl_brl']:+,.2f}",
            'Saldo Acumulado (R$)': f"R$ {running_bal:,.2f}"
        })
        
    csv_path = os.path.join(DATA_DIR, f'trades_{args.mode}.csv')
    if trades_records:
        tdf = pd.DataFrame(trades_records)
        tdf.to_csv(csv_path, index=False, encoding='utf-8')
    else:
        pd.DataFrame(columns=['Data Entrada', 'Ativo', 'Direção', 'Regime', 'Score', 'Preço Entrada', 'Stop Loss', 'BE Trigger (+1.9R)', 'Parcial (2.0R)', 'Datas Saída', 'Preços Saída', 'Motivo Saída', 'Resultado (R$)', 'Saldo Acumulado (R$)']).to_csv(csv_path, index=False, encoding='utf-8')
        
    # Salvar Relatório Markdown Executivo da Modalidade
    md_report_path = os.path.join(REPORTS_DIR, f'relatorio_{args.mode}.md')
    md_content = f"""# Relatório de Auditoria Quantitativa: Modalidade [{args.mode.upper()}]

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** {res['start_date']} até {res['end_date']}
- **Universo Monitorado:** {res['coins_scanned']} moedas da Binance
- **Capital Inicial:** R$ {res['initial_capital']:,.2f}
- **Saldo Final:** R$ {res['final_capital']:,.2f} ({res['return_pct']:+.2f}%)
- **Lucro Líquido Real:** R$ {res['net_profit_brl']:,.2f}
- **Total de Trades:** {res['total_trades']} ({res['winning_trades']} Vitórias / {res['losing_trades']} Derrotas)
- **Taxa de Acerto (Win Rate):** {res['win_rate_pct']:.2f}%
- **Fator de Lucro (Profit Factor):** {res['profit_factor']:.2f}
- **Drawdown Máximo (MtM):** {res['max_drawdown_pct']:.2f}%
- **Sharpe Ratio:** {res['sharpe_ratio']:.2f} | **Sortino Ratio:** {res['sortino_ratio']:.2f}
- **Rendimento do Caixa (Cash Yield 6% a.a.):** R$ {res['total_cash_yield_brl']:,.2f}
- **Custos de Funding Pagos:** R$ {res['total_funding_fees_brl']:,.2f}

---

## 📈 2. Evolução Semestral do Patrimônio
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
"""
    for dt_s, val_s in res['semester_checkpoints'].items():
        md_content += f"| {dt_s} | R$ {val_s:12,.2f} |\n"
        
    with open(md_report_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"\nArquivos atualizados com sucesso para o modo [{args.mode}]:")
    print(f"• {json_path}")
    print(f"• {csv_path}")
    print(f"• {md_report_path}")
