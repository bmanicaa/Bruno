"""
Motor de Simulação de Carteira Dinâmica Quantitativa (Prompt2.md)
Período: 360 dias a 180 dias atrás (24 de Agosto de 2025 a 20 de Fevereiro de 2026)
Universo: 20 Ativos Líquidos da Binance + BTCUSDT Macro
- SOL, ETH, BNB, NEAR, AVAX, SUI, APT, ARB, OP, RENDER,
  FET, ONDO, LINK, AAVE, INJ, PENDLE, TIA, PEPE, GALA, TON (+ BTC)

Regras Estritas de Prompt2.md:
- Risco Fixo de 5,0% por trade (alocação baseada na distância do Stop Loss, máx 2.5x alavancagem)
- Limite Máximo de 3 Posições Abertas Simultaneamente
- Ranking Dinâmico por Score (0-100) Point-in-Time a cada candle 4h
- Gestão de Caixa Dinâmica (USDT) quando houver menos de 3 ativos qualificados
- Taxas Reais da Binance (0,075% maker/taker com BNB) na entrada e na saída
- Funding Rates a cada 8h debitados/creditados na posição
- Breakeven Antecipado em +1.0R (move stop para 0x0)
- Alvos Adaptativos (1.8R consolidação / 2.5R tendência) com 50% parcial no Alvo 1
- Trailing Stop na EMA 20 4h / Alvo 2 (2.8R / 4.0R) para os 50% restantes
- Time-Stop de 14 dias (84 candles 4h) sem Alvo 1
- Stop Loss Inicial (100% da posição)
- Saída por Exaustão (RSI 4h > 75 e FR > 0.04%)
- Vetos Obrigatórios: Vesting (>1% em 7d), Funding Rate (>0.03%), BTC Macro Perdido, EMA50 sem volume
"""

import datetime
import math
import os
import json
import time
import numpy as np
import pandas as pd
import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cache_360d_180d')
os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_klines_extended(symbol, interval='4h', start_time_ms=None, end_time_ms=None, total_candles=2500):
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_{interval}_klines.parquet")
    if os.path.exists(cache_file):
        try:
            df = pd.read_parquet(cache_file)
            if not df.empty and df['open_time'].min() <= pd.to_datetime(start_time_ms, unit='ms') and df['open_time'].max() >= pd.to_datetime(end_time_ms - 86400000, unit='ms'):
                return df
        except Exception:
            pass

    url = 'https://api.binance.com/api/v3/klines'
    all_data = []
    curr_start = start_time_ms
    
    while True:
        params = {'symbol': symbol, 'interval': interval, 'limit': 1000}
        if curr_start:
            params['startTime'] = curr_start
        if end_time_ms:
            params['endTime'] = end_time_ms
            
        try:
            r = requests.get(url, params=params, timeout=10).json()
            if not r or not isinstance(r, list) or len(r) == 0:
                break
            all_data.extend(r)
            curr_start = r[-1][0] + 1
            if len(r) < 1000 or (end_time_ms and curr_start >= end_time_ms):
                break
            time.sleep(0.05)
        except Exception as e:
            print(f"Erro ao buscar klines para {symbol}: {e}")
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
        
    try:
        df.to_parquet(cache_file, index=False)
    except Exception:
        pass
        
    return df

