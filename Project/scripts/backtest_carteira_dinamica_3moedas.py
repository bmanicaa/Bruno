"""
Motor de Simulação de Carteira Dinâmica Quantitativa (3 Ativos Concomitantes / Universo de 20 Moedas)
Conforme especificado em Prompt.md (180 Dias: 20/02/2026 a 19/08/2026)
Universo: SOL, ETH, BNB, NEAR, AVAX, SUI, APT, ARB, OP, RENDER, FET, ONDO, LINK, AAVE, INJ, PENDLE, TIA, PEPE, GALA, TON (+ BTC Macro)
Regras:
- Risco Fixo de 5,0% do capital atual por trade
- Limite Máximo de 3 Posições Abertas Simultaneamente
- Ranking Dinâmico por Score (0-100) Point-in-Time a cada candle 4h
- Gestão de Caixa Dinâmica (USDT) quando houver menos de 3 ativos qualificados
- Taxas Reais da Binance (0,075% maker/taker com BNB) na entrada e na saída
- Puxada de Breakeven Antecipado em +1.0R
- Alvos Adaptativos (1.8R em consolidação / 2.5R em tendência)
- Time-Stop de 14 dias (84 candles 4h)
- Trailing Stop na EMA 20 4h para a 2ª metade
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
            r = requests.get(url, params=params, timeout=10).json()
            if not r or isinstance(r, dict):
                break
            all_data = r + all_data
            end_time = r[0][0] - 1
            if len(r) < limit:
                break
        except Exception as e:
            print(f"Erro ao buscar klines para {symbol}: {e}")
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
        r = requests.get(url, params=params, timeout=10).json()
        df = pd.DataFrame(r)
        if not df.empty and 'fundingTime' in df.columns:
            df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
            df['fundingRate'] = df['fundingRate'].astype(float)
            return df.sort_values('fundingTime').reset_index(drop=True)
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao buscar Funding Rate para {symbol}: {e}")
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
        r = requests.get(url, timeout=10)
        data = r.json().get('data', [])
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
        df['value'] = df['value'].astype(float)
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Erro ao buscar Fear & Greed: {e}")
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

def is_vesting_cliff_universe(symbol, dt):
    """
    Verificação de vesting para o universo de 20 moedas:
    - SUI: Cliff mensal dia 1 (dias 25 a 02)
    - APT: Cliff mensal dia 11/12 (dias 5 a 13)
    - ARB: Cliff mensal dia 16 (dias 9 a 17)
    - OP: Cliff mensal no fim do mês (dias 24 a 31)
    - GALA: Emissões trimestrais (meses 4 e 7, dias 15 a 25)
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
    elif 'GALA' in symbol:
        if dt.month in [4, 7] and 15 <= dt.day <= 25:
            return True, "Janela de Desbloqueio/Emissão GALA > 1%"
    return False, ""

