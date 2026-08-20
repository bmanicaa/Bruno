"""
Out-of-Sample Quantitative Validation Engine (180 Days: 2026-02-20 to 2026-08-19)
Assets: NEARUSDT (Major L1), APTUSDT (Move L1 with Vesting), GALAUSDT (Gaming/Metaverse)
Strict Out-of-Sample Test using the EXACT SAME rules from Prompt.md
"""

import datetime
import math
import os
import json
import numpy as np
import pandas as pd
import requests
from backtest_180d import fetch_klines_extended, fetch_funding_rates_extended, fetch_fear_and_greed, compute_indicators_4h, compute_indicators_1d

def is_vesting_cliff_oos(symbol, dt):
    if 'APT' in symbol:
        # Aptos monthly cliff unlock on the 11th-12th of each month (~2.5% circulating)
        # Veto window: 7 days before the 12th (days 5 to 13)
        if 5 <= dt.day <= 13:
            return True, "Desbloqueio de Vesting APT > 1% (Cliff mensal no dia 11/12)"
    elif 'GALA' in symbol:
        # Daily emissions, quarterly cliffs
        if dt.month in [4, 7] and 15 <= dt.day <= 25:
            return True, "Janela de Desbloqueio/Emissão GALA > 1%"
    elif 'NEAR' in symbol:
        # Predictable staking/foundation release
        return False, ""
    return False, ""

def run_oos_backtest():
    print("="*80)
    print("INICIANDO TESTE FORA DA AMOSTRA (OUT-OF-SAMPLE) - 180 DIAS")
    print("Ativos Selecionados: NEAR (L1 Principal), APT (Move L1), GALA (GameFi)")
    print("="*80)
    
    symbols = ['NEARUSDT', 'APTUSDT', 'GALAUSDT']
    data_4h = {}
    data_1d = {}
    funding_data = {}
    
    print("Baixando dados estendidos do BTCUSDT (Macro)...")
    btc_4h = compute_indicators_4h(fetch_klines_extended('BTCUSDT', interval='4h', total_candles=1600))
    btc_1d = compute_indicators_1d(fetch_klines_extended('BTCUSDT', interval='1d', total_candles=400))
    
    fng_df = fetch_fear_and_greed()
    
    for s in symbols:
        print(f"Baixando dados para {s}...")
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
    
    all_timestamps = data_4h['NEARUSDT'][(data_4h['NEARUSDT']['open_time'] >= start_date) & 
                                         (data_4h['NEARUSDT']['open_time'] <= end_date)]['open_time'].tolist()
    
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
                pct_return = (c_close - entry_price) / entry_price
                pnl_brl = allocated_capital * pct_return
                capital += pnl_brl
                pos['exit_dates'].append(current_time)
                pos['exit_prices'].append(c_close)
                pos['exit_reasons'].append("Time-Stop (14 Dias Estagnado sem atingir Alvo 1)")
                pos['pnl_brl'] += pnl_brl
                pos['final_capital'] = capital
                pos['status'] = 'CLOSED'
                trades.append(pos)
                del active_positions[s]
                continue
                
            # Check Breakeven Trigger at +1.0R
            if not pos['be_moved'] and c_high >= be_trigger_price:
                pos['be_moved'] = True
                pos['stop_loss'] = entry_price
                
            if not pos['partial_taken']:
                if c_low <= pos['stop_loss']:
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
            
            if len(active_positions) >= 2:
                veto_reasons.append("Limite de Exposição Global da Carteira atingido (máx 2 posições abertas)")
                
            is_vesting, vest_msg = is_vesting_cliff_oos(s, current_time)
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
            if s == 'NEARUSDT':
                onchain_score += 10
            elif s == 'APTUSDT':
                onchain_score += 8
            elif s == 'GALAUSDT':
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
    print("RESUMO EXECUTIVO OUT-OF-SAMPLE (NEAR, APT, GALA)")
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
    trades_df.to_csv('trades_executados_oos.csv', index=False)
    
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
    vetoes_df.to_csv('oportunidades_vetadas_oos.csv', index=False)
    
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
    
    with open('resumo_estatistico_oos.json', 'w') as f:
        json.dump(summary, f, indent=4)
        
    return summary, trades_df, vetoes_df

if __name__ == '__main__':
    run_oos_backtest()
