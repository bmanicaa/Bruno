"""
Motor de Backtest Quantitativo para as 6 Novas Criptomoedas (180 Dias)
Ativos: ARB, RENDER, ONDO, PEPE, AAVE, TIA (+ BTC para Regime Macro)
Período: 20 de Fevereiro de 2026 a 19 de Agosto de 2026
Regras Estritas de Prompt.md:
- Risco Fixo de 5,0% por trade (alocação baseada na distância do Stop Loss)
- Taxas de Corretagem da Binance (0,075% maker/taker com BNB) na entrada e na saída
- Puxada de Breakeven Antecipado em +1.0R
- Alvos Adaptativos (1.8R em consolidação / 2.5R em tendência)
- Time-Stop de 14 dias (84 candles 4h)
- Saída Trailing na EMA 20 4h para a 2ª metade
- Vetos Obrigatórios: Vesting (>1% em 7d), Funding Rate (>0.03%), BTC Macro perdido, EMA50 sem volume
- Simulação Individual por moeda (R$ 200 inicial cada) e Simulação de Carteira Consolidada (Max 2 posições)
"""

import datetime
import math
import os
import json
import numpy as np
import pandas as pd
import requests

def fetch_klines_extended(symbol, interval='4h', total_candles=1600):
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

def is_vesting_cliff_6_assets(symbol, dt):
    """
    Verificação de vesting para as 6 moedas:
    - ARB: Cliff mensal no dia 16 de cada mês (~92.65M tokens, >1% circulante). Veto nos 7 dias antes até 1 dia após (dias 9 a 17).
    - TIA: Emissão linear padrão; grande cliff anual em 31/10 (fora da janela fev-ago).
    - RENDER: Migração concluída, sem cliff > 1%.
    - ONDO: Sem cliffs mensais > 1% durante fev-ago.
    - PEPE: 100% circulante, 0% vesting.
    - AAVE: 100% circulante, 0% vesting.
    """
    if 'ARB' in symbol:
        if 9 <= dt.day <= 17:
            return True, "Desbloqueio de Vesting ARB > 1% (Cliff mensal no dia 16)"
    return False, ""