def fetch_funding_rates_extended(symbol, start_time_ms=None, end_time_ms=None):
    fut_symbol = '1000PEPEUSDT' if symbol == 'PEPEUSDT' else symbol
    cache_file = os.path.join(CACHE_DIR, f"{fut_symbol}_funding.parquet")
    if os.path.exists(cache_file):
        try:
            df = pd.read_parquet(cache_file)
            if not df.empty:
                return df
        except Exception:
            pass

    url = 'https://fapi.binance.com/fapi/v1/fundingRate'
    all_data = []
    curr_start = start_time_ms
    
    while True:
        params = {'symbol': fut_symbol, 'limit': 1000}
        if curr_start:
            params['startTime'] = curr_start
        if end_time_ms:
            params['endTime'] = end_time_ms
            
        try:
            r = requests.get(url, params=params, timeout=10).json()
            if not r or not isinstance(r, list) or len(r) == 0:
                break
            all_data.extend(r)
            curr_start = r[-1]['fundingTime'] + 1
            if len(r) < 1000 or (end_time_ms and curr_start >= end_time_ms):
                break
            time.sleep(0.05)
        except Exception as e:
            print(f"Erro ao buscar Funding Rate para {symbol}: {e}")
            break
            
    if not all_data:
        return pd.DataFrame()
        
    df = pd.DataFrame(all_data)
    if not df.empty and 'fundingTime' in df.columns:
        df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
        df['fundingRate'] = df['fundingRate'].astype(float)
        df = df.drop_duplicates(subset=['fundingTime']).sort_values('fundingTime').reset_index(drop=True)
        try:
            df.to_parquet(cache_file, index=False)
        except Exception:
            pass
        return df
    return pd.DataFrame()

def fetch_fear_and_greed():
    cache_file = os.path.join(CACHE_DIR, "fear_and_greed.parquet")
    if os.path.exists(cache_file):
        try:
            df = pd.read_parquet(cache_file)
            if not df.empty:
                return df
        except Exception:
            pass

    try:
        url = 'https://api.alternative.me/fng/?limit=0'
        r = requests.get(url, timeout=10)
        data = r.json().get('data', [])
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
        df['value'] = df['value'].astype(float)
        df = df.sort_values('timestamp').reset_index(drop=True)
        try:
            df.to_parquet(cache_file, index=False)
        except Exception:
            pass
        return df
    except Exception as e:
        print(f"Erro ao buscar Fear & Greed: {e}")
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
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi14_1d'] = 100 - (100 / (1 + rs))
    return df

def is_vesting_cliff_universe(symbol, dt):
    """
    Verificação de vesting para o universo de 20 moedas:
    - SUI: Cliff mensal dia 1 (dias 24 a 02)
    - APT: Cliff mensal dia 11/12 (dias 5 a 13)
    - ARB: Cliff mensal dia 16 (dias 9 a 17)
    - OP: Cliff mensal no fim do mês (dias 24 a 31)
    - TIA: Mega cliff anual dia 31/10 (dias 24/10 a 02/11)
    - GALA: Emissões trimestrais (meses 1, 4, 7, 10, dias 15 a 25)
    - ONDO: Cliff anual em Janeiro (dias 11 a 19 de Janeiro)
    """
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
    elif 'ARB' in symbol:
        if 9 <= dt.day <= 17:
            return True, "Desbloqueio de Vesting ARB > 1% (Cliff mensal no dia 16)"
    elif 'OP' in symbol and not 'PEPE' in symbol:
        if dt.day >= 24:
            return True, "Desbloqueio de Vesting OP > 1% (Cliff no fim do mês)"
    elif 'TIA' in symbol:
        if dt.month == 10 and dt.day >= 24:
            return True, "Desbloqueio Massivo Anual TIA > 1% (Cliff 31/10)"
        if dt.month == 11 and dt.day <= 2:
            return True, "Desbloqueio Massivo Anual TIA > 1% (Pós-Cliff 31/10)"
    elif 'GALA' in symbol:
        if dt.month in [1, 4, 7, 10] and 15 <= dt.day <= 25:
            return True, "Janela de Desbloqueio/Emissão GALA > 1%"
    elif 'ONDO' in symbol:
        if dt.month == 1 and 11 <= dt.day <= 19:
            return True, "Desbloqueio Anual ONDO > 1% (Cliff Janeiro)"
    return False, ""