def run_dynamic_portfolio_backtest(symbols, data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, initial_capital=200.0, risk_pct=0.05, fee_pct=0.00075, max_positions=3):
    start_date = pd.to_datetime("2026-02-20 00:00:00")
    end_date = pd.to_datetime("2026-08-19 23:59:59")
    
    capital = initial_capital
    trades = []
    vetoes = []
    active_positions = {}
    
    ref_sym = symbols[0]
    all_timestamps = data_4h[ref_sym][(data_4h[ref_sym]['open_time'] >= start_date) & 
                                      (data_4h[ref_sym]['open_time'] <= end_date)]['open_time'].tolist()
                                      
    equity_curve = [{'timestamp': start_date, 'capital': capital, 'cash': capital, 'active_count': 0}]
    
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
            
            # Custo de Financiamento (Funding Rate) a cada 8h (00:00, 08:00, 16:00 UTC)
            if current_time.hour in [0, 8, 16] and not funding_data[s].empty:
                rem_pct_funding = 0.5 if pos['partial_taken'] else 1.0
                current_notional = (allocated_capital * rem_pct_funding) * (c_close / entry_price)
                funding_fee = current_notional * fr_val
                capital -= funding_fee
                pos['pnl_brl'] -= funding_fee
                pos['funding_paid'] = pos.get('funding_paid', 0.0) + funding_fee
            
            # Abordagem Pessimista: Stop Loss tem prioridade MÁXIMA sobre qualquer saída intra-candle.
            # Se c_low <= stop na mesma vela que RSI > 75, assume-se que o stop foi atingido primeiro.
            if c_low <= pos['stop_loss']:
                stop_slippage = 0.0008  # 8 bps de slippage adverso na ordem Stop-Market em dump rápido
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
            # Saídas de Exaustão e Time-Stop (só avaliadas se o stop NÃO foi atingido)
            elif c_rsi > 75 and fr_val > 0.0004:
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
                # Movimenta Breakeven SE não foi estopado
                if not pos['be_moved'] and c_high >= be_trigger_price:
                    pos['be_moved'] = True
                    pos['stop_loss'] = entry_price
                    
                if not pos['partial_taken']:
                    if c_high >= target_1:
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
            
            sub_4h = df_sym_4h[df_sym_4h['open_time'] < current_time]  # LOOKAHEAD FIX: Must strictly use data before current_time to make decision
            sub_1d = df_sym_1d[df_sym_1d['open_time'] < current_time]  # LOOKAHEAD FIX
            if len(sub_4h) < 50 or len(sub_1d) < 30:
                continue
                
            # Entry candle will be the one opening at current_time
            current_open_candle = df_sym_4h[df_sym_4h['open_time'] == current_time]
            if current_open_candle.empty:
                continue
            entry_candle_open = current_open_candle.iloc[0]['open']

            candle = sub_4h.iloc[-1]  # This is now the PREVIOUS closed candle (current_time - 4h)
            prev_candle = sub_4h.iloc[-2]  # This is now two candles ago
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
                    # Log de Oportunidade Vetada
                    # NOTA: Lookahead INTENCIONAL abaixo — usado apenas para relatório retroativo,
                    #       NÃO influencia decisões de entrada/saída do backtest.
                    idx_matches = df_sym_4h[df_sym_4h['open_time'] == current_time].index
                    if idx_matches.empty:
                        continue
                    idx = idx_matches[0]
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
            # Ordenar por Score decrescente (as melhores primeiro)
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
                    'exit_dates': [], 'exit_prices': [], 'exit_reasons': [], 'pnl_brl': -entry_fee, 'status': 'OPEN',
                    'funding_paid': 0.0
                }
                
        # Curva de Patrimônio Mark-to-Market (Capital Realizado + PnL Não-Realizado a cada 4h)
        unrealized_pnl = 0.0
        for s_act, p_act in active_positions.items():
            df_sym_curr = data_4h[s_act]
            cand_curr = df_sym_curr[df_sym_curr['open_time'] == current_time]
            if not cand_curr.empty:
                c_close_now = cand_curr.iloc[0]['close']
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
    total_funding_fees = sum(t.get('funding_paid', 0.0) for t in trades)
    
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
        'total_funding_fees_brl': total_funding_fees,
        'total_vetoes': len(vetoes),
        'total_prejuizo_evitado': sum(v['prejuizo_evitado'] for v in vetoes)
    }
    
    return summary, trades, vetoes, equity_df

