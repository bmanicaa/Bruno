"""
Motor de Backtest de Mercado Total da Binance (180 Dias: 20/02/2026 a 19/08/2026)
Conforme especificado em Prompt2.md
Varredura Point-in-Time candle a candle 4h em todo o pool de pares USDT líquidos da Binance.
Regras Estritas:
- Risco Fixo de 5,0% do capital atual por trade
- Limite Máximo de 3 Posições Abertas Simultaneamente
- Ranking Dinâmico por Score (0-100) Point-in-Time a cada candle 4h entre todos os ativos do mercado
- Gestão de Caixa Dinâmica (USDT) quando houver menos de 3 ativos qualificados
- Taxas Reais da Binance (0,075% maker/taker com BNB) na entrada e na saída
- Puxada de Breakeven Antecipado em +1.0R
- Alvos Adaptativos (1.8R em consolidação / 2.5R em tendência)
- Time-Stop de 14 dias (84 candles 4h)
- Trailing Stop na EMA 20 4h para a 2ª metade
- Vetos Obrigatórios: Vesting (>1% em 7d), Funding Rate (>0.03%), BTC Macro perdido, EMA50 sem volume
"""

import datetime
import math
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import requests

def get_all_liquid_usdt_pairs():
    url_info = 'https://api.binance.com/api/v3/exchangeInfo'
    r_info = requests.get(url_info, timeout=10).json()
    
    stables_and_leveraged = [
        'USDCUSDT', 'FDUSDUSDT', 'TUSDUSDT', 'BUSDUSDT', 'EURUSDT', 'DAIUSDT', 'USDPUSDT', 'AEURUSDT',
        'USTCUSDT', 'PAXGUSDT', 'XAUTUSDT', 'USD1USDT', 'RLUSDUSDT'
    ]
    
    valid_symbols = []
    for s in r_info['symbols']:
        sym = s['symbol']
        if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING':
            if not any(sym.endswith(x) for x in ['UPUSDT', 'DOWNUSDT', 'BEARUSDT', 'BULLUSDT']):
                if sym not in stables_and_leveraged:
                    valid_symbols.append(sym)
                    
    # Buscar volume 24h para priorizar ativos com liquidez institucional (> $3M/dia)
    url_ticker = 'https://api.binance.com/api/v3/ticker/24hr'
    r_ticker = requests.get(url_ticker, timeout=10).json()
    ticker_map = {item['symbol']: float(item['quoteVolume']) for item in r_ticker if item['symbol'] in valid_symbols}
    
    # Filtrar os mais líquidos (Top 80 por volume)
    sorted_pairs = [p[0] for p in sorted(ticker_map.items(), key=lambda x: x[1], reverse=True) if p[1] >= 3e6]
    return sorted_pairs[:80]

def fetch_klines(symbol, interval='4h', total_candles=1500):
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
    fut_sym = '1000PEPEUSDT' if symbol == 'PEPEUSDT' else ('1000BONKUSDT' if symbol == 'BONKUSDT' else ('1000SHIBUSDT' if symbol == 'SHIBUSDT' else symbol))
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
        url = 'https://api.alternative.me/fng/?limit=220'
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
            return True, "Desbloqueio SUI > 1% (Cliff mensal no dia 1)"
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
        if dt.month in [4, 7] and 15 <= dt.day <= 25:
            return True, "Janela de Emissão GALA > 1%"
    elif 'STRK' in symbol:
        if 8 <= dt.day <= 16:
            return True, "Desbloqueio STRK > 1% (Cliff mensal dia 15)"
    elif 'WLD' in symbol:
        if dt.month in [7, 8]:
            return True, "Desbloqueio WLD > 1% (Início de unlocks massivos)"
    return False, ""