def run_single_asset_backtest(symbol, df_4h, df_1d, funding_data, btc_4h, btc_1d, fng_df, risk_pct=0.05, fee_pct=0.00075):
    start_date = pd.to_datetime("2026-02-20 00:00:00")
    end_date = pd.to_datetime("2026-08-19 23:59:59")
    
    initial_capital = 200.0
    capital = initial_capital
    
    trades = []
    vetoes = []
    active_pos = None
    
    sub_df_4h = df_4h[(df_4h['open_time'] >= start_date) & (df_4h['open_time'] <= end_date)]
    if sub_df_4h.empty:
        return None, [], []
        
    all_timestamps = sub_df_4h['open_time'].tolist()
    equity_curve = [{'timestamp': start_date, 'capital': capital}]
    
    p_start = sub_df_4h.iloc[0]['open']
    p_end = sub_df_4h.iloc[-1]['close']
    bnh_return = (p_end - p_start) / p_start * 100
    
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
                
        # 1. Gerenciamento de Posição Ativa
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
                
                # Saída por Exaustão Extrema (RSI > 75 e Funding Rate > 0.04%)
                if c_rsi > 75 and fr_val > 0.0004:
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
                # Time-Stop de 14 Dias (84 candles 4h sem Alvo 1)
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
                    # Ativação do Breakeven em +1.0R
                    if not active_pos['be_moved'] and c_high >= be_trigger_price:
                        active_pos['be_moved'] = True
                        active_pos['stop_loss'] = entry_price
                        
                    if not active_pos['partial_taken']:
                        # Stop Loss Inicial ou Breakeven antes do Alvo 1
                        if c_low <= active_pos['stop_loss']:
                            pct_loss = (active_pos['stop_loss'] - entry_price) / entry_price
                            gross_pnl = allocated_capital * pct_loss
                            exit_fee = (allocated_capital * (1 + pct_loss)) * fee_pct
                            pnl_brl = gross_pnl - exit_fee
                            capital += pnl_brl
                            active_pos['exit_dates'].append(current_time)
                            active_pos['exit_prices'].append(active_pos['stop_loss'])
                            active_pos['exit_reasons'].append("Stop no Breakeven" if active_pos['be_moved'] else "Stop Loss Inicial")
                            active_pos['pnl_brl'] += pnl_brl
                            active_pos['final_capital'] = capital
                            active_pos['status'] = 'CLOSED'
                            trades.append(active_pos)
                            active_pos = None
                        # Atingimento do Alvo 1 (Realização de 50%)
                        elif c_high >= target_1:
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
                            
                            # Se atingiu Alvo 2 no mesmo candle
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
                        # Gestão da 2ª Metade (Stop no 0x0 garantido)
                        if c_low <= active_pos['stop_loss']:
                            exit_fee = (allocated_capital * 0.5) * fee_pct
                            pnl_brl = -exit_fee
                            capital += pnl_brl
                            active_pos['pnl_brl'] += pnl_brl
                            active_pos['exit_dates'].append(current_time)
                            active_pos['exit_prices'].append(active_pos['stop_loss'])
                            active_pos['exit_reasons'].append("Stop Breakeven (0x0 na 2ª metade)")
                            active_pos['final_capital'] = capital
                            active_pos['status'] = 'CLOSED'
                            trades.append(active_pos)
                            active_pos = None
                        elif c_high >= target_2:
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
                            
        # 2. Avaliação de Sinais e Pontuação (Score 0-100)
        if active_pos is None:
            sub_4h = df_4h[df_4h['open_time'] <= current_time]
            sub_1d = df_1d[df_1d['open_time'] <= current_time]
            if len(sub_4h) >= 50 and len(sub_1d) >= 30:
                candle = sub_4h.iloc[-1]
                prev_candle = sub_4h.iloc[-2]
                candle_1d = sub_1d.iloc[-1]
                
                veto_reasons = []
                is_vest, vest_msg = is_vesting_cliff_6_assets(symbol, current_time)
                if is_vest:
                    veto_reasons.append(f"Vesting ({vest_msg})")
                    
                fr_val = 0.0001
                if not funding_data.empty:
                    fr_sub = funding_data[funding_data['fundingTime'] <= current_time]
                    if not fr_sub.empty:
                        fr_val = fr_sub.iloc[-1]['fundingRate']
                if fr_val > 0.0003:
                    veto_reasons.append(f"Funding Rate Alto ({fr_val*100:.4f}% > 0.03%)")
                if btc_macro_support_lost:
                    veto_reasons.append("Suporte Macro do BTC Perdido (< EMA50 1D -3%)")
                if candle['close'] < candle['ema50'] and candle['vol_ratio'] < 1.3:
                    veto_reasons.append("Preço < EMA50 4h sem Volume Agressor (Ratio < 1.3)")
                
                # Cálculo de Score Multidimensional
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
                
                if (trend_trigger or reversal_trigger) and total_score >= 75 and len(veto_reasons) == 0:
                    risk_brl = capital * risk_pct  # 5.0% de risco fixo
                    allocated_capital = min(risk_brl / stop_dist_pct, capital * 2.5)  # Máximo 2.5x alavancagem
                    entry_fee = allocated_capital * fee_pct
                    capital -= entry_fee  # Desconto de taxa de entrada
                    
                    active_pos = {
                        'symbol': symbol, 'entry_date': current_time, 'entry_price': entry_price,
                        'stop_loss': stop_loss, 'stop_dist': stop_dist, 'stop_dist_pct': stop_dist_pct,
                        'be_trigger_price': be_trigger_price, 'be_moved': False,
                        'target_1': target_1, 'target_2': target_2, 'rr_target1': rr_target1, 'regime': regime_str,
                        'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                        'score': total_score, 'candles_held': 0, 'partial_taken': False,
                        'exit_dates': [], 'exit_prices': [], 'exit_reasons': [], 'pnl_brl': -entry_fee, 'status': 'OPEN'
                    }
                elif (trend_trigger or reversal_trigger):
                    # Registro de Oportunidade Vetada
                    idx = df_4h[df_4h['open_time'] == current_time].index[0]
                    sub_future = df_4h.iloc[idx+1:idx+15]
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
                        'symbol': symbol.replace('USDT', ''),
                        'score': total_score,
                        'motivo': " | ".join(veto_reasons) if veto_reasons else f"Score insuficiente ({total_score}/100 < 75)",
                        'outcome': outcome,
                        'prejuizo_evitado': simulated_loss
                    })
                    
        equity_curve.append({'timestamp': current_time, 'capital': capital})
        
    # Fechamento Mark-to-Market no fim do período caso posição ainda aberta
    if active_pos is not None:
        last_candle = df_4h[df_4h['open_time'] <= end_date].iloc[-1]
        c_close = last_candle['close']
        remaining_pct = 0.5 if active_pos['partial_taken'] else 1.0
        pct_return = (c_close - active_pos['entry_price']) / active_pos['entry_price']
        gross_pnl = (active_pos['allocated_capital'] * remaining_pct) * pct_return
        exit_fee = (active_pos['allocated_capital'] * remaining_pct * (1 + pct_return)) * fee_pct
        pnl_brl = gross_pnl - exit_fee
        capital += pnl_brl
        active_pos['exit_dates'].append(last_candle['open_time'])
        active_pos['exit_prices'].append(c_close)
        active_pos['exit_reasons'].append("Fechamento Fim do Período (MtM)")
        active_pos['pnl_brl'] += pnl_brl
        active_pos['final_capital'] = capital
        active_pos['status'] = 'CLOSED'
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
    
    res = {
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
    
    return res, trades, vetoes

def run_portfolio_backtest(symbols, data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, risk_pct=0.05, fee_pct=0.00075):
    """
    Simulação de Portfólio Consolidado com R$ 200,00 Inicial e Máximo de 2 Posições Concomitantes
    """
    start_date = pd.to_datetime("2026-02-20 00:00:00")
    end_date = pd.to_datetime("2026-08-19 23:59:59")
    
    initial_capital = 200.0
    capital = initial_capital
    
    trades = []
    vetoes = []
    active_positions = {}
    
    ref_sym = symbols[0]
    all_timestamps = data_4h[ref_sym][(data_4h[ref_sym]['open_time'] >= start_date) & 
                                      (data_4h[ref_sym]['open_time'] <= end_date)]['open_time'].tolist()
                                      
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
            stop_loss = pos['stop_loss']
            target_1 = pos['target_1']
            target_2 = pos['target_2']
            be_trigger_price = pos['be_trigger_price']
            allocated_capital = pos['allocated_capital']
            
            pos['candles_held'] += 1
            
            # Exaustão
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
                        
        # 2. Avaliar Novos Sinais
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
            is_vest, vest_msg = is_vesting_cliff_6_assets(s, current_time)
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
            if len(active_positions) >= 2:
                veto_reasons.append("Limite de Exposição Global (Máx 2 Posições Concomitantes)")
                
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
            
            if (trend_trigger or reversal_trigger) and total_score >= 75 and len(veto_reasons) == 0:
                risk_brl = capital * risk_pct
                allocated_capital = min(risk_brl / stop_dist_pct, capital * 2.5)
                entry_fee = allocated_capital * fee_pct
                capital -= entry_fee
                
                active_positions[s] = {
                    'symbol': s, 'entry_date': current_time, 'entry_price': entry_price,
                    'stop_loss': stop_loss, 'stop_dist': stop_dist, 'stop_dist_pct': stop_dist_pct,
                    'be_trigger_price': be_trigger_price, 'be_moved': False,
                    'target_1': target_1, 'target_2': target_2, 'rr_target1': rr_target1, 'regime': regime_str,
                    'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                    'score': total_score, 'candles_held': 0, 'partial_taken': False,
                    'exit_dates': [], 'exit_prices': [], 'exit_reasons': [], 'pnl_brl': -entry_fee, 'status': 'OPEN'
                }
            elif (trend_trigger or reversal_trigger):
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
                
        equity_curve.append({'timestamp': current_time, 'capital': capital})
        
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
        'total_prejuizo_evitado': sum(v['prejuizo_evitado'] for v in vetoes)
    }
    
    return summary, trades, vetoes

