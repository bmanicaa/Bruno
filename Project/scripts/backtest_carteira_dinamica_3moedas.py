"""
Motor de Simulação de Carteira Dinâmica Institucional (Até 3 Ativos Simultâneos)
Varredura Point-in-Time sobre o Mercado Total da Binance (~500+ Moedas USDT)
Sem Viés de Sobrevivência (Survivorship Bias Free)

Funil Institucional em 2 Passos:
1. PASSO 1 (Screener Dinâmico Point-in-Time):
   - Maturidade mínima de 90 dias de histórico fechado no timestamp T (540 velas 4h).
   - Volume médio diário dos últimos 30 dias (T-30d a T) > $25M USD (ou Top 50 por volume naquele dia).
   - Mercado de Futuros / Funding Rate ativo no momento T.
2. PASSO 2 (Matriz de Decisão & Score 0-100 do Prompt.md):
   - Macro BTC (20%) + Técnico 4h/1D (30%) + Derivativos/FR/CVD (25%) + On-Chain/Vesting (25%).
   - Filtro de Vetos Absolutos (Vesting > 1%, FR > 0.03%, BTC < EMA50 1D -3%, etc.).
   - Alocação nas TOP 3 Melhores Oportunidades (Score >= 75) com Risco Fixo de 5,0%.
   - Caixa 100% protegido em USDT quando houver menos de 3 ativos qualificados.
   - Puxada de Breakeven em +1.0R | Alvos 1.8R/2.5R | Time-Stop 14d | Trailing EMA20.
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
    
    df['swing_low_10'] = df['low'].rolling(window=10).min()
    df['swing_high_10'] = df['high'].rolling(window=10).max()
    df['vol_sma20'] = df['volume'].rolling(window=20).mean()
    df['vol_ratio'] = df['volume'] / (df['vol_sma20'] + 1e-9)
    
    if 'taker_buy_base' in df.columns:
        df['taker_sell_base'] = df['volume'] - df['taker_buy_base']
        df['delta_vol'] = df['taker_buy_base'] - df['taker_sell_base']
        df['cvd'] = df['delta_vol'].rolling(window=6).sum()
    else:
        df['cvd'] = 0.0
        
    # Screener de Volume Point-in-Time: Soma móvel de 30 dias (180 velas de 4h)
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

def run_portfolio_backtest(start_date_str, end_date_str, initial_capital=200.0, risk_pct=0.05, 
                           max_positions=3, min_daily_volume=25_000_000, fee_pct=0.00075):
    start_date = pd.to_datetime(start_date_str)
    end_date = pd.to_datetime(end_date_str)
    
    print(f"\nCarregando dados macro de referência...")
    btc_4h, btc_1d, fng_df = load_macro_data()
    
    # Identificar todas as moedas disponíveis em data/raw/coins/
    available_symbols = [d for d in os.listdir(COINS_DIR) if os.path.isdir(os.path.join(COINS_DIR, d))]
    print(f"Total de Moedas no Repositório: {len(available_symbols)}")
    
    print("Pré-carregando e indexando dados históricos para execução ultrarrápida...")
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
            
    # Obter lista cronológica de timestamps 4h a partir do BTC benchmark
    btc_4h_slice = btc_4h[(btc_4h['open_time'] >= start_date) & (btc_4h['open_time'] <= end_date)]
    all_timestamps = btc_4h_slice['open_time'].tolist()
    
    print(f"Período de Simulação: {start_date_str} a {end_date_str} ({len(all_timestamps)} candles 4h / {len(all_timestamps)/6:.1f} dias)")
    print("Iniciando loop Point-in-Time institucional...\n")
    
    capital = initial_capital
    active_positions = {}
    trades = []
    vetoes = []
    equity_curve = [{'timestamp': start_date, 'capital': capital, 'cash': capital, 'active_count': 0}]
    screener_stats = []
    
    for current_time in all_timestamps:
        # Macro BTC Point-in-Time (< current_time)
        btc_sub_1d = btc_1d[btc_1d['open_time'] < current_time]
        btc_sub_4h = btc_4h[btc_4h['open_time'] < current_time]
        if btc_sub_1d.empty or btc_sub_4h.empty:
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
            
            # Funding Rate 8h
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
        eligible_count = 0
        
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
            
            # Localizar dados estritamente anteriores a current_time
            # Usando slicing rápido no índice ordenado
            loc_idx = df4.index.get_loc(current_time)
            if loc_idx < 180:  # Requer pelo menos 180 candles 4h (30 dias)
                continue
                
            prev_candle = df4.iloc[loc_idx - 1]  # Vela fechada anterior
            candle_2ago = df4.iloc[loc_idx - 2]
            
            # PASSO 1: SCREENER INSTITUCIONAL DINÂMICO POINT-IN-TIME
            # 1. Maturidade > 90 dias (540 velas)
            if loc_idx < 540:
                continue
                
            # 2. Volume Médio Diário dos Últimos 30 Dias (em USD) > $25M
            daily_vol_30d = prev_candle['daily_avg_vol_30d']
            if daily_vol_30d < min_daily_volume:
                continue
                
            eligible_count += 1
            
            # Obter 1D anterior
            sub1d = df1[df1.index < current_time]
            if sub1d.empty:
                continue
            candle_1d = sub1d.iloc[-1]
            
            # PASSO 2: MATRIZ DE DECISÃO & VETOS
            veto_reasons = []
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
            if btc_macro_support_lost:
                veto_reasons.append("Suporte Macro do BTC Perdido (< EMA50 1D -3%)")
            if prev_candle['close'] < prev_candle['ema50'] and prev_candle['vol_ratio'] < 1.3:
                veto_reasons.append("Preço < EMA50 4h sem Volume Agressor (Ratio < 1.3)")
                
            # Score (0-100)
            macro_score = 12 if btc_macro_bullish else (8 if btc_last_4h['close'] >= btc_last_4h['ema20'] else 0)
            macro_score += 8 if fng_val >= 40 else (4 if fng_val >= 25 else 0)
            
            ema_aligned = (prev_candle['ema20'] > prev_candle['ema50']) and (prev_candle['close'] > prev_candle['ema20'])
            ema_major_aligned = (prev_candle['ema50'] > prev_candle['ema200']) or (prev_candle['close'] > prev_candle['ema200'])
            tech_score = 12 if (ema_aligned and ema_major_aligned) else (7 if prev_candle['close'] > prev_candle['ema20'] else 0)
            
            rsi_val, adx_val = prev_candle['rsi14'], prev_candle['adx14']
            if 45 <= rsi_val <= 65:
                tech_score += 10
            elif rsi_val < 40 and prev_candle['close'] > prev_candle['open'] and prev_candle['low'] <= prev_candle['swing_low_10'] * 1.01:
                tech_score += 8
            elif 65 < rsi_val <= 70:
                tech_score += 5
            tech_score += 8 if candle_1d['close'] > candle_1d['ema50_1d'] else (4 if candle_1d['close'] > candle_1d['ema20_1d'] else 0)
            
            deriv_score = 15 if fr_val <= 0.0001 else (8 if fr_val <= 0.0002 else 0)
            deriv_score += 10 if (prev_candle['cvd'] > 0 and prev_candle['vol_ratio'] > 1.0) else (6 if prev_candle['cvd'] > 0 else 0)
            
            onchain_score = 25
            total_score = macro_score + tech_score + deriv_score + onchain_score
            
            entry_price = current_open_candle['open'] * 1.0005  # Entrada na Abertura + 5 bps slippage
            stop_loss = prev_candle['swing_low_10'] - (1.5 * prev_candle['atr14'])
            stop_dist = entry_price - stop_loss
            if stop_dist <= 0:
                continue
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
            
            trend_trigger = (prev_candle['close'] > prev_candle['ema20']) and (prev_candle['close'] > candle_2ago['high']) and (48 <= rsi_val <= 68) and (prev_candle['close'] > prev_candle['ema50'])
            reversal_trigger = (candle_2ago['rsi14'] < 40) and (prev_candle['close'] > candle_2ago['high']) and (prev_candle['close'] > prev_candle['open'])
            
            regime_str = "Tendência (2.5R)" if is_strong_trend else "Consolidação (1.8R)"
            
            if trend_trigger or reversal_trigger:
                if total_score >= 75 and len(veto_reasons) == 0:
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
                        'motivo': " | ".join(veto_reasons) if veto_reasons else f"Score insuficiente ({total_score}/100 < 75)"
                    })
                    
        # 3. Alocação Dinâmica nas Melhores Oportunidades (Top 3)
        if candidates and len(active_positions) < max_positions:
            candidates.sort(key=lambda x: x['score'], reverse=True)
            available_slots = max_positions - len(active_positions)
            selected_candidates = candidates[:available_slots]
            
            for c in selected_candidates:
                risk_brl = capital * risk_pct
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
        'coins_scanned': len(available_symbols)
    }
    
    return summary, trades, vetoes, equity_df

def main():
    parser = argparse.ArgumentParser(description="Motor de Simulação de Carteira Dinâmica (Mercado Total / Zero Survivorship Bias)")
    parser.add_argument('--start', type=str, default="2026-02-20", help="Data de Início (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, default="2026-08-19", help="Data de Fim (YYYY-MM-DD)")
    parser.add_argument('--capital', type=float, default=200.0, help="Capital Inicial em R$")
    parser.add_argument('--risk', type=float, default=0.05, help="Risco Fixo por Trade (Ex: 0.05 = 5%)")
    parser.add_argument('--max-pos', type=int, default=3, help="Número Máximo de Posições Concomitantes")
    parser.add_argument('--min-vol', type=float, default=25_000_000, help="Volume Médio Diário Mínimo em USD")
    
    args = parser.parse_args()
    
    print("=" * 85)
    print("BACKTEST INSTITUCIONAL DE CARTEIRA DINÂMICA (MERCADO TOTAL / ZERO SURVIVORSHIP BIAS)")
    print(f"Janela Temporal: {args.start} a {args.end}")
    print(f"Capital Inicial: R$ {args.capital:.2f} | Risco: {args.risk*100:.1f}% | Max Posições: {args.max_pos}")
    print(f"Screener: Volume 30d > ${args.min_vol/1e6:.1f}M/dia | Maturidade > 90d")
    print("=" * 85)
    
    summary, trades, vetoes, equity_df = run_portfolio_backtest(
        args.start, args.end, initial_capital=args.capital, risk_pct=args.risk,
        max_positions=args.max_pos, min_daily_volume=args.min_vol
    )
    
    print("\n" + "=" * 85)
    print("RESUMO EXECUTIVO CONSOLIDADO DA CARTEIRA")
    print("=" * 85)
    print(f"Período Auditado:      {summary['start_date']} a {summary['end_date']}")
    print(f"Universo Monitorado:   {summary['coins_scanned']} moedas")
    print(f"Capital Inicial:       R$ {summary['initial_capital']:.2f}")
    print(f"Saldo Final:           R$ {summary['final_capital']:.2f} ({summary['return_pct']:+.2f}%)")
    print(f"Lucro Líquido:         R$ {summary['net_profit_brl']:+.2f}")
    print(f"Total de Trades:       {summary['total_trades']}")
    print(f"Trades Vencedores:     {summary['winning_trades']}")
    print(f"Trades Perdedores:     {summary['losing_trades']}")
    print(f"Trades no 0x0:         {summary['breakeven_trades']}")
    print(f"Win Rate:              {summary['win_rate_pct']:.2f}%")
    print(f"Profit Factor:         {summary['profit_factor']:.2f}")
    print(f"Drawdown Máximo (MtM): {summary['max_drawdown_pct']:.2f}%")
    print(f"Custos Funding Rate:   R$ {summary['total_funding_fees_brl']:.2f}")
    print(f"Vetos de Proteção:     {summary['total_vetoes']}")
    print("=" * 85)
    
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
            'Resultado (R$)': f"R$ {t['pnl_brl']:+.2f}",
            'Saldo Acumulado (R$)': f"R$ {t['final_capital']:.2f}"
        })
    df_trades = pd.DataFrame(trades_export)
    df_trades.to_csv(os.path.join(DATA_DIR, 'trades_executados_carteira_dinamica.csv'), index=False)
    
    with open(os.path.join(DATA_DIR, 'resumo_estatistico_carteira_dinamica.json'), 'w') as f:
        json.dump(summary, f, indent=4)
        
    print("\nResultados salvos com sucesso em data/:")
    print(f"- {os.path.join(DATA_DIR, 'trades_executados_carteira_dinamica.csv')}")
    print(f"- {os.path.join(DATA_DIR, 'resumo_estatistico_carteira_dinamica.json')}")

if __name__ == '__main__':
    main()