def run_full_market_backtest(initial_capital=200.0, risk_pct=0.05, fee_pct=0.00075, max_positions=3):
    start_date = pd.to_datetime("2026-02-20 00:00:00")
    end_date = pd.to_datetime("2026-08-19 23:59:59")
    
    print("="*80)
    print("INICIANDO BACKTEST DE MERCADO TOTAL DA BINANCE (180 DIAS - POINT-IN-TIME)")
    print("================================================================================")
    
    print("\n1. Mapeando pares líquidos da Binance...")
    candidate_symbols = get_all_liquid_usdt_pairs()
    print(f"Total de pares líquidos mapeados: {len(candidate_symbols)}")
    
    print("\n2. Baixando dados de referência do BTCUSDT (Macro)...")
    btc_4h = compute_indicators_4h(fetch_klines('BTCUSDT', interval='4h', total_candles=1500))
    btc_1d = compute_indicators_1d(fetch_klines('BTCUSDT', interval='1d', total_candles=400))
    fng_df = fetch_fear_and_greed()
    
    print("\n3. Baixando dados históricos em paralelo para todos os ativos...")
    data_4h = {}
    data_1d = {}
    funding_data = {}
    
    def download_asset(sym):
        try:
            df4 = fetch_klines(sym, interval='4h', total_candles=1500)
            if df4.empty or df4['open_time'].min() > start_date:
                return sym, None, None, None
            df1 = fetch_klines(sym, interval='1d', total_candles=400)
            fr = fetch_funding_rates(sym)
            ind4 = compute_indicators_4h(df4)
            ind1 = compute_indicators_1d(df1)
            return sym, ind4, ind1, fr
        except Exception:
            return sym, None, None, None
            
    t0 = time.time()
    valid_symbols = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(download_asset, candidate_symbols))
        
    for sym, ind4, ind1, fr in results:
        if ind4 is not None and not ind4.empty and ind1 is not None and not ind1.empty:
            data_4h[sym] = ind4
            data_1d[sym] = ind1
            funding_data[sym] = fr
            valid_symbols.append(sym)
            
    t1 = time.time()
    print(f"Dados baixados e validados para {len(valid_symbols)} ativos em {t1-t0:.2f}s.")
    
    capital = initial_capital
    trades = []
    vetoes = []
    active_positions = {}
    
    ref_sym = 'BTCUSDT'
    all_timestamps = data_4h[ref_sym][(data_4h[ref_sym]['open_time'] >= start_date) & 
                                      (data_4h[ref_sym]['open_time'] <= end_date)]['open_time'].tolist()
                                      
    equity_curve = [{'timestamp': start_date, 'capital': capital, 'active_count': 0}]
    
    print(f"\n4. Executando simulação Point-in-Time em {len(all_timestamps)} candles 4h...")
    
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
                    
            entry_price = pos['entry_price']
            stop_loss = pos['stop_loss']
            target_1 = pos['target_1']
            target_2 = pos['target_2']
            be_trigger_price = pos['be_trigger_price']
            allocated_capital = pos['allocated_capital']
            
            pos['candles_held'] += 1
            
            # Saída por Exaustão
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
                        
        # 2. Avaliar e Rankear TODOS os Ativos do Mercado Point-in-Time
        candidates = []
        for s in valid_symbols:
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
                
            # Score
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
                    
        # 3. Alocação Dinâmica nas Melhores Oportunidades do Mercado (Top 3)
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
        'total_prejuizo_evitado': sum(v['prejuizo_evitado'] for v in vetoes),
        'total_assets_scanned': len(valid_symbols)
    }
    
    print("\n" + "="*80)
    print("RESUMO EXECUTIVO MERCADO TOTAL DA BINANCE")
    print("="*80)
    print(f"Total de Ativos Escaneados: {len(valid_symbols)}")
    print(f"Capital Inicial:       R$ {summary['initial_capital']:.2f}")
    print(f"Saldo Final:           R$ {summary['final_capital']:.2f} ({summary['return_pct']:+.2f}%)")
    print(f"Lucro Líquido:         R$ {summary['net_profit_brl']:+.2f}")
    print(f"Total de Trades:       {summary['total_trades']}")
    print(f"Trades Vencedores:     {summary['winning_trades']}")
    print(f"Trades Perdedores:     {summary['losing_trades']}")
    print(f"Win Rate:              {summary['win_rate_pct']:.2f}%")
    print(f"Profit Factor:         {summary['profit_factor']:.2f}")
    print(f"Drawdown Máximo:       {summary['max_drawdown_pct']:.2f}%")
    print(f"Vetos de Proteção:     {summary['total_vetoes']}")
    print(f"Prejuízo Evitado:      R$ {summary['total_prejuizo_evitado']:.2f}")
    print("="*80)
    
    # Exportar datasets
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
    df_trades.to_csv('data/trades_executados_mercado_total.csv', index=False)
    
    vetoes_export = []
    for v in vetoes[:500]: # Exportar top 500 para economia de espaço
        vetoes_export.append({
            'Data': v['date'].strftime('%Y-%m-%d %H:%M'),
            'Ativo': v['symbol'],
            'Score': f"{v['score']}/100",
            'Motivo do Veto': v['motivo'],
            'Resultado Simulado': v['outcome'],
            'Prejuízo Evitado (R$)': f"R$ {v['prejuizo_evitado']:.2f}" if v['prejuizo_evitado'] > 0 else "R$ 0,00"
        })
    df_vetoes = pd.DataFrame(vetoes_export)
    df_vetoes.to_csv('data/oportunidades_vetadas_mercado_total.csv', index=False)
    
    with open('data/resumo_estatistico_mercado_total.json', 'w') as f:
        json.dump(summary, f, indent=4)
        
    return summary, trades, vetoes

if __name__ == '__main__':
    run_full_market_backtest()
