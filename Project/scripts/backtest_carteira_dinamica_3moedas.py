"""
Motor de Simulação de Carteira Dinâmica Institucional (Estado da Arte Consolidado)
Arquitetura Dual-Timeframe Hierárquica (1D comanda regime / 4h executa timing)
Universo Completo da Binance (~536 Moedas incluindo BTCUSDT) ao longo de 5 Anos (2021 a 2026)

Princípios de Alta Performance Quantitativa:
1. Long-Only Institucional com Filtro Macro Secular:
   - Operações compradas apenas quando BTC 1D >= EMA200 1D e EMA50 1D >= EMA200 1D.
   - Bear Market (2022): 100% Protegido em Caixa USDT Remunerado a 6% a.a. (Zero risco de mercado).
2. Força Relativa Institucional (Alpha vs BTC 7d):
   - Altcoins selecionadas apenas se Retorno 7d >= Retorno 7d do BTC. BTC elegível automaticamente em ralis.
3. Gestão de Alvos em 3 Estágios (Segurança + Trava de Lucro + Cauda Longa):
   - Alvo 1 (50% da mão): 2.0R (trava +1.0R líquido e move stop da posição restante para Breakeven Protegido).
   - Alvo 2 (30% da mão): 4.0R (trava +1.2R líquido no topo da expansão).
   - Runner (20% da mão): Conduzido por Trailing na EMA50 4h sem teto para capturar ralis de 8R a 25R.
4. Remuneração Ativa de Caixa (*Cash Yield*):
   - Rendimento passivo institucional de 6,0% a.a. creditado a cada candle 4h sobre o saldo em USDT não alocado.
5. Blindagem Temporal Point-in-Time com custos reais de corretagem (0,075%), funding e slippage de 8 bps.
"""

import argparse
import datetime
import json
import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
COINS_DIR = os.path.join(RAW_DIR, 'coins')
MACRO_DIR = os.path.join(RAW_DIR, 'macro')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
DATA_DIR = os.path.join(BASE_DIR, 'data')