def main():
    print("="*80)
    print("INICIANDO BACKTEST DAS 6 NOVAS MOEDAS (180 DIAS - 20/02/2026 A 19/08/2026)")
    print("Moedas: ARB, RENDER, ONDO, PEPE, AAVE, TIA")
    print("Configuração: Risco Fixo 5.0% + Taxas Reais Binance (0.075%)")
    print("="*80)
    
    symbols = ['ARBUSDT', 'RENDERUSDT', 'ONDOUSDT', 'PEPEUSDT', 'AAVEUSDT', 'TIAUSDT']
    
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
        
    # --- PARTE A: BACKTEST INDIVIDUAL POR MOEDA ---
    print("\n" + "="*80)
    print("EXECUTANDO BACKTEST INDIVIDUAL POR MOEDA (R$ 200,00 CADA)")
    print("="*80)
    
    individual_results = []
    all_individual_trades = []
    all_individual_vetoes = []
    
    for s in symbols:
        res, trades, vetoes = run_single_asset_backtest(s, data_4h[s], data_1d[s], funding_data[s], btc_4h, btc_1d, fng_df, risk_pct=0.05, fee_pct=0.00075)
        individual_results.append(res)
        all_individual_trades.extend(trades)
        all_individual_vetoes.extend(vetoes)
        
    df_res = pd.DataFrame(individual_results)
    df_res.to_csv('data/resultado_6_novas_moedas_risco_5pct_com_taxas.csv', index=False)
    print("\nRESULTADOS INDIVIDUAIS POR MOEDA:")
    print(df_res.to_string(index=False))
    
    # --- PARTE B: BACKTEST DE PORTFÓLIO CONSOLIDADO ---
    print("\n" + "="*80)
    print("EXECUTANDO BACKTEST DE PORTFÓLIO CONSOLIDADO (MAX 2 POSIÇÕES SIMULTÂNEAS)")
    print("="*80)
    
    port_summary, port_trades, port_vetoes = run_portfolio_backtest(symbols, data_4h, data_1d, funding_data, btc_4h, btc_1d, fng_df, risk_pct=0.05, fee_pct=0.00075)
    
    print(f"Capital Inicial:       R$ {port_summary['initial_capital']:.2f}")
    print(f"Saldo Final:           R$ {port_summary['final_capital']:.2f} ({port_summary['return_pct']:+.2f}%)")
    print(f"Lucro Líquido:         R$ {port_summary['net_profit_brl']:+.2f}")
    print(f"Total de Trades:       {port_summary['total_trades']}")
    print(f"Trades Vencedores:     {port_summary['winning_trades']}")
    print(f"Trades Perdedores:     {port_summary['losing_trades']}")
    print(f"Trades no 0x0:         {port_summary['breakeven_trades']}")
    print(f"Win Rate:              {port_summary['win_rate_pct']:.2f}%")
    print(f"Profit Factor:         {port_summary['profit_factor']:.2f}")
    print(f"Drawdown Máximo:       {port_summary['max_drawdown_pct']:.2f}%")
    print(f"Vetos de Proteção:     {port_summary['total_vetoes']}")
    print(f"Prejuízo Evitado:      R$ {port_summary['total_prejuizo_evitado']:.2f}")
    print("="*80)
    
    # Exportação de Dados para data/
    trades_export = []
    for t in port_trades:
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
    df_port_trades = pd.DataFrame(trades_export)
    df_port_trades.to_csv('data/trades_executados_6_novas_moedas.csv', index=False)
    
    vetoes_export = []
    for v in port_vetoes:
        vetoes_export.append({
            'Data': v['date'].strftime('%Y-%m-%d %H:%M'),
            'Ativo': v['symbol'],
            'Score': f"{v['score']}/100",
            'Motivo do Veto': v['motivo'],
            'Resultado Simulado': v['outcome'],
            'Prejuízo Evitado (R$)': f"R$ {v['prejuizo_evitado']:.2f}" if v['prejuizo_evitado'] > 0 else "R$ 0,00"
        })
    df_port_vetoes = pd.DataFrame(vetoes_export)
    df_port_vetoes.to_csv('data/oportunidades_vetadas_6_novas_moedas.csv', index=False)
    
    with open('data/resumo_estatistico_6_novas_moedas.json', 'w') as f:
        json.dump(port_summary, f, indent=4)
        
    print("\nArquivos salvos com sucesso em data/:")
    print("- data/resultado_6_novas_moedas_risco_5pct_com_taxas.csv")
    print("- data/trades_executados_6_novas_moedas.csv")
    print("- data/oportunidades_vetadas_6_novas_moedas.csv")
    print("- data/resumo_estatistico_6_novas_moedas.json")

if __name__ == '__main__':
    main()
