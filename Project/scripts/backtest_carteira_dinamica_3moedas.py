"""
Motor de Simulação de Carteira Dinâmica Institucional (Até 3 Ativos Simultâneos)
Varredura Point-in-Time sobre o Mercado Total da Binance (~523 Moedas USDT)
Histórico Completo de 5 Anos (2021 a 2026) com Filtro de Regime de Mercado Anti-Chop

Princípios Estruturais Institucionais Aplicados:
1. Regime Macro de Tendência Confirmada do BTC (Anti-Chop):
   - Proibido Long se BTC 1D não estiver em tendência confirmada (Close 1D >= EMA50 1D e EMA20 1D >= EMA50 1D).
2. Alinhamento Multi-Timeframe (1D/4h na Moeda):
   - A moeda precisa estar saudável no gráfico diário (Close 1D >= EMA50 1D e Close 1D >= EMA20 1D).
3. Volume Institucional Real:
   - Volume 4h >= 1.5x da média dos últimos 20 períodos com CVD Comprador (> 0).
4. Rompimento de Pivô Técnico no 4h:
   - Close 4h > máxima recente dos 3 candles anteriores com RSI entre 50 e 68.
5. Gestão de Risco:
   - Risco Fixo de 2,5% por trade | Capital Inicial: R$ 100.000,00 | Max 3 Posições.
"""

import argparse
import datetime
import json
import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
COINS_DIR = os.path.join(RAW_DIR, 'coins')
MACRO_DIR = os.path.join(RAW_DIR, 'macro')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
DATA_DIR = os.path.join(BASE_DIR, 'data')

for d in [REPORTS_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

def load_macro_data():
    btc_4h_path = os.path.join(MACRO_DIR, 'BTCUSDT_4h.csv')
    btc_1d_path = os.path.join(MACRO_DIR, 'BTCUSDT_1d.csv')
    fng_path = os.path.join(MACRO_DIR, 'fear_and_greed.csv')
    
    btc_4h = pd.read_csv(btc_4h_path)
    btc_4h['open_time'] = pd.to_datetime(btc_4h['open_time_dt'] if 'open_time_dt' in btc_4h.columns else btc_4h['open_time'])
    btc_4h = compute_indicators_4h(btc_4h)
    
    btc_1d = pd.read_csv(btc_1d_path)
    btc_1d['open_time'] = pd.to_datetime(btc_1d['open_time_dt'] if 'open_time_dt' in btc_1d.columns else btc_1d['open_time'])
    btc_1d = compute_indicators_1d(btc_1d)
    
    fng_df = pd.DataFrame()
    if os.path.exists(fng_path):
        fng_df = pd.read_csv(fng_path)
        fng_df['timestamp'] = pd.to_datetime(fng_df['date'])
        fng_df['value'] = fng_df['value'].astype(float)
        fng_df = fng_df.sort_values('timestamp').reset_index(drop=True)
        
    return btc_4h, btc_1d, fng_df

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
    
    df['swing_low_3'] = df['low'].rolling(window=3).min()
    df['swing_high_3'] = df['high'].rolling(window=3).max()
    df['swing_low_10'] = df['low'].rolling(window=10).min()
    df['vol_sma20'] = df['volume'].rolling(window=20).mean()
    df['vol_ratio'] = df['volume'] / (df['vol_sma20'] + 1e-9)
    
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
        df['daily_avg_vol_30d'] = 0.0
        
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
    
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    plus_dm = df['high'].diff()
    minus_dm = -df['low'].diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)
    
    tr_smooth = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, min_periods=14, adjust=False).mean() / (tr_smooth + 1e-9))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, min_periods=14, adjust=False).mean() / (tr_smooth + 1e-9))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    df['adx14_1d'] = dx.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
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