def run_simulation(symbols, data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, initial_capital=200.0, risk_pct=0.05, fee_pct=0.00075, max_positions=3):
    start_date = pd.to_datetime("2025-08-24 00:00:00")
    end_date = pd.to_datetime("2026-02-20 00:00:00")
    
    capital = initial_capital
    trades = []
    vetoes = []
    active_positions = {}
    
    ref_sym = 'BTCUSDT' if 'BTCUSDT' in data_4h else symbols[0]
    all_timestamps = data_4h[ref_sym][(data_4h[ref_sym]['open_time'] >= start_date) & 
                                      (data_4h[ref_sym]['open_time'] <= end_date)]['open_time'].tolist()
                                      
    equity_curve = [{'timestamp': start_date, 'capital': capital, 'cash': capital, 'active_count': 0}]
    
    for current_time in all_timestamps:
        btc_sub_1d = btc_1d[btc_1d['open_time'] <= current_time]
        btc_sub_4h = btc_4h[btc_4h['open_time'] <= current_time]
        if len(btc_sub_1d) == 0 or len(btc_sub_4h) == 0:
            continue
            
        btc_last_1d = btc_sub_1d.iloc[-1]
        btc_last_4h = btc_sub_4h.iloc[-1]
        btc_macro_bullish = btc_last_1d['close'] >= btc_last_1d['ema50_1d']
        btc_macro_support_lost = btc_last_1d['close'] < (btc_last_1d['ema50_1d'] * 0.97)
        
        fng_val = 50.0
        if not fng_df.empty:
            fng_sub = fng_df[fng_df['timestamp'] <= current_time]
            if not fng_sub.empty:
                fng_val = fng_sub.iloc[-1]['value']
                
        # 1. Gerenciar Posições Ativas (Até 3)
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
                    
            # Cobrança de Funding Rate a cada 8h (00:00, 08:00, 16:00)
            if current_time.hour in [0, 8, 16]:
                remaining_pct = 0.5 if pos['partial_taken'] else 1.0
                current_notional = (pos['allocated_capital'] * remaining_pct) * (c_close / pos['entry_price'])
                funding_cost = current_notional * fr_val
                capital -= funding_cost
                pos['funding_fees_paid'] += funding_cost
                pos['pnl_brl'] -= funding_cost
                
            entry_price = pos['entry_price']
            stop_loss = pos['stop_loss']
            target_1 = pos['target_1']
            target_2 = pos['target_2']
            be_trigger_price = pos['be_trigger_price']
            allocated_capital = pos['allocated_capital']
            
            pos['candles_held'] += 1
            
            # Saída por Exaustão (RSI > 75 + FR Alto > 0.04%)
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
            # Time-Stop de 14 Dias (84 candles 4h sem Alvo 1)
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
                # Breakeven Antecipado em +1.0R
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
                        
                        # Se no mesmo candle bateu Alvo 2
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
                    # Gerenciar 2ª metade da posição
                    if c_low <= pos['stop_loss']:
                        pct_be = (pos['stop_loss'] - entry_price) / entry_price
                        gross_pnl_be = (allocated_capital * 0.5) * pct_be
                        exit_fee = (allocated_capital * 0.5 * (1 + pct_be)) * fee_pct
                        pnl_brl = gross_pnl_be - exit_fee
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
                        
        # 2. Avaliar e Rankear Sinais dos 20 Ativos Point-in-Time
        candidates = []
        for s in symbols:
            if s in active_positions:
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
            is_vest, vest_msg = is_vesting_cliff_universe(s, current_time)
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
                
            # Score (0 - 100)
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
                        'rr_target1': rr_target1, 'rr_target2': rr_target2, 'regime': regime_str
                    })
                else:
                    # Log de Oportunidade Vetada
                    idx = df_sym_4h[df_sym_4h['open_time'] == current_time].index[0]
                    sub_future = df_sym_4h.iloc[idx+1:idx+15]
                    outcome = "Não Executado"
                    simulated_loss = 0.0
                    if not sub_future.empty:
                        min_future_low = sub_future['low'].min()
                        max_future_high = sub_future['high'].max()
                        if min_future_low <= stop_loss:
                            simulated_loss = capital * risk_pct
                            outcome = f"Prejuízo evitado: -R$ {simulated_loss:.2f} (-{stop_dist_pct*100:.2f}%)"
                        elif max_future_high >= target_1:
                            outcome = "Alvo 1 atingido (Filtrado pelo protocolo)"
                        else:
                            outcome = "Consolidação sem alvo/stop"
                            
                    vetoes.append({
                        'date': current_time,
                        'symbol': s.replace('USDT', ''),
                        'score': total_score,
                        'motivo': " | ".join(veto_reasons) if veto_reasons else f"Score insuficiente ({total_score}/100 < 75)",
                        'outcome': outcome,
                        'prejuizo_evitado': simulated_loss
                    })
                    
        # 3. Alocação Dinâmica nas Melhores Oportunidades (Top 3)
        if candidates and len(active_positions) < max_positions:
            candidates.sort(key=lambda x: x['score'], reverse=True)
            available_slots = max_positions - len(active_positions)
            selected_candidates = candidates[:available_slots]
            
            for c in selected_candidates:
                risk_brl = capital * risk_pct  # 5% de risco fixo
                allocated_capital = min(risk_brl / c['stop_dist_pct'], capital * 2.5)
                entry_fee = allocated_capital * fee_pct
                capital -= entry_fee
                
                active_positions[c['symbol']] = {
                    'symbol': c['symbol'], 'entry_date': current_time, 'entry_price': c['entry_price'],
                    'stop_loss': c['stop_loss'], 'stop_dist': c['stop_dist'], 'stop_dist_pct': c['stop_dist_pct'],
                    'be_trigger_price': c['be_trigger_price'], 'be_moved': False,
                    'target_1': c['target_1'], 'target_2': c['target_2'], 'rr_target1': c['rr_target1'], 'rr_target2': c['rr_target2'],
                    'regime': c['regime'], 'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                    'score': c['score'], 'candles_held': 0, 'partial_taken': False,
                    'funding_fees_paid': 0.0,
                    'exit_dates': [], 'exit_prices': [], 'exit_reasons': [], 'pnl_brl': -entry_fee, 'status': 'OPEN'
                }
                
        equity_curve.append({
            'timestamp': current_time,
            'capital': capital,
            'active_count': len(active_positions)
        })
        
    # Fechamento Mark-to-Market de Posições no Fim do Período
    for s, pos in list(active_positions.items()):
        df_sym_4h = data_4h[s]
        last_sub = df_sym_4h[df_sym_4h['open_time'] <= end_date]
        if not last_sub.empty:
            last_candle = last_sub.iloc[-1]
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
    
    summary = {
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
        'total_vetoes': len(vetoes),
        'total_prejuizo_evitado': sum(v['prejuizo_evitado'] for v in vetoes)
    }
    
    return summary, trades, vetoes, equity_df