for d in [REPORTS_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

def compute_indicators_4h(df):
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
        
    df['candle_count'] = list(range(len(df)))
    return df

def compute_indicators_1d(df):
    df = df.copy()
    for c in ['open', 'high', 'low', 'close', 'volume']:
        if c in df.columns:
            df[c] = df[c].astype(float)
    df['ema20_1d'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50_1d'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema200_1d'] = df['close'].ewm(span=200, adjust=False).mean()
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
    btc_4h['open_time'] = pd.to_datetime(btc_4h['open_time_dt'] if 'open_time_dt' in btc_4h.columns else btc_4h['open_time'])
    btc_4h = compute_indicators_4h(btc_4h)
    btc_4h.sort_values('open_time', inplace=True)
    
    btc_1d = pd.read_csv(btc_1d_path)
    btc_1d['open_time'] = pd.to_datetime(btc_1d['open_time_dt'] if 'open_time_dt' in btc_1d.columns else btc_1d['open_time'])
    btc_1d = compute_indicators_1d(btc_1d)
    btc_1d.sort_values('open_time', inplace=True)
    
    btc_1d_sub = btc_1d[['open_time', 'close', 'ema20_1d', 'ema50_1d', 'ema200_1d']].copy()
    btc_1d_sub.columns = ['open_time_1d', 'close_1d', 'ema20_1d', 'ema50_1d', 'ema200_1d']
    btc_4h_merged = pd.merge_asof(
        btc_4h, btc_1d_sub,
        left_on='open_time', right_on='open_time_1d',
        direction='backward'
    )
    btc_4h_merged.set_index('open_time', inplace=True)
    
    fng_df = pd.DataFrame()
    if os.path.exists(fng_path):
        fng_df = pd.read_csv(fng_path)
        fng_df['timestamp'] = pd.to_datetime(fng_df['date'])
        fng_df['value'] = fng_df['value'].astype(float)
        fng_df = fng_df.sort_values('timestamp').reset_index(drop=True)
        
    available_symbols = [d for d in os.listdir(COINS_DIR) if os.path.isdir(os.path.join(COINS_DIR, d))]
    if 'BTCUSDT' not in available_symbols:
        available_symbols.append('BTCUSDT')
        
    coins_4h_map = {'BTCUSDT': btc_4h_merged}
    funding_map = {}
    
    print(f"Carregando e indexando {len(available_symbols)} moedas (incluindo BTCUSDT)...")
    
    for s in available_symbols:
        if s == 'BTCUSDT':
            continue
        k4h_p = os.path.join(COINS_DIR, s, 'klines_4h.csv')
        k1d_p = os.path.join(COINS_DIR, s, 'klines_1d.csv')
        fr_p = os.path.join(COINS_DIR, s, 'funding_rates.csv')
        
        if os.path.exists(k4h_p) and os.path.exists(k1d_p):
            df4 = pd.read_csv(k4h_p)
            df4['open_time'] = pd.to_datetime(df4['open_time_dt'] if 'open_time_dt' in df4.columns else df4['open_time'])
            df4 = compute_indicators_4h(df4)
            df4.sort_values('open_time', inplace=True)
            
            df1 = pd.read_csv(k1d_p)
            df1['open_time'] = pd.to_datetime(df1['open_time_dt'] if 'open_time_dt' in df1.columns else df1['open_time'])
            df1 = compute_indicators_1d(df1)
            df1.sort_values('open_time', inplace=True)
            
            df1_sub = df1[['open_time', 'close', 'ema20_1d', 'ema50_1d', 'ema200_1d']].copy()
            df1_sub.columns = ['open_time_1d', 'close_1d', 'ema20_1d', 'ema50_1d', 'ema200_1d']
            
            df4 = pd.merge_asof(
                df4, df1_sub,
                left_on='open_time', right_on='open_time_1d',
                direction='backward'
            )
            
            df4.set_index('open_time', inplace=True)
            coins_4h_map[s] = df4
            
        if os.path.exists(fr_p):
            fr_df = pd.read_csv(fr_p)
            fr_df['fundingTime'] = pd.to_datetime(fr_df['fundingTime_dt'] if 'fundingTime_dt' in fr_df.columns else fr_df['fundingTime'])
            fr_df.sort_values('fundingTime', inplace=True)
            funding_map[s] = fr_df
            
    return btc_4h, btc_1d, fng_df, coins_4h_map, funding_map, available_symbols

def run_portfolio_backtest(start_date_str, end_date_str, initial_capital=100000.0, risk_pct=0.0125,
                           max_positions=3, min_daily_volume=25_000_000, fee_pct=0.00075,
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
        
        is_bull = (last_1d['close'] >= last_1d['ema200_1d']) and \
                  (last_1d['close'] >= last_1d['ema50_1d']) and \
                  (last_1d['ema50_1d'] >= last_1d['ema200_1d']) and \
                  (last_4h['close'] >= last_4h['ema50'])
        btc_macro_map[ts] = is_bull
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
    
    print("Pre-indexando candidatos qualificados (Dual-Timeframe 1D -> 4h + BTC + Alpha)...")
    candidates_by_time = {ts: [] for ts in all_timestamps}
    
    for s in available_symbols:
        df4 = coins_4h_map.get(s)
        if df4 is None or len(df4) < 540:
            continue
            
        idx_times = df4.index
        valid_mask = (idx_times >= start_date) & (idx_times <= end_date)
        valid_indices = np.where(valid_mask)[0]
        
        for loc_idx in valid_indices:
            if loc_idx < 540:
                continue
            current_time = idx_times[loc_idx]
            
            prev_candle = df4.iloc[loc_idx - 1]
            candle_2ago = df4.iloc[loc_idx - 2]
            candle_3ago = df4.iloc[loc_idx - 3]
            
            # 1. Volume 30d > $25M
            if prev_candle['daily_avg_vol_30d'] < min_daily_volume:
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
            
            # 6. FILTRO ANTI-PAVIO (Anti-Trap de rejeição superior)
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
            
            # STOP LOSS TÉCNICO CALIBRADO (Mínima dos últimos 5 candles - 1.2 * ATR)
            recent_5_lows = df4.iloc[loc_idx-5:loc_idx]['low'].min()
            raw_stop = recent_5_lows - (1.2 * prev_candle['atr14'])
            raw_dist_pct = (entry_price - raw_stop) / entry_price
            stop_dist_pct = min(max(raw_dist_pct, 0.035 if s == 'BTCUSDT' else 0.040), 0.080)
            stop_loss = entry_price * (1 - stop_dist_pct)
            stop_dist = entry_price - stop_loss
            
            # Alvos em 3 Estágios: Alvo 1 = 2.0R (50%), Alvo 2 = 4.0R (30%), Runner = 20%
            target_1 = entry_price + (2.0 * stop_dist)
            target_2 = entry_price + (4.0 * stop_dist)
            
            btc_bonus = 15 if s == 'BTCUSDT' else 0
            score = 100 + (coin_ret7d - btc_ret7d)*100 + (prev_candle['adx14'] - 20) + btc_bonus
            
            candidates_by_time[current_time].append({
                'symbol': s,
                'score': score,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'stop_dist': stop_dist,
                'stop_dist_pct': stop_dist_pct,
                'target_1': target_1,
                'target_2': target_2,
                'regime': "Tendência Institucional (2.0R / 4.0R / Runner)",
                'adx_val': prev_candle['adx14']
            })
            
    print("Iniciando loop de simulação da carteira...")
    
    for current_time in all_timestamps:
        btc_bull = btc_macro_map.get(current_time, False)
        
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
            
            # Débito de Funding nas janelas UTC 00:00, 08:00, 16:00
            if current_time.hour in [0, 8, 16]:
                current_notional = (allocated_capital * pos['remaining_pct']) * (c_close / entry_price)
                funding_fee = current_notional * fr_val
                capital -= funding_fee
                pos['pnl_brl'] -= funding_fee
                pos['funding_paid'] = pos.get('funding_paid', 0.0) + funding_fee

            # GESTÃO DA POSIÇÃO EM 3 ESTÁGIOS
            # Estágio 1: Antes do Alvo 1 (100% da mão ativa)
            if not pos['t1_taken']:
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
                    pos['exit_reasons'].append("Alvo 1 (2.0R / 50%)")
                    
                    # Travar stop dos 50% restantes no Breakeven Protegido
                    pos['stop_loss'] = entry_price * 1.004
                    
                    # Se na mesma vela atingir o Alvo 2
                    if c_high >= pos['target_2']:
                        pos['t2_taken'] = True
                        pos['remaining_pct'] = 0.20 # sobram 20% para o runner
                        pct_gain_2 = (pos['target_2'] - entry_price) / entry_price
                        gross_pnl_2 = (allocated_capital * 0.30) * pct_gain_2
                        exit_fee_2 = (allocated_capital * 0.30 * (1 + pct_gain_2)) * fee_pct
                        pnl_2 = gross_pnl_2 - exit_fee_2
                        capital += pnl_2
                        pos['pnl_brl'] += pnl_2
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(pos['target_2'])
                        pos['exit_reasons'].append("Alvo 2 (4.0R / 30%)")
                elif c_low <= pos['stop_loss']:
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
                elif c_rsi > 75 and fr_val > 0.0004:
                    pct_return = (c_close - entry_price) / entry_price
                    gross_pnl = allocated_capital * pct_return
                    exit_fee = (allocated_capital * (1 + pct_return)) * fee_pct
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
                    continue
                elif pos['candles_held'] >= 84:
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
                    continue
            # Estágio 2: Alvo 1 já executado (50% restante rodando)
            elif pos['t1_taken'] and not pos['t2_taken']:
                if c_high >= pos['target_2']:
                    pos['t2_taken'] = True
                    pos['remaining_pct'] = 0.20
                    pct_gain_2 = (pos['target_2'] - entry_price) / entry_price
                    gross_pnl_2 = (allocated_capital * 0.30) * pct_gain_2
                    exit_fee_2 = (allocated_capital * 0.30 * (1 + pct_gain_2)) * fee_pct
                    pnl_2 = gross_pnl_2 - exit_fee_2
                    capital += pnl_2
                    pos['pnl_brl'] += pnl_2
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(pos['target_2'])
                    pos['exit_reasons'].append("Alvo 2 (4.0R / 30%)")
                elif c_low <= pos['stop_loss']:
                    stop_slippage = 0.0008
                    stop_exec_price = pos['stop_loss'] * (1 - stop_slippage)
                    pct_pnl = (stop_exec_price - entry_price) / entry_price
                    gross_pnl = (allocated_capital * pos['remaining_pct']) * pct_pnl
                    exit_fee = (allocated_capital * pos['remaining_pct'] * (1 + pct_pnl)) * fee_pct
                    pnl_brl = gross_pnl - exit_fee
                    capital += pnl_brl
                    pos['pnl_brl'] += pnl_brl
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(stop_exec_price)
                    pos['exit_reasons'].append("Stop Breakeven Protegido (50%)")
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue
                elif c_close < c_ema50:
                    pct_gain_trail = (c_close - entry_price) / entry_price
                    gross_pnl_trail = (allocated_capital * pos['remaining_pct']) * pct_gain_trail
                    exit_fee_trail = (allocated_capital * pos['remaining_pct'] * (1 + pct_gain_trail)) * fee_pct
                    pnl_trail = gross_pnl_trail - exit_fee_trail
                    capital += pnl_trail
                    pos['pnl_brl'] += pnl_trail
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(c_close)
                    pos['exit_reasons'].append("Trailing EMA50 4h (50%)")
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue
            # Estágio 3: Alvo 1 e Alvo 2 executados (20% Runner livre surfando a tendência)
            elif pos['t2_taken']:
                if c_low <= pos['stop_loss']:
                    stop_slippage = 0.0008
                    stop_exec_price = pos['stop_loss'] * (1 - stop_slippage)
                    pct_pnl = (stop_exec_price - entry_price) / entry_price
                    gross_pnl = (allocated_capital * pos['remaining_pct']) * pct_pnl
                    exit_fee = (allocated_capital * pos['remaining_pct'] * (1 + pct_pnl)) * fee_pct
                    pnl_brl = gross_pnl - exit_fee
                    capital += pnl_brl
                    pos['pnl_brl'] += pnl_brl
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(stop_exec_price)
                    pos['exit_reasons'].append("Stop Breakeven Runner (20%)")
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue
                elif c_close < c_ema50:
                    pct_gain_trail = (c_close - entry_price) / entry_price
                    gross_pnl_trail = (allocated_capital * pos['remaining_pct']) * pct_gain_trail
                    exit_fee_trail = (allocated_capital * pos['remaining_pct'] * (1 + pct_gain_trail)) * fee_pct
                    pnl_trail = gross_pnl_trail - exit_fee_trail
                    capital += pnl_trail
                    pos['pnl_brl'] += pnl_trail
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(c_close)
                    pos['exit_reasons'].append("Trailing EMA50 Runner (20%)")
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue

        # 3. Seleção de Candidatos
        raw_candidates = candidates_by_time.get(current_time, [])
        if btc_bull and raw_candidates and len(active_positions) < max_positions:
            eligible_candidates = [c for c in raw_candidates if c['symbol'] not in active_positions]
            if eligible_candidates:
                eligible_candidates.sort(key=lambda x: x['score'], reverse=True)
                available_slots = max_positions - len(active_positions)
                selected = eligible_candidates[:available_slots]
                
                for c in selected:
                    risk_brl = capital * risk_pct
                    allocated_capital = min(risk_brl / c['stop_dist_pct'], capital * 1.5)
                    entry_fee = allocated_capital * fee_pct
                    capital -= entry_fee
                    
                    active_positions[c['symbol']] = {
                        'symbol': c['symbol'], 'entry_date': current_time, 'entry_price': c['entry_price'],
                        'stop_loss': c['stop_loss'], 'stop_dist': c['stop_dist'], 'stop_dist_pct': c['stop_dist_pct'],
                        'target_1': c['target_1'], 'target_2': c['target_2'], 'regime': c['regime'],
                        'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                        'score': c['score'], 'candles_held': 0, 't1_taken': False, 't2_taken': False,
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
    total_funding_fees = sum(t.get('funding_paid', 0.0) for t in trades)
    
    summary = {
        'start_date': str(start_date_str),
        'end_date': str(end_date_str),
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
        'total_cash_yield_brl': total_cash_yield_earned,
        'total_funding_fees_brl': total_funding_fees,
        'coins_scanned': len(available_symbols),
        'semester_checkpoints': semester_checkpoints
    }
    
    return summary, trades, equity_df

def main():
    parser = argparse.ArgumentParser(description="Simulação Institucional Estado da Arte (5 Anos / R$ 100k)")
    parser.add_argument('--start', type=str, default="2021-11-15", help="Data de Início (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, default="2026-08-20", help="Data de Fim (YYYY-MM-DD)")
    parser.add_argument('--capital', type=float, default=100000.0, help="Capital Inicial em R$")
    parser.add_argument('--risk', type=float, default=0.0125, help="Risco Fixo por Trade (0.0125 = 1.25%)")
    parser.add_argument('--max-pos', type=int, default=3, help="Número Máximo de Posições Concomitantes")
    parser.add_argument('--min-vol', type=float, default=25_000_000, help="Volume Médio Diário Mínimo em USD")
    parser.add_argument('--yield-rate', type=float, default=0.06, help="Taxa Anual de Remuneração do Caixa (0.06 = 6% a.a.)")
    
    args = parser.parse_args()
    
    print("=" * 85)
    print("BACKTEST INSTITUCIONAL ESTADO DA ARTE CONSOLIDADO (5 ANOS)")
    print(f"Janela Temporal: {args.start} a {args.end}")
    print(f"Capital Inicial: R$ {args.capital:,.2f} | Risco: {args.risk*100:.2f}% | Max Posições: {args.max_pos}")
    print(f"Motores: 3 Estágios de Alvos (2.0R / 4.0R / Runner) + Cash Yield 6% a.a. + BTC Habilitado")
    print("=" * 85)
    
    summary, trades, equity_df = run_portfolio_backtest(
        args.start, args.end, initial_capital=args.capital, risk_pct=args.risk,
        max_positions=args.max_pos, min_daily_volume=args.min_vol, annual_cash_yield=args.yield_rate
    )
    
    print("\n" + "=" * 85)
    print("RESUMO EXECUTIVO CONSOLIDADO DA CARTEIRA ESTADO DA ARTE (5 ANOS)")
    print("=" * 85)
    print(f"Período Auditado:      {summary['start_date']} a {summary['end_date']}")
    print(f"Universo Monitorado:   {summary['coins_scanned']} moedas")
    print(f"Capital Inicial:       R$ {summary['initial_capital']:,.2f}")
    print(f"Saldo Final:           R$ {summary['final_capital']:,.2f} ({summary['return_pct']:+.2f}%)")
    print(f"Lucro Líquido Real:    R$ {summary['net_profit_brl']:+,.2f}")
    print(f"Total de Trades:       {summary['total_trades']}")
    print(f"Trades Vencedores:     {summary['winning_trades']}")
    print(f"Trades Perdedores:     {summary['losing_trades']}")
    print(f"Trades no 0x0:         {summary['breakeven_trades']}")
    print(f"Win Rate:              {summary['win_rate_pct']:.2f}%")
    print(f"Profit Factor:         {summary['profit_factor']:.2f}")
    print(f"Drawdown Máximo (MtM): {summary['max_drawdown_pct']:.2f}%")
    print(f"Rendimento de Caixa:   R$ {summary['total_cash_yield_brl']:+,.2f} (Yield 6% a.a.)")
    print(f"Custos Funding Rate:   R$ {summary['total_funding_fees_brl']:,.2f}")
    print("=" * 85)
    
    print("\n" + "-" * 75)
    print("EVOLUÇÃO SEMESTRAL DO SALDO (A CADA 6 MESES NOS 5 ANOS):")
    print("-" * 75)
    prev_val = args.capital
    for date_str, val in summary['semester_checkpoints'].items():
        ret_sem = ((val - prev_val) / prev_val) * 100
        ret_cum = ((val - args.capital) / args.capital) * 100
        print(f"• Data: {date_str} | Saldo: R$ {val:12,.2f} | Semestre: {ret_sem:+7.2f}% | Acumulado: {ret_cum:+7.2f}%")
        prev_val = val
    print("-" * 75)
    
    trades_export = []
    for t in trades:
        trades_export.append({
            'Data Entrada': t['entry_date'].strftime('%Y-%m-%d %H:%M'),
            'Ativo': t['symbol'].replace('USDT', ''),
            'Regime': t['regime'],
            'Score': f"{t['score']:.1f}",
            'Preço Entrada': f"${t['entry_price']:.4f}",
            'Stop Loss': f"${t['stop_loss']:.4f} ({t['stop_dist_pct']*100:.2f}%)",
            'Alvo 1': f"${t['target_1']:.4f}",
            'Alvo 2': f"${t['target_2']:.4f}",
            'Datas Saída': " | ".join([d.strftime('%Y-%m-%d %H:%M') for d in t['exit_dates']]),
            'Preços Saída': " | ".join([f"${p:.4f}" for p in t['exit_prices']]),
            'Motivo Saída': " | ".join(t['exit_reasons']),
            'Resultado (R$)': f"R$ {t['pnl_brl']:+,.2f}",
            'Saldo Acumulado (R$)': f"R$ {t['final_capital']:,.2f}"
        })
    df_trades = pd.DataFrame(trades_export)
    df_trades.to_csv(os.path.join(DATA_DIR, 'trades_executados_institucional_5anos.csv'), index=False)
    
    with open(os.path.join(DATA_DIR, 'resumo_estatistico_institucional_5anos.json'), 'w') as f:
        json.dump(summary, f, indent=4)
        
    print("\nResultados salvos com sucesso:")
    print(f"- {os.path.join(DATA_DIR, 'trades_executados_institucional_5anos.csv')}")
    print(f"- {os.path.join(DATA_DIR, 'resumo_estatistico_institucional_5anos.json')}")

if __name__ == '__main__':
    main()