def run_portfolio_backtest(start_date_str, end_date_str, initial_capital=100000.0, risk_pct=0.025, 
                           max_positions=3, min_daily_volume=25_000_000, fee_pct=0.00075):
    start_date = pd.to_datetime(start_date_str)
    end_date = pd.to_datetime(end_date_str)
    
    btc_4h, btc_1d, fng_df = load_macro_data()
    available_symbols = [d for d in os.listdir(COINS_DIR) if os.path.isdir(os.path.join(COINS_DIR, d))]
    
    coins_4h_map = {}
    coins_1d_map = {}
    funding_map = {}
    
    for s in available_symbols:
        k4h_p = os.path.join(COINS_DIR, s, 'klines_4h.csv')
        k1d_p = os.path.join(COINS_DIR, s, 'klines_1d.csv')
        fr_p = os.path.join(COINS_DIR, s, 'funding_rates.csv')
        
        if os.path.exists(k4h_p) and os.path.exists(k1d_p):
            df4 = pd.read_csv(k4h_p)
            df4['open_time'] = pd.to_datetime(df4['open_time_dt'] if 'open_time_dt' in df4.columns else df4['open_time'])
            df4 = compute_indicators_4h(df4)
            df4.set_index('open_time', inplace=True)
            coins_4h_map[s] = df4
            
            df1 = pd.read_csv(k1d_p)
            df1['open_time'] = pd.to_datetime(df1['open_time_dt'] if 'open_time_dt' in df1.columns else df1['open_time'])
            df1 = compute_indicators_1d(df1)
            df1.set_index('open_time', inplace=True)
            coins_1d_map[s] = df1
            
        if os.path.exists(fr_p):
            fr_df = pd.read_csv(fr_p)
            fr_df['fundingTime'] = pd.to_datetime(fr_df['fundingTime_dt'] if 'fundingTime_dt' in fr_df.columns else fr_df['fundingTime'])
            fr_df.sort_values('fundingTime', inplace=True)
            funding_map[s] = fr_df
            
    btc_4h_slice = btc_4h[(btc_4h['open_time'] >= start_date) & (btc_4h['open_time'] <= end_date)]
    all_timestamps = btc_4h_slice['open_time'].tolist()
    
    capital = initial_capital
    active_positions = {}
    trades = []
    vetoes = []
    equity_curve = [{'timestamp': start_date, 'capital': capital, 'cash': capital, 'active_count': 0}]
    
    # Checkpoints Semestrais (10 Semestres ao longo de 5 anos)
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
    
    for current_time in all_timestamps:
        btc_sub_1d = btc_1d[btc_1d['open_time'] < current_time]
        btc_sub_4h = btc_4h[btc_4h['open_time'] < current_time]
        if btc_sub_1d.empty or btc_sub_4h.empty:
            continue
            
        btc_last_1d = btc_sub_1d.iloc[-1]
        btc_last_4h = btc_sub_4h.iloc[-1]
        
        # FILTRO DE REGIME INSTITUCIONAL DO BITCOIN:
        # Tendência de Alta Confirmada no BTC:
        # 1. Preço do BTC >= EMA 50 1D
        # 2. EMA 20 1D >= EMA 50 1D (Tendência Rápida alinhada com a Lenta)
        # 3. BTC não pode estar colapsando no 4h (Close 4h >= EMA 50 4h)
        btc_macro_bullish = (btc_last_1d['close'] >= btc_last_1d['ema50_1d']) and \
                            (btc_last_1d['ema20_1d'] >= btc_last_1d['ema50_1d']) and \
                            (btc_last_4h['close'] >= btc_last_4h['ema50'])
        
        fng_val = 50.0
        if not fng_df.empty:
            fng_sub = fng_df[fng_df['timestamp'] <= current_time]
            if not fng_sub.empty:
                fng_val = fng_sub.iloc[-1]['value']
                
        # 1. Gerenciar Posições Abertas (Até 3)
        for s in list(active_positions.keys()):
            pos = active_positions[s]
            df4 = coins_4h_map.get(s)
            if df4 is None or current_time not in df4.index:
                continue
            candle = df4.loc[current_time]
            
            c_high = candle['high']
            c_low = candle['low']
            c_close = candle['close']
            c_ema20 = candle['ema20']
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
                rem_pct_funding = 0.5 if pos['partial_taken'] else 1.0
                current_notional = (allocated_capital * rem_pct_funding) * (c_close / entry_price)
                funding_fee = current_notional * fr_val
                capital -= funding_fee
                pos['pnl_brl'] -= funding_fee
                pos['funding_paid'] = pos.get('funding_paid', 0.0) + funding_fee
                
            # Abordagem Pessimista: Stop Loss tem prioridade absoluta em conflito intra-candle
            if c_low <= pos['stop_loss']:
                stop_slippage = 0.0008  # 8 bps
                stop_exec_price = pos['stop_loss'] * (1 - stop_slippage)
                if not pos['partial_taken']:
                    pct_loss = (stop_exec_price - entry_price) / entry_price
                    gross_pnl = allocated_capital * pct_loss
                    exit_fee = (allocated_capital * (1 + pct_loss)) * fee_pct
                    pnl_brl = gross_pnl - exit_fee
                    capital += pnl_brl
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(stop_exec_price)
                    pos['exit_reasons'].append("Stop no Breakeven (Pessimista)" if pos['be_moved'] else "Stop Loss Inicial (Pessimista)")
                    pos['pnl_brl'] += pnl_brl
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue
                else:
                    pct_loss = (stop_exec_price - entry_price) / entry_price
                    gross_pnl = (allocated_capital * 0.5) * pct_loss
                    exit_fee = (allocated_capital * 0.5 * (1 + pct_loss)) * fee_pct
                    pnl_brl = gross_pnl - exit_fee
                    capital += pnl_brl
                    pos['pnl_brl'] += pnl_brl
                    pos['exit_dates'].append(current_time)
                    pos['exit_prices'].append(stop_exec_price)
                    pos['exit_reasons'].append("Stop Breakeven 0x0 2ª metade (Pessimista)")
                    pos['final_capital'] = capital
                    pos['status'] = 'CLOSED'
                    trades.append(pos)
                    del active_positions[s]
                    continue
            elif c_rsi > 75 and fr_val > 0.0004:
                pct_return = (c_close - entry_price) / entry_price
                rem_pct = 0.5 if pos['partial_taken'] else 1.0
                gross_pnl = (allocated_capital * rem_pct) * pct_return
                exit_fee = (allocated_capital * rem_pct * (1 + pct_return)) * fee_pct
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
                if not pos['be_moved'] and c_high >= pos['be_trigger_price']:
                    pos['be_moved'] = True
                    pos['stop_loss'] = entry_price
                    
                if not pos['partial_taken']:
                    if c_high >= pos['target_1']:
                        pos['partial_taken'] = True
                        pos['be_moved'] = True
                        pos['stop_loss'] = entry_price
                        pct_gain_1 = (pos['target_1'] - entry_price) / entry_price
                        gross_pnl_1 = (allocated_capital * 0.5) * pct_gain_1
                        exit_fee_1 = (allocated_capital * 0.5 * (1 + pct_gain_1)) * fee_pct
                        pnl_1 = gross_pnl_1 - exit_fee_1
                        capital += pnl_1
                        pos['pnl_brl'] += pnl_1
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(pos['target_1'])
                        pos['exit_reasons'].append(f"Alvo 1 ({pos['rr_target1']}R)")
                        
                        if c_high >= pos['target_2']:
                            pct_gain_2 = (pos['target_2'] - entry_price) / entry_price
                            gross_pnl_2 = (allocated_capital * 0.5) * pct_gain_2
                            exit_fee_2 = (allocated_capital * 0.5 * (1 + pct_gain_2)) * fee_pct
                            pnl_2 = gross_pnl_2 - exit_fee_2
                            capital += pnl_2
                            pos['pnl_brl'] += pnl_2
                            pos['exit_dates'].append(current_time)
                            pos['exit_prices'].append(pos['target_2'])
                            pos['exit_reasons'].append("Alvo 2")
                            pos['final_capital'] = capital
                            pos['status'] = 'CLOSED'
                            trades.append(pos)
                            del active_positions[s]
                else:
                    if c_high >= pos['target_2']:
                        pct_gain_2 = (pos['target_2'] - entry_price) / entry_price
                        gross_pnl_2 = (allocated_capital * 0.5) * pct_gain_2
                        exit_fee_2 = (allocated_capital * 0.5 * (1 + pct_gain_2)) * fee_pct
                        pnl_2 = gross_pnl_2 - exit_fee_2
                        capital += pnl_2
                        pos['pnl_brl'] += pnl_2
                        pos['exit_dates'].append(current_time)
                        pos['exit_prices'].append(pos['target_2'])
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
                        
        # 2. Screener Dinâmico Point-in-Time & Scoring Matrix
        candidates = []
        
        for s in available_symbols:
            if s in active_positions or s == 'BTCUSDT':
                continue
                
            df4 = coins_4h_map.get(s)
            df1 = coins_1d_map.get(s)
            if df4 is None or df1 is None:
                continue
            if current_time not in df4.index:
                continue
                
            current_open_candle = df4.loc[current_time]
            loc_idx = df4.index.get_loc(current_time)
            
            # PASSO 1: SCREENER INSTITUCIONAL DINÂMICO
            # 1. Maturidade > 90 dias
            if loc_idx < 540:
                continue
                
            # 2. Volume Médio Diário dos Últimos 30 Dias > $25M
            prev_candle = df4.iloc[loc_idx - 1]
            candle_2ago = df4.iloc[loc_idx - 2]
            candle_3ago = df4.iloc[loc_idx - 3]
            
            daily_vol_30d = prev_candle['daily_avg_vol_30d']
            if daily_vol_30d < min_daily_volume:
                continue
                
            sub1d = df1[df1.index < current_time]
            if sub1d.empty:
                continue
            candle_1d = sub1d.iloc[-1]
            
            # PASSO 2: MATRIZ DE DECISÃO & VETOS
            veto_reasons = []
            
            # VETO 1: Veto Macro de Tendência Confirmada do BTC (Anti-Chop)
            if not btc_macro_bullish:
                veto_reasons.append("BTC sem Tendência Confirmada (EMA20 1D < EMA50 1D ou BTC < EMA50)")
                
            # VETO 2: Alinhamento Estrutural no Gráfico Diário (1D)
            is_1d_aligned = (candle_1d['close'] >= candle_1d['ema50_1d']) and (candle_1d['close'] >= candle_1d['ema20_1d'])
            if not is_1d_aligned:
                veto_reasons.append("Estrutura 1D Fraca (Preço 1D < EMA50 1D)")
                
            # VETO 3: Volume Institucional Mínimo (Volume Ratio >= 1.5 e CVD Positivo)
            if prev_candle['vol_ratio'] < 1.5 or prev_candle['cvd'] <= 0:
                veto_reasons.append("Falta de Volume Institucional (Ratio < 1.5 ou CVD Vendedor)")
                
            is_vest, vest_msg = is_vesting_cliff(s, current_time)
            if is_vest:
                veto_reasons.append(f"Vesting ({vest_msg})")
                
            fr_val = 0.0001
            if s in funding_map and not funding_map[s].empty:
                fr_sub = funding_map[s][funding_map[s]['fundingTime'] <= current_time]
                if not fr_sub.empty:
                    fr_val = fr_sub.iloc[-1]['fundingRate']
                    
            if fr_val > 0.0003:
                veto_reasons.append(f"Funding Rate Alto ({fr_val*100:.4f}% > 0.03%)")
                
            # Score (0-100)
            macro_score = 20 if btc_macro_bullish else 0
            
            ema_aligned = (prev_candle['ema20'] > prev_candle['ema50']) and (prev_candle['close'] > prev_candle['ema20'])
            ema_major_aligned = (prev_candle['ema50'] > prev_candle['ema200']) or (prev_candle['close'] > prev_candle['ema200'])
            tech_score = 15 if (ema_aligned and ema_major_aligned) else (8 if prev_candle['close'] > prev_candle['ema20'] else 0)
            
            rsi_val, adx_val = prev_candle['rsi14'], prev_candle['adx14']
            if 50 <= rsi_val <= 68:
                tech_score += 15
            elif 45 <= rsi_val < 50:
                tech_score += 8
                
            deriv_score = 15 if fr_val <= 0.0001 else (8 if fr_val <= 0.0002 else 0)
            deriv_score += 10 if (prev_candle['cvd'] > 0 and prev_candle['vol_ratio'] >= 1.5) else 0
            
            onchain_score = 25
            total_score = macro_score + tech_score + deriv_score + onchain_score
            
            entry_price = current_open_candle['open'] * 1.0005  # Abertura + 5 bps slippage
            
            # STOP LOSS TÉCNICO CALIBRADO (2,5% a 6,0%)
            raw_stop = min(prev_candle['low'], candle_2ago['low']) - (0.3 * prev_candle['atr14'])
            raw_dist_pct = (entry_price - raw_stop) / entry_price
            stop_dist_pct = min(max(raw_dist_pct, 0.025), 0.060)
            stop_loss = entry_price * (1 - stop_dist_pct)
            stop_dist = entry_price - stop_loss
            
            is_strong_trend = btc_macro_bullish and (adx_val > 22)
            rr_target1 = 2.5 if is_strong_trend else 1.8
            rr_target2 = 4.0 if is_strong_trend else 2.8
            be_trigger_price = entry_price + stop_dist
            target_1 = entry_price + (rr_target1 * stop_dist)
            target_2 = entry_price + (rr_target2 * stop_dist)
            
            # GATILHO DE CONFLUÊNCIA INSTITUCIONAL
            recent_max_high = max(candle_2ago['high'], candle_3ago['high'])
            pivot_breakout = (prev_candle['close'] > recent_max_high) and (prev_candle['close'] > prev_candle['open'])
            trend_active = (prev_candle['close'] > prev_candle['ema20']) and (prev_candle['ema20'] > prev_candle['ema50'])
            momentum_ok = (50 <= rsi_val <= 68)
            volume_burst = (prev_candle['vol_ratio'] >= 1.5) and (prev_candle['cvd'] > 0)
            
            valid_signal = pivot_breakout and trend_active and momentum_ok and volume_burst
            regime_str = "Tendência (2.5R)" if is_strong_trend else "Consolidação (1.8R)"
            
            if valid_signal:
                if total_score >= 80 and len(veto_reasons) == 0:
                    candidates.append({
                        'symbol': s, 'score': total_score, 'entry_price': entry_price,
                        'stop_loss': stop_loss, 'stop_dist': stop_dist, 'stop_dist_pct': stop_dist_pct,
                        'be_trigger_price': be_trigger_price, 'target_1': target_1, 'target_2': target_2,
                        'rr_target1': rr_target1, 'regime': regime_str, 'daily_vol_30d': daily_vol_30d
                    })
                else:
                    vetoes.append({
                        'date': current_time,
                        'symbol': s.replace('USDT', ''),
                        'score': total_score,
                        'motivo': " | ".join(veto_reasons) if veto_reasons else f"Score insuficiente ({total_score}/100 < 80)"
                    })
                    
        # 3. Alocação Dinâmica nas Melhores Oportunidades (Top 3)
        if candidates and len(active_positions) < max_positions:
            candidates.sort(key=lambda x: x['score'], reverse=True)
            available_slots = max_positions - len(active_positions)
            selected_candidates = candidates[:available_slots]
            
            for c in selected_candidates:
                risk_brl = capital * risk_pct  # 2.5% de risco fixo
                allocated_capital = min(risk_brl / c['stop_dist_pct'], capital * 2.0)
                entry_fee = allocated_capital * fee_pct
                capital -= entry_fee
                
                active_positions[c['symbol']] = {
                    'symbol': c['symbol'], 'entry_date': current_time, 'entry_price': c['entry_price'],
                    'stop_loss': c['stop_loss'], 'stop_dist': c['stop_dist'], 'stop_dist_pct': c['stop_dist_pct'],
                    'be_trigger_price': c['be_trigger_price'], 'be_moved': False,
                    'target_1': c['target_1'], 'target_2': c['target_2'], 'rr_target1': c['rr_target1'], 'regime': c['regime'],
                    'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                    'score': c['score'], 'candles_held': 0, 'partial_taken': False,
                    'exit_dates': [], 'exit_prices': [], 'exit_reasons': [], 'pnl_brl': -entry_fee, 'status': 'OPEN',
                    'funding_paid': 0.0
                }
                
        # Curva de Patrimônio Mark-to-Market
        unrealized_pnl = 0.0
        for s_act, p_act in active_positions.items():
            df_sym_curr = coins_4h_map.get(s_act)
            if df_sym_curr is not None and current_time in df_sym_curr.index:
                c_close_now = df_sym_curr.loc[current_time]['close']
                rem_pct_now = 0.5 if p_act['partial_taken'] else 1.0
                pct_ret_now = (c_close_now - p_act['entry_price']) / p_act['entry_price']
                unrealized_pnl += (p_act['allocated_capital'] * rem_pct_now) * pct_ret_now
                
        total_mtm_equity = capital + unrealized_pnl
        equity_curve.append({
            'timestamp': current_time,
            'capital': total_mtm_equity,
            'realized_capital': capital,
            'unrealized_pnl': unrealized_pnl,
            'active_count': len(active_positions)
        })
        
        # Gravar Checkpoints Semestrais
        for sm in semesters:
            if current_time == sm or (current_time > sm and sm.strftime('%Y-%m-%d') not in semester_checkpoints):
                semester_checkpoints[sm.strftime('%Y-%m-%d')] = total_mtm_equity
                
    # Fechamento de posições restantes no fim da simulação
    for s, pos in list(active_positions.items()):
        df4 = coins_4h_map.get(s)
        if df4 is not None:
            last_sub = df4[df4.index <= end_date]
            if not last_sub.empty:
                last_candle = last_sub.iloc[-1]
                c_close = last_candle['close']
                rem_pct = 0.5 if pos['partial_taken'] else 1.0
                pct_return = (c_close - pos['entry_price']) / pos['entry_price']
                gross_pnl = (pos['allocated_capital'] * rem_pct) * pct_return
                exit_fee = (pos['allocated_capital'] * rem_pct * (1 + pct_return)) * fee_pct
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
        'total_funding_fees_brl': total_funding_fees,
        'total_vetoes': len(vetoes),
        'coins_scanned': len(available_symbols),
        'semester_checkpoints': semester_checkpoints
    }
    
    return summary, trades, vetoes, equity_df