def main():
    print("="*80)
    print("INICIANDO BACKTEST DA CARTEIRA DINÂMICA (MAX 3 ATIVOS / UNIVERSO DE 20 MOEDAS)")
    print("Período: 20 de Fevereiro de 2026 a 19 de Agosto de 2026 (180 Dias)")
    print("Configuração: Risco Fixo 5.0% + Taxas Reais Binance (0.075% BNB)")
    print("="*80)
    
    symbols = [
        'SOLUSDT', 'ETHUSDT', 'BNBUSDT', 'NEARUSDT', 'AVAXUSDT',
        'SUIUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT', 'RENDERUSDT',
        'FETUSDT', 'ONDOUSDT', 'LINKUSDT', 'AAVEUSDT', 'INJUSDT',
        'PENDLEUSDT', 'TIAUSDT', 'PEPEUSDT', 'GALAUSDT', 'TONUSDT'
    ]
    
    print("\n1. Baixando dados de referência do BTCUSDT (Macro)...")
    btc_4h = compute_indicators_4h(fetch_klines_extended('BTCUSDT', interval='4h', total_candles=1600))
    btc_1d = compute_indicators_1d(fetch_klines_extended('BTCUSDT', interval='1d', total_candles=400))
    
    print("2. Baixando Fear & Greed Index...")
    fng_df = fetch_fear_and_greed()
    
    data_4h = {}
    data_1d = {}
    funding_data = {}
    
    for s in symbols:
        print(f"3. Processando indicadores para {s}...")
        df_4h = fetch_klines_extended(s, interval='4h', total_candles=1600)
        df_1d = fetch_klines_extended(s, interval='1d', total_candles=400)
        df_4h = compute_indicators_4h(df_4h)
        df_1d = compute_indicators_1d(df_1d)
        data_4h[s] = df_4h
        data_1d[s] = df_1d
        funding_data[s] = fetch_funding_rates_extended(s)
        
    print("\n" + "="*80)
    print("EXECUTANDO SIMULAÇÃO DE CARTEIRA DINÂMICA (MAX 3 POSIÇÕES)")
    print("="*80)
    
    summary, trades, vetoes, equity_df = run_dynamic_portfolio_backtest(
        symbols, data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df,
        initial_capital=200.0, risk_pct=0.05, fee_pct=0.00075, max_positions=3
    )
    
    print(f"Capital Inicial:       R$ {summary['initial_capital']:.2f}")
    print(f"Saldo Final:           R$ {summary['final_capital']:.2f} ({summary['return_pct']:+.2f}%)")
    print(f"Lucro Líquido:         R$ {summary['net_profit_brl']:+.2f}")
    print(f"Total de Trades:       {summary['total_trades']}")
    print(f"Trades Vencedores:     {summary['winning_trades']}")
    print(f"Trades Perdedores:     {summary['losing_trades']}")
    print(f"Trades no 0x0:         {summary['breakeven_trades']}")
    print(f"Win Rate:              {summary['win_rate_pct']:.2f}%")
    print(f"Profit Factor:         {summary['profit_factor']:.2f}")
    print(f"Drawdown Máximo:       {summary['max_drawdown_pct']:.2f}%")
    print(f"Vetos de Proteção:     {summary['total_vetoes']}")
    print(f"Prejuízo Evitado:      R$ {summary['total_prejuizo_evitado']:.2f}")
    print("="*80)
    
    # Exportação de Dados para data/
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
    df_trades.to_csv('data/trades_executados_carteira_dinamica_3moedas.csv', index=False)
    
    vetoes_export = []
    for v in vetoes:
        vetoes_export.append({
            'Data': v['date'].strftime('%Y-%m-%d %H:%M'),
            'Ativo': v['symbol'],
            'Score': f"{v['score']}/100",
            'Motivo do Veto': v['motivo'],
            'Resultado Simulado': v['outcome'],
            'Prejuízo Evitado (R$)': f"R$ {v['prejuizo_evitado']:.2f}" if v['prejuizo_evitado'] > 0 else "R$ 0,00"
        })
    df_vetoes = pd.DataFrame(vetoes_export)
    df_vetoes.to_csv('data/oportunidades_vetadas_carteira_dinamica_3moedas.csv', index=False)
    
    with open('data/resumo_estatistico_carteira_dinamica_3moedas.json', 'w') as f:
        json.dump(summary, f, indent=4)
        
    print("\nArquivos salvos com sucesso em data/:")
    print("- data/trades_executados_carteira_dinamica_3moedas.csv")
    print("- data/oportunidades_vetadas_carteira_dinamica_3moedas.csv")
    print("- data/resumo_estatistico_carteira_dinamica_3moedas.json")

if __name__ == '__main__':
    main()