def main():
    print("="*80)
    print("INICIANDO BACKTEST DE 360d A 180d ATRÁS (24/08/2025 A 20/02/2026)")
    print("Protocolo: Prompt2.md (Carteira Dinâmica 3 Ativos / Risco Fixo 5.0%)")
    print("Universo: 20 Ativos da Binance + BTC Macro")
    print("="*80)
    
    symbols = [
        'SOLUSDT', 'ETHUSDT', 'BNBUSDT', 'NEARUSDT', 'AVAXUSDT',
        'SUIUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT', 'RENDERUSDT',
        'FETUSDT', 'ONDOUSDT', 'LINKUSDT', 'AAVEUSDT', 'INJUSDT',
        'PENDLEUSDT', 'TIAUSDT', 'PEPEUSDT', 'GALAUSDT', 'TONUSDT'
    ]
    
    # Período de Warmup: desde 01/06/2025 até 21/02/2026
    start_warmup_ms = int(datetime.datetime(2025, 6, 1, 0, 0).timestamp() * 1000)
    end_sim_ms = int(datetime.datetime(2026, 2, 21, 0, 0).timestamp() * 1000)
    
    print("\n1. Baixando dados de referência do BTCUSDT (Macro)...")
    btc_4h_raw = fetch_klines_extended('BTCUSDT', interval='4h', start_time_ms=start_warmup_ms, end_time_ms=end_sim_ms)
    btc_1d_raw = fetch_klines_extended('BTCUSDT', interval='1d', start_time_ms=start_warmup_ms, end_time_ms=end_sim_ms)
    btc_4h = compute_indicators_4h(btc_4h_raw)
    btc_1d = compute_indicators_1d(btc_1d_raw)
    
    print("2. Baixando Fear & Greed Index...")
    fng_df = fetch_fear_and_greed()
    
    data_4h = {}
    data_1d = {}
    funding_data = {}
    
    print("3. Baixando e processando 20 ativos do pool...")
    for s in symbols:
        print(f"   -> Processando {s}...")
        df_4h_raw = fetch_klines_extended(s, interval='4h', start_time_ms=start_warmup_ms, end_time_ms=end_sim_ms)
        df_1d_raw = fetch_klines_extended(s, interval='1d', start_time_ms=start_warmup_ms, end_time_ms=end_sim_ms)
        data_4h[s] = compute_indicators_4h(df_4h_raw)
        data_1d[s] = compute_indicators_1d(df_1d_raw)
        funding_data[s] = fetch_funding_rates_extended(s, start_time_ms=start_warmup_ms, end_time_ms=end_sim_ms)
        
    print("\n" + "="*80)
    print("EXECUTANDO SIMULAÇÃO POINT-IN-TIME (24/08/2025 a 20/02/2026)")
    print("="*80)
    
    summary, trades, vetoes, equity_df = run_simulation(
        symbols, data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df,
        initial_capital=200.0, risk_pct=0.05, fee_pct=0.00075, max_positions=3
    )
    
    # Cálculo em Escala R$ 100k
    scale_factor = 100000.0 / 200.0
    summary_100k = {
        'initial_capital': 100000.0,
        'final_capital': summary['final_capital'] * scale_factor,
        'net_profit_brl': summary['net_profit_brl'] * scale_factor,
        'return_pct': summary['return_pct'],
        'total_trades': summary['total_trades'],
        'winning_trades': summary['winning_trades'],
        'losing_trades': summary['losing_trades'],
        'breakeven_trades': summary['breakeven_trades'],
        'win_rate_pct': summary['win_rate_pct'],
        'profit_factor': summary['profit_factor'],
        'max_drawdown_pct': summary['max_drawdown_pct'],
        'total_vetoes': summary['total_vetoes'],
        'total_prejuizo_evitado': summary['total_prejuizo_evitado'] * scale_factor
    }
    
    print("\n" + "="*80)
    print("RESULTADOS CONSOLIDADOS DO BACKTEST (360d a 180d atrás)")
    print("="*80)
    print(f"Período:               24/08/2025 00:00 a 20/02/2026 00:00 (180 Dias)")
    print(f"Capital Inicial (Base): R$ {summary['initial_capital']:.2f}")
    print(f"Saldo Final (Base):     R$ {summary['final_capital']:.2f} ({summary['return_pct']:+.2f}%)")
    print(f"Lucro Líquido (Base):   R$ {summary['net_profit_brl']:+.2f}")
    print(f"Capital Inicial (100k): R$ {summary_100k['initial_capital']:,.2f}")
    print(f"Saldo Final (100k):     R$ {summary_100k['final_capital']:,.2f} ({summary_100k['return_pct']:+.2f}%)")
    print(f"Lucro Líquido (100k):   R$ {summary_100k['net_profit_brl']:+,.2f}")
    print(f"Total de Trades:       {summary['total_trades']}")
    print(f"Trades Vencedores:     {summary['winning_trades']}")
    print(f"Trades Perdedores:     {summary['losing_trades']}")
    print(f"Trades no 0x0:         {summary['breakeven_trades']}")
    print(f"Win Rate:              {summary['win_rate_pct']:.2f}%")
    print(f"Profit Factor:         {summary['profit_factor']:.2f}")
    print(f"Drawdown Máximo:       {summary['max_drawdown_pct']:.2f}%")
    print(f"Vetos de Proteção:     {summary['total_vetoes']}")
    print(f"Prejuízo Evitado (Base): R$ {summary['total_prejuizo_evitado']:.2f}")
    print(f"Prejuízo Evitado (100k): R$ {summary_100k['total_prejuizo_evitado']:,.2f}")
    print("="*80)
    
    # Análise de Performance por Ativo
    asset_performance = {}
    for t in trades:
        sym = t['symbol'].replace('USDT', '')
        if sym not in asset_performance:
            asset_performance[sym] = {'trades': 0, 'wins': 0, 'pnl_brl': 0.0, 'pnl_100k': 0.0}
        asset_performance[sym]['trades'] += 1
        if t['pnl_brl'] > 0.001:
            asset_performance[sym]['wins'] += 1
        asset_performance[sym]['pnl_brl'] += t['pnl_brl']
        asset_performance[sym]['pnl_100k'] += t['pnl_brl'] * scale_factor
        
    print("\nPERFORMANCE POR ATIVO:")
    for sym, perf in sorted(asset_performance.items(), key=lambda x: x[1]['pnl_brl'], reverse=True):
        wr = (perf['wins'] / perf['trades'] * 100) if perf['trades'] > 0 else 0
        print(f"{sym:10s} | Trades: {perf['trades']:2d} | WinRate: {wr:5.1f}% | PnL Base: R$ {perf['pnl_brl']:+7.2f} | PnL 100k: R$ {perf['pnl_100k']:+10.2f}")
        
    # Exportar Dados
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # 1. Trades Executados CSV
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
            'Funding Fees (R$)': f"R$ {t['funding_fees_paid']:.2f}",
            'Resultado Base (R$)': f"R$ {t['pnl_brl']:+.2f}",
            'Resultado 100k (R$)': f"R$ {t['pnl_brl']*scale_factor:+,.2f}",
            'Saldo Acumulado Base': f"R$ {t['final_capital']:.2f}"
        })
    df_trades = pd.DataFrame(trades_export)
    df_trades.to_csv('data/trades_executados_360d_a_180d.csv', index=False)
    
    # 2. Oportunidades Vetadas CSV
    vetoes_export = []
    for v in vetoes:
        vetoes_export.append({
            'Data': v['date'].strftime('%Y-%m-%d %H:%M'),
            'Ativo': v['symbol'],
            'Score': f"{v['score']}/100",
            'Motivo do Veto': v['motivo'],
            'Resultado Simulado': v['outcome'],
            'Prejuízo Evitado Base': f"R$ {v['prejuizo_evitado']:.2f}" if v['prejuizo_evitado'] > 0 else "R$ 0,00",
            'Prejuízo Evitado 100k': f"R$ {v['prejuizo_evitado']*scale_factor:,.2f}" if v['prejuizo_evitado'] > 0 else "R$ 0,00"
        })
    df_vetoes = pd.DataFrame(vetoes_export)
    df_vetoes.to_csv('data/oportunidades_vetadas_360d_a_180d.csv', index=False)
    
    # 3. Resumo Estatístico JSON
    full_summary = {
        'periodo': '2025-08-24 00:00:00 a 2026-02-20 00:00:00',
        'universo_ativos': [s.replace('USDT', '') for s in symbols],
        'simulacao_base_200': summary,
        'simulacao_escala_100k': summary_100k,
        'performance_por_ativo': asset_performance
    }
    with open('data/resumo_estatistico_360d_a_180d.json', 'w', encoding='utf-8') as f:
        json.dump(full_summary, f, indent=4, ensure_ascii=False)
        
    print("\nArquivos salvos com sucesso:")
    print("1. data/trades_executados_360d_a_180d.csv")
    print("2. data/oportunidades_vetadas_360d_a_180d.csv")
    print("3. data/resumo_estatistico_360d_a_180d.json")

if __name__ == '__main__':
    main()