def main():
    parser = argparse.ArgumentParser(description="Simulação Institucional de Carteira Dinâmica (5 Anos / Anti-Chop BTC / R$ 100k)")
    parser.add_argument('--start', type=str, default="2021-11-15", help="Data de Início (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, default="2026-08-20", help="Data de Fim (YYYY-MM-DD)")
    parser.add_argument('--capital', type=float, default=100000.0, help="Capital Inicial em R$")
    parser.add_argument('--risk', type=float, default=0.025, help="Risco Fixo por Trade (0.025 = 2.5%)")
    parser.add_argument('--max-pos', type=int, default=3, help="Número Máximo de Posições Concomitantes")
    parser.add_argument('--min-vol', type=float, default=25_000_000, help="Volume Médio Diário Mínimo em USD")
    
    args = parser.parse_args()
    
    print("=" * 85)
    print("BACKTEST INSTITUCIONAL DE 5 ANOS (FILTRO DE REGIME CONFIRMADO / ANTI-CHOP)")
    print(f"Janela Temporal: {args.start} a {args.end}")
    print(f"Capital Inicial: R$ {args.capital:,.2f} | Risco: {args.risk*100:.1f}% | Max Posições: {args.max_pos}")
    print(f"Screener: Volume 30d > ${args.min_vol/1e6:.1f}M/dia | BTC Trend Confirmada (EMA20 1D >= EMA50 1D)")
    print("=" * 85)
    
    summary, trades, vetoes, equity_df = run_portfolio_backtest(
        args.start, args.end, initial_capital=args.capital, risk_pct=args.risk,
        max_positions=args.max_pos, min_daily_volume=args.min_vol
    )
    
    print("\n" + "=" * 85)
    print("RESUMO EXECUTIVO CONSOLIDADO DA CARTEIRA INSTITUCIONAL (5 ANOS)")
    print("=" * 85)
    print(f"Período Auditado:      {summary['start_date']} a {summary['end_date']}")
    print(f"Universo Monitorado:   {summary['coins_scanned']} moedas")
    print(f"Capital Inicial:       R$ {summary['initial_capital']:,.2f}")
    print(f"Saldo Final:           R$ {summary['final_capital']:,.2f} ({summary['return_pct']:+.2f}%)")
    print(f"Lucro Líquido:         R$ {summary['net_profit_brl']:+,.2f}")
    print(f"Total de Trades:       {summary['total_trades']}")
    print(f"Trades Vencedores:     {summary['winning_trades']}")
    print(f"Trades Perdedores:     {summary['losing_trades']}")
    print(f"Trades no 0x0:         {summary['breakeven_trades']}")
    print(f"Win Rate:              {summary['win_rate_pct']:.2f}%")
    print(f"Profit Factor:         {summary['profit_factor']:.2f}")
    print(f"Drawdown Máximo (MtM): {summary['max_drawdown_pct']:.2f}%")
    print(f"Custos Funding Rate:   R$ {summary['total_funding_fees_brl']:,.2f}")
    print(f"Vetos de Proteção:     {summary['total_vetoes']}")
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
    
    # Salvar Trades CSV
    trades_export = []
    for t in trades:
        trades_export.append({
            'Data Entrada': t['entry_date'].strftime('%Y-%m-%d %H:%M'),
            'Ativo': t['symbol'].replace('USDT', ''),
            'Regime': t['regime'],
            'Score': f"{t['score']}/100",
            'Preço Entrada': f"${t['entry_price']:.4f}",
            'Stop Loss': f"${t['stop_loss']:.4f} (-{t['stop_dist_pct']*100:.2f}%)",
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
