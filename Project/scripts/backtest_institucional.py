"""
MOTOR INSTITUCIONAL CANÔNICO — Prompt Mestre V2.2 (Binance Total + Delistados)

Este é o ÚNICO motor oficial de simulação do sistema. Qualquer divergência entre
este arquivo e o Prompt.md deve ser tratada como bug (corrigir o código ou o prompt).

Estratégia base (100% alinhada ao Prompt.md V2.2 — validada por walk-forward OOS):
1. Screener Point-in-Time no mercado total da Binance (Volume 30d > $25M, Maturidade 180d).
   Vetos: Vesting > 1% em 7d | Funding > 0.03% (LONG) | Funding < -0.03% (SHORT).
2. Filtro Macro (1D): BULL (BTC >= EMA50/EMA200) / BEAR (BTC < EMA50/EMA200, Short BTC-ETH) / TRANSIÇÃO (caixa).
3. Seleção de Líderes: Top 10% de Força Relativa (Alpha 7d vs BTC) + estrutura diária.
4. Gatilho LONG: confirmação no 1D (close > dia anterior + pullback na EMA20 1D + RSI 44-62 + CVD 4h > 0).
   Gatilho SHORT: rompimento de fundo diário (close 1D < mínima do dia anterior + RSI 30-56 + CVD < 0).
5. Stop Estrutural: mín/máx 10 candles 4h ± 1.5xATR14 (3,5%-8%).
6. Risco 1,50% | até 4 posições | Circuit Breaker 3/5 | Cooldown 2,5d.
7. +2.0R -> Breakeven + Parcial 50%. Runner (50%) SEM TETO na EMA20 1D. Time-Stop 21d.
8. Custos reais: 0,075% + slippage 5bps/8bps + Funding 8h. Cash Yield 6% a.a.

INSTRUMENTAÇÃO (Fase 1): MAE/MFE em R, regime de entrada, classe de ativo, motivos de saída,
expectância por trade — relatórios segmentados por regime/classe/saída.

WALK-FORWARD (Fase 2): `--walkforward` avalia qualquer config em janelas deslizantes:
  IS    2019-09 -> 2022-09 (calibração, NÃO decide)
  OOS1  2022-09 -> 2023-09 | OOS2 2023-09 -> 2024-09
  OOS3  2024-09 -> 2025-09 | OOS4 2025-09 -> 2026-02
  HOLDOUT 2026-02 -> 2026-08 (testado apenas pela config vencedora)
A decisão usa APENAS os 4 blocos OOS (agregado + mediana). Cada experimento gera:
  data/experimentos/exp_{hash8}.json + entrada automática no analises.md

EXPERIMENTOS (1 parâmetro por vez):
  --btc-adx-min N   : exige ADX 1D do BTC >= N p/ LONGS (0 = off)         [e1]
  --entry-tf 4h|1d  : gatilho no 4h ou confirmado no 1D                    [e2]
  --runner-mode ema20_1d|prev_low_1d|atr_chandelier                        [e3]
  --short-mode revert|breakout                                             [e4]
  --universe alpha|top20                                                   [e5]
  --fee 0.00075|0.0002                                                     [e6]

Execução:
  python scripts/backtest_institucional.py --mode full
  python scripts/backtest_institucional.py --walkforward                  # baseline V2.1
  python scripts/backtest_institucional.py --walkforward --btc-adx-min 20 # experimento e1
"""

import argparse
import datetime
import hashlib
import json
import math
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
EXP_DIR = os.path.join(DATA_DIR, 'experimentos')
ANALISES_PATH = os.path.join(BASE_DIR, 'analises.md')

for d in [REPORTS_DIR, DATA_DIR, EXP_DIR]:
    os.makedirs(d, exist_ok=True)

ENGINE_VERSION = 'V2.3.1'
FEE_PCT = 0.00075
ENTRY_SLIPPAGE = 0.0005
STOP_SLIPPAGE = 0.0008
CASH_YIELD_ANNUAL = 0.06
MATURITY_CANDLES = 1080
MIN_DAILY_VOLUME = 25_000_000
TIME_STOP_CANDLES = 126
BREAKEVEN_R = 2.0
PARTIAL_R = 2.0
PARTIAL_PCT = 0.50
FUNDING_VETO = 0.0003
RSI_LONG_MIN = 44
RSI_LONG_MAX = 62
RSI_SHORT_MIN = 38
RSI_SHORT_MAX = 56

WALKFORWARD_WINDOWS = [
    ('IS',      '2019-09-01', '2022-09-01'),
    ('OOS1',    '2022-09-01', '2023-09-01'),
    ('OOS2',    '2023-09-01', '2024-09-01'),
    ('OOS3',    '2024-09-01', '2025-09-01'),
    ('OOS4',    '2025-09-01', '2026-02-01'),
]
HOLDOUT = ('2026-02-01', '2026-08-20')


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

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi14_1d'] = 100 - (100 / (1 + rs))

    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr14_1d'] = tr.rolling(window=14).mean()

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


def load_all_data():
    btc_4h_path = os.path.join(MACRO_DIR, 'BTCUSDT_4h.csv')
    btc_1d_path = os.path.join(MACRO_DIR, 'BTCUSDT_1d.csv')
    btc_fr_path = os.path.join(MACRO_DIR, 'BTCUSDT_funding_rates.csv')
    fng_path = os.path.join(MACRO_DIR, 'fear_and_greed.csv')

    btc_4h = pd.read_csv(btc_4h_path)
    btc_4h['open_time'] = pd.to_datetime(btc_4h['open_time_dt'] if 'open_time_dt' in btc_4h.columns else btc_4h['open_time']).astype('datetime64[ns]')
    btc_4h = compute_indicators_4h(btc_4h)
    btc_4h.sort_values('open_time', inplace=True)

    btc_1d = pd.read_csv(btc_1d_path)
    btc_1d['open_time'] = pd.to_datetime(btc_1d['open_time_dt'] if 'open_time_dt' in btc_1d.columns else btc_1d['open_time']).astype('datetime64[ns]')
    btc_1d = compute_indicators_1d(btc_1d)
    btc_1d.sort_values('open_time', inplace=True)

    btc_1d_sub = btc_1d[['open_time', 'close', 'high', 'low', 'ema20_1d', 'ema50_1d', 'ema200_1d', 'rsi14_1d', 'atr14_1d', 'adx14_1d']].copy()
    btc_1d_sub.columns = ['open_time_1d', 'close_1d', 'high_1d', 'low_1d', 'ema20_1d', 'ema50_1d', 'ema200_1d', 'rsi14_1d', 'atr14_1d', 'adx14_1d']
    btc_1d_prev = btc_1d_sub[['open_time_1d', 'close_1d', 'high_1d', 'low_1d']].copy()
    btc_1d_prev.columns = ['open_time_1d_prev', 'close_1d_prev', 'high_1d_prev', 'low_1d_prev']
    btc_1d_prev['open_time_1d_prev'] = btc_1d_prev['open_time_1d_prev'] + pd.Timedelta(days=2)
    btc_1d_sub['open_time_1d'] = btc_1d_sub['open_time_1d'] + pd.Timedelta(days=1)
    btc_4h_merged = pd.merge_asof(
        btc_4h, btc_1d_sub,
        left_on='open_time', right_on='open_time_1d',
        direction='backward'
    )
    btc_4h_merged = pd.merge_asof(
        btc_4h_merged, btc_1d_prev,
        left_on='open_time', right_on='open_time_1d_prev',
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

    # Funding do BTC vem do arquivo macro (BTCUSDT não tem pasta em coins/)
    if os.path.exists(btc_fr_path):
        btc_fr = pd.read_csv(btc_fr_path)
        btc_fr['fundingTime'] = pd.to_datetime(btc_fr['fundingTime_dt'] if 'fundingTime_dt' in btc_fr.columns else btc_fr['fundingTime']).astype('datetime64[ns]')
        btc_fr.sort_values('fundingTime', inplace=True)
        funding_map['BTCUSDT'] = btc_fr

    print(f"Carregando e indexando {len(available_symbols)} moedas do mercado total da Binance...")

    df1_cols = ['open_time', 'close', 'high', 'low', 'ema20_1d', 'ema50_1d', 'ema200_1d', 'rsi14_1d', 'atr14_1d']

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
                    df1_sub = df1[df1_cols].copy()
                    df1_sub.columns = ['open_time_1d', 'close_1d', 'high_1d', 'low_1d', 'ema20_1d', 'ema50_1d', 'ema200_1d', 'rsi14_1d', 'atr14_1d']

                    # Dia anterior ao dia completado (shift 2) para gatilhos de rompimento/breakout
                    df1_prev = df1_sub[['open_time_1d', 'close_1d', 'high_1d', 'low_1d']].copy()
                    df1_prev.columns = ['open_time_1d_prev', 'close_1d_prev', 'high_1d_prev', 'low_1d_prev']
                    df1_prev['open_time_1d_prev'] = df1_prev['open_time_1d_prev'] + pd.Timedelta(days=2)

                    # ZERO LOOKAHEAD: valores diarios deslocados +1d -> apenas o dia COMPLETO anterior
                    df1_sub['open_time_1d'] = df1_sub['open_time_1d'] + pd.Timedelta(days=1)

                    df4 = pd.merge_asof(
                        df4, df1_sub,
                        left_on='open_time', right_on='open_time_1d',
                        direction='backward'
                    )
                    df4 = pd.merge_asof(
                        df4, df1_prev,
                        left_on='open_time', right_on='open_time_1d_prev',
                        direction='backward'
                    )

                    df4.set_index('open_time', inplace=True)
                    coins_4h_map[s] = df4

        if os.path.exists(fr_p):
            fr_df = pd.read_csv(fr_p)
            if not fr_df.empty:
                fr_df['fundingTime'] = pd.to_datetime(fr_df['fundingTime_dt'] if 'fundingTime_dt' in fr_df.columns else fr_df['fundingTime']).astype('datetime64[ns]')
                fr_df.sort_values('fundingTime', inplace=True)
                funding_map[s] = fr_df

    return btc_4h, btc_1d, fng_df, coins_4h_map, funding_map, available_symbols


def _last_funding_before(funding_map, s, current_time, default=0.0001):
    if s not in funding_map or funding_map[s].empty:
        return default
    fr_sub = funding_map[s][funding_map[s]['fundingTime'] <= current_time]
    if fr_sub.empty:
        return default
    return float(fr_sub.iloc[-1]['fundingRate'])


def _asset_class(symbol):
    if symbol == 'BTCUSDT':
        return 'BTC'
    if symbol == 'ETHUSDT':
        return 'ETH'
    return 'ALT'


def funding_charge(is_long, allocated_capital, remaining_pct, entry_price, c_close, fr_val):
    if is_long:
        notional = (allocated_capital * remaining_pct) * (c_close / entry_price)
        return notional * fr_val
    notional = (allocated_capital * remaining_pct) * (c_close / entry_price)
    return -notional * fr_val


def run_portfolio_backtest(start_date_str, end_date_str, initial_capital=100000.0, params=None, preloaded=None):
    if params is None:
        params = {}
    p = {
        'risk_pct': 0.015,
        'max_positions': 4,
        'fee_pct': FEE_PCT,
        'entry_slippage': ENTRY_SLIPPAGE,
        'stop_slippage': STOP_SLIPPAGE,
        'annual_cash_yield': CASH_YIELD_ANNUAL,
        'btc_adx_min': params.get('btc_adx_min', 0.0),
        'entry_tf': params.get('entry_tf', '1d'),
        'long_mode': params.get('long_mode', 'pullback'),
        'runner_mode': params.get('runner_mode', 'ema20_1d'),
        'short_mode': params.get('short_mode', 'breakout'),
        'universe': params.get('universe', 'alpha'),
    }
    p.update({k: v for k, v in params.items() if k in p})

    start_date = pd.to_datetime(start_date_str)
    end_date = pd.to_datetime(end_date_str)

    if preloaded is None:
        preloaded = load_all_data()
    btc_4h, btc_1d, fng_df, coins_4h_map, funding_map, available_symbols = preloaded

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
        close_1d = float(last_1d['close'])
        ema50_1d = float(last_1d['ema50_1d'])
        ema200_1d = float(last_1d['ema200_1d'])
        adx_1d = float(last_1d['adx14_1d']) if pd.notna(last_1d['adx14_1d']) else 0.0

        is_strong_bull = (close_1d >= ema50_1d) and (close_1d >= ema200_1d)
        is_bear = (close_1d < ema50_1d) and (close_1d < ema200_1d)
        is_transition = not is_strong_bull and not is_bear

        btc_macro_map[ts] = {
            'bull': is_strong_bull,
            'bear': is_bear,
            'transition': is_transition,
            'adx_1d': adx_1d
        }

        # ZERO LOOKAHEAD: retorno 7d da vela ANTERIOR à vela corrente
        pos_idx = btc_4h_sorted.index.get_loc(ts)
        if pos_idx >= 1:
            prev_4h = btc_4h_sorted.iloc[pos_idx - 1]
            btc_return_7d_map[ts] = prev_4h['return_7d'] if pd.notna(prev_4h['return_7d']) else 0.0
        else:
            btc_return_7d_map[ts] = 0.0

    capital = initial_capital
    active_positions = {}
    trades = []
    equity_curve = [{'timestamp': start_date, 'capital': capital, 'active_count': 0}]
    total_cash_yield_earned = 0.0
    cash_yield_per_4h = p['annual_cash_yield'] / 2190.0

    semesters = []
    cursor = start_date
    while cursor < end_date:
        semesters.append(cursor)
        cursor += pd.DateOffset(months=6)
    semesters.append(end_date)
    semester_checkpoints = {}

    print("Pre-indexando candidatos qualificados no mercado total (Dual-Timeframe + Alpha vs BTC)...")
    candidates_by_time = {ts: [] for ts in all_timestamps}

    for s in available_symbols:
        if p['universe'] == 'btceth' and s not in ('BTCUSDT', 'ETHUSDT'):
            continue
        df4 = coins_4h_map.get(s)
        if df4 is None or len(df4) < MATURITY_CANDLES:
            continue

        idx_times = df4.index
        valid_mask = (idx_times >= start_date) & (idx_times <= end_date)
        valid_indices = np.where(valid_mask)[0]

        for loc_idx in valid_indices:
            if loc_idx < MATURITY_CANDLES:
                continue
            current_time = idx_times[loc_idx]

            prev_candle = df4.iloc[loc_idx - 1]
            candle_2ago = df4.iloc[loc_idx - 2]
            candle_3ago = df4.iloc[loc_idx - 3]

            # 1. Volume Médio Diário 30d > $25M
            if prev_candle['daily_avg_vol_30d'] < MIN_DAILY_VOLUME:
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

            # 4. FILTRO DE REGIME MACRO: ADX 1D do BTC (e1)
            if p['btc_adx_min'] > 0:
                adx_btc = btc_macro_map.get(current_time, {}).get('adx_1d', 0.0)
                if adx_btc < p['btc_adx_min']:
                    continue

            # 5. GATILHO DE ENTRADA (4h ou 1D conforme experimento)
            if p['entry_tf'] == '1d':
                if p['long_mode'] == 'breakout':
                    tested_support = prev_candle['high_1d'] > prev_candle['high_1d_prev']
                    rsi_ok = (55 <= prev_candle['rsi14_1d'] <= 72)
                    close_break = prev_candle['close_1d'] > prev_candle['ema20_1d']
                    rejection_turn = True
                    cvd_ok = prev_candle['cvd'] > 0
                    vol_active = True
                else:
                    tested_support = prev_candle['low_1d'] <= (prev_candle['ema20_1d'] * 1.02)
                    rsi_ok = (RSI_LONG_MIN <= prev_candle['rsi14_1d'] <= RSI_LONG_MAX)
                    close_break = prev_candle['close_1d'] > prev_candle['close_1d_prev']
                    rejection_turn = (prev_candle['close_1d'] > prev_candle['open_1d'] if pd.notna(prev_candle.get('open_1d', np.nan)) else True) and (prev_candle['close_1d'] >= prev_candle['ema20_1d'])
                    cvd_ok = prev_candle['cvd'] > 0
                    vol_active = True
            else:
                # 4. ESTRUTURA 4H: EMA20 > EMA50 > EMA200 e ADX >= 22
                if not (prev_candle['ema20'] > prev_candle['ema50'] > prev_candle['ema200']):
                    continue
                if prev_candle['adx14'] < 22:
                    continue
                tested_support = min(prev_candle['low'], candle_2ago['low'], candle_3ago['low']) <= (prev_candle['ema20'] * 1.02)
                rsi_ok = (RSI_LONG_MIN <= prev_candle['rsi14'] <= RSI_LONG_MAX)
                close_break = prev_candle['close'] > candle_2ago['high']
                rejection_turn = (prev_candle['close'] > prev_candle['open']) and (prev_candle['close'] >= prev_candle['ema20'])
                cvd_ok = prev_candle['cvd'] > 0
                vol_active = prev_candle['vol_ratio'] >= 0.9

            if not (tested_support and rsi_ok and close_break and rejection_turn and cvd_ok and vol_active):
                continue

            # 6. VETOS OBRIGATÓRIOS: Vesting e Funding > 0.03%
            is_vest, _ = is_vesting_cliff(s, current_time)
            if is_vest:
                continue
            fr_entry = _last_funding_before(funding_map, s, current_time)
            if fr_entry > FUNDING_VETO:
                continue

            current_open_candle = df4.iloc[loc_idx]
            entry_price = current_open_candle['open'] * (1 + p['entry_slippage'])

            recent_10_lows = df4.iloc[max(0, loc_idx - 10):loc_idx]['low'].min()
            raw_stop = recent_10_lows - (1.5 * prev_candle['atr14'])
            raw_dist_pct = (entry_price - raw_stop) / entry_price
            stop_dist_pct = min(max(raw_dist_pct, 0.035 if s == 'BTCUSDT' else 0.040), 0.080)
            stop_loss = entry_price * (1 - stop_dist_pct)
            stop_dist = entry_price - stop_loss

            breakeven_trigger = entry_price + (BREAKEVEN_R * stop_dist)
            target_partial = entry_price + (PARTIAL_R * stop_dist)

            btc_bonus = 15 if s == 'BTCUSDT' else 0
            score = 100 + (coin_ret7d - btc_ret7d) * 100 + (prev_candle['adx14'] - 20) + btc_bonus

            btc_macro_now = btc_macro_map.get(current_time)
            btc_adx_1d = btc_macro_now.get('adx_1d', 0.0) if isinstance(btc_macro_now, dict) else 0.0

            candidates_by_time[current_time].append({
                'symbol': s,
                'score': score,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'stop_dist': stop_dist,
                'stop_dist_pct': stop_dist_pct,
                'breakeven_trigger': breakeven_trigger,
                'target_partial': target_partial,
                'alpha_7d': coin_ret7d - btc_ret7d,
                'daily_avg_vol_30d': float(prev_candle['daily_avg_vol_30d']),
                'regime': "Trend Following (BE/Par. 2.0R / Runner 50%)",
                'adx_val': prev_candle['adx14'],
                'direction': 'LONG',
                'rsi_1d': float(prev_candle['rsi14_1d']) if pd.notna(prev_candle['rsi14_1d']) else 0.0,
                'atr_1d_pct': float(prev_candle['atr14_1d'] / (prev_candle['close_1d'] + 1e-9)) if pd.notna(prev_candle.get('atr14_1d', np.nan)) else 0.0,
                'btc_adx_1d': btc_adx_1d,
            })

    # Seleção de Líderes por timestamp: Top 10% Alpha (padrão) ou Top 20 Liquidez (e5)
    for ts in candidates_by_time:
        cands = candidates_by_time[ts]
        if not cands:
            continue
        if p['universe'] == 'top20':
            cands_sorted = sorted(cands, key=lambda c: c['daily_avg_vol_30d'], reverse=True)
            candidates_by_time[ts] = cands_sorted[:20]
        else:
            alphas = np.array([c['alpha_7d'] for c in cands])
            if len(alphas) >= 10:
                threshold = np.quantile(alphas, 0.90)
                candidates_by_time[ts] = [c for c in cands if c['alpha_7d'] >= threshold]
            else:
                candidates_by_time[ts] = cands

    # ================================================================
    # SCREENER SHORT — Apenas BTC e ETH em Regime Bear
    # ================================================================
    short_symbols = ['BTCUSDT', 'ETHUSDT']
    short_candidates_by_time = {ts: [] for ts in all_timestamps}

    if p['short_mode'] == 'none':
        short_symbols = []

    for s in short_symbols:
        df4 = coins_4h_map.get(s)
        if df4 is None or len(df4) < MATURITY_CANDLES:
            continue

        idx_times = df4.index
        valid_mask = (idx_times >= start_date) & (idx_times <= end_date)
        valid_indices = np.where(valid_mask)[0]

        for loc_idx in valid_indices:
            if loc_idx < MATURITY_CANDLES:
                continue
            current_time = idx_times[loc_idx]

            regime = btc_macro_map.get(current_time, {'bear': False})
            if not regime.get('bear', False):
                continue

            prev_candle = df4.iloc[loc_idx - 1]
            candle_2ago = df4.iloc[loc_idx - 2]
            candle_3ago = df4.iloc[loc_idx - 3]

            if prev_candle['daily_avg_vol_30d'] < MIN_DAILY_VOLUME:
                continue

            if pd.isna(prev_candle.get('close_1d')) or pd.isna(prev_candle.get('ema20_1d')):
                continue
            if not (prev_candle['close_1d'] < prev_candle['ema20_1d'] < prev_candle['ema50_1d']):
                continue

            if not (prev_candle['ema20'] < prev_candle['ema50']):
                continue

            if p['short_mode'] == 'breakout':
                # e4: rompimento de fundo diário (trend-following short)
                tested_resistance = True
                close_break_down = prev_candle['close_1d'] < prev_candle['low_1d_prev'] if pd.notna(prev_candle.get('low_1d_prev', np.nan)) else False
                bearish_candle = prev_candle['close_1d'] < prev_candle['ema20_1d']
                rsi_rejection = (30 <= prev_candle['rsi14'] <= RSI_SHORT_MAX)
                cvd_negative = prev_candle['cvd'] < 0
            else:
                tested_resistance = max(prev_candle['high'], candle_2ago['high'], candle_3ago['high']) >= (prev_candle['ema20'] * 0.98)
                rsi_rejection = (RSI_SHORT_MIN <= prev_candle['rsi14'] <= RSI_SHORT_MAX)
                close_break_down = prev_candle['close'] < candle_2ago['low']
                bearish_candle = (prev_candle['close'] < prev_candle['open']) and (prev_candle['close'] <= prev_candle['ema20'])
                cvd_negative = prev_candle['cvd'] < 0

            if not (tested_resistance and rsi_rejection and close_break_down and bearish_candle and cvd_negative):
                continue

            fr_entry = _last_funding_before(funding_map, s, current_time)
            if fr_entry < -FUNDING_VETO:
                continue

            current_open_candle = df4.iloc[loc_idx]
            entry_price = current_open_candle['open'] * (1 - p['entry_slippage'])

            recent_10_highs = df4.iloc[max(0, loc_idx - 10):loc_idx]['high'].max()
            raw_stop = recent_10_highs + (1.5 * prev_candle['atr14'])
            raw_dist_pct = (raw_stop - entry_price) / entry_price
            stop_dist_pct = min(max(raw_dist_pct, 0.035), 0.080)
            stop_loss = entry_price * (1 + stop_dist_pct)
            stop_dist = stop_loss - entry_price

            breakeven_trigger = entry_price - (BREAKEVEN_R * stop_dist)
            target_partial = entry_price - (PARTIAL_R * stop_dist)

            score = 100 + (prev_candle['adx14'] - 20)

            btc_macro_now = btc_macro_map.get(current_time)
            btc_adx_1d = btc_macro_now.get('adx_1d', 0.0) if isinstance(btc_macro_now, dict) else 0.0

            short_candidates_by_time[current_time].append({
                'symbol': s,
                'score': score,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'stop_dist': stop_dist,
                'stop_dist_pct': stop_dist_pct,
                'breakeven_trigger': breakeven_trigger,
                'target_partial': target_partial,
                'alpha_7d': 0.0,
                'daily_avg_vol_30d': float(prev_candle['daily_avg_vol_30d']),
                'regime': "Short Bear (BE/Par. 2.0R / Runner 50%)",
                'adx_val': prev_candle['adx14'],
                'direction': 'SHORT',
                'rsi_1d': float(prev_candle['rsi14']) if pd.notna(prev_candle['rsi14']) else 0.0,
                'atr_1d_pct': float(prev_candle['atr14_1d'] / (prev_candle['close_1d'] + 1e-9)) if pd.notna(prev_candle.get('atr14_1d', np.nan)) else 0.0,
                'btc_adx_1d': btc_adx_1d,
            })

    print(f"Iniciando loop de simulação da carteira (Risco {p['risk_pct']*100:.2f}%, até {p['max_positions']} posições)...")

    for current_time in all_timestamps:
        btc_regime = btc_macro_map.get(current_time, {'bull': False, 'bear': False, 'transition': True})
        if isinstance(btc_regime, dict):
            btc_bull = btc_regime['bull']
            btc_bear = btc_regime['bear']
        else:
            btc_bull = btc_regime
            btc_bear = False

        effective_risk = p['risk_pct']
        skip_new_entries = False

        closed_trades = [t for t in trades if t['status'] == 'CLOSED']
        if len(closed_trades) >= 3:
            last_3 = closed_trades[-3:]
            if all(t['pnl_brl'] < 0 for t in last_3):
                effective_risk = p['risk_pct'] * 0.50

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

        allocated_total = sum(pos['allocated_capital'] * pos['remaining_pct'] for pos in active_positions.values())
        free_cash = max(capital - allocated_total, 0.0)
        cash_interest = free_cash * cash_yield_per_4h
        capital += cash_interest
        total_cash_yield_earned += cash_interest

        for s in list(active_positions.keys()):
            pos = active_positions[s]
            df4 = coins_4h_map.get(s)
            if df4 is None or current_time not in df4.index:
                continue
            candle = df4.loc[current_time]

            c_high = candle['high']
            c_low = candle['low']
            c_close = candle['close']
            c_rsi = candle['rsi14']

            entry_price = pos['entry_price']
            allocated_capital = pos['allocated_capital']
            pos['candles_held'] += 1

            is_long = pos.get('direction', 'LONG') == 'LONG'

            if current_time.hour in [0, 8, 16] and current_time > pos['entry_date']:
                fr_val = _last_funding_before(funding_map, s, current_time)
                funding_fee = funding_charge(is_long, allocated_capital, pos['remaining_pct'],
                                             entry_price, candle['open'], fr_val)
                capital -= funding_fee
                pos['pnl_brl'] -= funding_fee
                pos['funding_paid'] = pos.get('funding_paid', 0.0) + funding_fee

            # MAE/MFE em R (instrumentação)
            if is_long:
                pct_ret_now = (c_close - entry_price) / entry_price
            else:
                pct_ret_now = (entry_price - c_close) / entry_price
            unreal_r = (allocated_capital * pos['remaining_pct']) * pct_ret_now / (pos['risk_brl'] + 1e-9)
            pos['mfe_r'] = max(pos.get('mfe_r', 0.0), unreal_r)
            pos['mae_r'] = min(pos.get('mae_r', 0.0), unreal_r)

            def close_position(exit_price, reason, pct_of_position):
                nonlocal capital
                if is_long:
                    pct_return = (exit_price - entry_price) / entry_price
                else:
                    pct_return = (entry_price - exit_price) / entry_price
                gross = (allocated_capital * pct_of_position) * pct_return
                fee = (allocated_capital * pct_of_position * (1 + abs(pct_return))) * p['fee_pct']
                pnl = gross - fee
                capital += pnl
                pos['pnl_brl'] += pnl
                pos['fees_paid'] = pos.get('fees_paid', 0.0) + fee
                pos['exit_dates'].append(current_time)
                pos['exit_prices'].append(exit_price)
                pos['exit_reasons'].append(reason)
                pos['stop_final'] = pos['stop_loss']

            def finalize():
                pos['final_capital'] = capital
                pos['status'] = 'CLOSED'
                trades.append(pos)
                del active_positions[s]

            if not pos['t1_taken']:
                stop_hit = (c_low <= pos['stop_loss']) if is_long else (c_high >= pos['stop_loss'])
                if stop_hit:
                    stop_exec = pos['stop_loss'] * (1 - p['stop_slippage']) if is_long else pos['stop_loss'] * (1 + p['stop_slippage'])
                    close_position(stop_exec, "Stop Loss Inicial" if not pos.get('breakeven_set') else "Stop Breakeven (0x0)", pos['remaining_pct'])
                    finalize()
                    continue

                be_hit = (c_high >= pos['breakeven_trigger']) if is_long else (c_low <= pos['breakeven_trigger'])
                if be_hit:
                    pos['breakeven_set'] = True
                    pos['stop_loss'] = entry_price * 1.001 if is_long else entry_price * 0.999
                    pos['t1_taken'] = True
                    pos['remaining_pct'] = 1.0 - PARTIAL_PCT
                    pos['trail_high'] = c_high if is_long else c_low
                    close_position(pos['target_partial'], "Parcial Segurança (2.0R / 50%)", PARTIAL_PCT)
                    pos['breakeven_trigger'] = None
                    continue

                if pos['candles_held'] >= TIME_STOP_CANDLES:
                    close_position(c_close, "Time-Stop (21d)", pos['remaining_pct'])
                    finalize()
                    continue

            else:
                stop_hit = (c_low <= pos['stop_loss']) if is_long else (c_high >= pos['stop_loss'])
                if stop_hit:
                    stop_exec = pos['stop_loss'] * (1 - p['stop_slippage']) if is_long else pos['stop_loss'] * (1 + p['stop_slippage'])
                    close_position(stop_exec, "Stop BE Runner (50%)", pos['remaining_pct'])
                    finalize()
                    continue

                if is_long:
                    pos['trail_high'] = max(pos.get('trail_high', c_high), c_high)
                else:
                    pos['trail_high'] = min(pos.get('trail_high', c_low), c_low)

                runner_mode = p['runner_mode']
                exit_runner = False
                if runner_mode == 'ema20_1d':
                    runner_ema = candle.get('ema20_1d', None)
                    if runner_ema is not None and not pd.isna(runner_ema):
                        exit_runner = (c_close < runner_ema) if is_long else (c_close > runner_ema)
                elif runner_mode == 'prev_low_1d':
                    lvl = candle.get('low_1d', None) if is_long else candle.get('high_1d', None)
                    if lvl is not None and not pd.isna(lvl):
                        exit_runner = (c_close < lvl) if is_long else (c_close > lvl)
                elif runner_mode == 'atr_chandelier':
                    atr_d = candle.get('atr14_1d', None)
                    if atr_d is not None and not pd.isna(atr_d):
                        if is_long:
                            exit_runner = c_close < (pos.get('trail_high', c_high) - 3.0 * atr_d)
                        else:
                            exit_runner = c_close > (pos.get('trail_high', c_low) + 3.0 * atr_d)

                if exit_runner:
                    close_position(c_close, f"Trailing Runner 50% ({runner_mode})", pos['remaining_pct'])
                    finalize()
                    continue

        raw_candidates = candidates_by_time.get(current_time, [])
        if btc_bull and raw_candidates and not skip_new_entries and len(active_positions) < p['max_positions']:
            eligible = [c for c in raw_candidates if c['symbol'] not in active_positions]
            eligible = [c for c in eligible if c['symbol'] not in recent_loss_exits or (current_time - recent_loss_exits[c['symbol']]).total_seconds() >= cooldown_seconds]
            if eligible:
                eligible.sort(key=lambda x: x['score'], reverse=True)
                available_slots = p['max_positions'] - len(active_positions)
                selected = eligible[:available_slots]

                for c in selected:
                    risk_brl = capital * effective_risk
                    allocated_capital = min(risk_brl / c['stop_dist_pct'], capital * 1.5)
                    entry_fee = allocated_capital * p['fee_pct']
                    capital -= entry_fee

                    active_positions[c['symbol']] = {
                        'symbol': c['symbol'], 'entry_date': current_time, 'entry_price': c['entry_price'],
                        'stop_loss': c['stop_loss'], 'stop_initial': c['stop_loss'], 'stop_final': c['stop_loss'],
                        'stop_dist': c['stop_dist'], 'stop_dist_pct': c['stop_dist_pct'],
                        'breakeven_trigger': c['breakeven_trigger'], 'target_partial': c['target_partial'],
                        'regime': c['regime'], 'direction': 'LONG',
                        'regime_macro': 'bull' if btc_bull else ('bear' if btc_bear else 'transition'),
                        'asset_class': _asset_class(c['symbol']),
                        'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                        'score': c['score'], 'candles_held': 0,
                        'rsi_1d': c.get('rsi_1d', 0.0), 'atr_1d_pct': c.get('atr_1d_pct', 0.0),
                        'btc_adx_1d': c.get('btc_adx_1d', 0.0),
                        'breakeven_set': False, 't1_taken': False,
                        'remaining_pct': 1.0, 'mae_r': 0.0, 'mfe_r': 0.0, 'trail_high': 0.0,
                        'exit_dates': [], 'exit_prices': [], 'exit_reasons': [],
                        'pnl_brl': -entry_fee, 'fees_paid': entry_fee, 'funding_paid': 0.0,
                        'status': 'OPEN'
                    }

        if btc_bear and not skip_new_entries and len(active_positions) < p['max_positions']:
            short_raw = short_candidates_by_time.get(current_time, [])
            short_eligible = [c for c in short_raw if c['symbol'] not in active_positions]
            short_eligible = [c for c in short_eligible if c['symbol'] not in recent_loss_exits or (current_time - recent_loss_exits[c['symbol']]).total_seconds() >= cooldown_seconds]

            if short_eligible:
                short_eligible.sort(key=lambda x: x['score'], reverse=True)
                available_slots = p['max_positions'] - len(active_positions)
                short_selected = short_eligible[:available_slots]

                for c in short_selected:
                    risk_brl = capital * effective_risk
                    allocated_capital = min(risk_brl / c['stop_dist_pct'], capital * 1.5)
                    entry_fee = allocated_capital * p['fee_pct']
                    capital -= entry_fee

                    active_positions[c['symbol']] = {
                        'symbol': c['symbol'], 'entry_date': current_time, 'entry_price': c['entry_price'],
                        'stop_loss': c['stop_loss'], 'stop_initial': c['stop_loss'], 'stop_final': c['stop_loss'],
                        'stop_dist': c['stop_dist'], 'stop_dist_pct': c['stop_dist_pct'],
                        'breakeven_trigger': c['breakeven_trigger'], 'target_partial': c['target_partial'],
                        'regime': c['regime'], 'direction': 'SHORT',
                        'regime_macro': 'bear',
                        'asset_class': _asset_class(c['symbol']),
                        'allocated_capital': allocated_capital, 'risk_brl': risk_brl,
                        'score': c['score'], 'candles_held': 0,
                        'rsi_1d': c.get('rsi_1d', 0.0), 'atr_1d_pct': c.get('atr_1d_pct', 0.0),
                        'btc_adx_1d': c.get('btc_adx_1d', 0.0),
                        'breakeven_set': False, 't1_taken': False,
                        'remaining_pct': 1.0, 'mae_r': 0.0, 'mfe_r': 0.0, 'trail_high': 0.0,
                        'exit_dates': [], 'exit_prices': [], 'exit_reasons': [],
                        'pnl_brl': -entry_fee, 'fees_paid': entry_fee, 'funding_paid': 0.0,
                        'status': 'OPEN'
                    }

        unrealized_pnl = 0.0
        for s_act, p_act in active_positions.items():
            df_sym_curr = coins_4h_map.get(s_act)
            if df_sym_curr is not None and current_time in df_sym_curr.index:
                c_close_now = df_sym_curr.loc[current_time]['close']
                if p_act.get('direction', 'LONG') == 'LONG':
                    pct_ret_now = (c_close_now - p_act['entry_price']) / p_act['entry_price']
                else:
                    pct_ret_now = (p_act['entry_price'] - c_close_now) / p_act['entry_price']
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
            if current_time >= sm and sm.strftime('%Y-%m-%d') not in semester_checkpoints:
                semester_checkpoints[sm.strftime('%Y-%m-%d')] = total_mtm_equity

    for s, pos in list(active_positions.items()):
        df4 = coins_4h_map.get(s)
        if df4 is not None:
            last_sub = df4[df4.index <= end_date]
            if not last_sub.empty:
                last_candle = last_sub.iloc[-1]
                c_close = last_candle['close']
                is_long = pos.get('direction', 'LONG') == 'LONG'
                if is_long:
                    pct_return = (c_close - pos['entry_price']) / pos['entry_price']
                else:
                    pct_return = (pos['entry_price'] - c_close) / pos['entry_price']
                gross_pnl = (pos['allocated_capital'] * pos['remaining_pct']) * pct_return
                exit_fee = (pos['allocated_capital'] * pos['remaining_pct'] * (1 + pct_return)) * p['fee_pct']
                pnl_brl = gross_pnl - exit_fee
                capital += pnl_brl
                pos['exit_dates'].append(last_sub.index[-1])
                pos['exit_prices'].append(c_close)
                pos['exit_reasons'].append("Fechamento Fim do Período (MtM)")
                pos['stop_final'] = pos['stop_loss']
                pos['pnl_brl'] += pnl_brl
                pos['fees_paid'] = pos.get('fees_paid', 0.0) + exit_fee
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

    equity_df['period_return'] = equity_df['capital'].pct_change()
    period_rets = equity_df['period_return'].dropna()
    sharpe = (period_rets.mean() / (period_rets.std() + 1e-9)) * np.sqrt(2190) if len(period_rets) > 0 else 0.0
    downside = period_rets[period_rets < 0]
    sortino = (period_rets.mean() / (downside.std() + 1e-9)) * np.sqrt(2190) if len(downside) > 0 else 0.0

    total_fees_brl = sum(t.get('fees_paid', 0.0) for t in trades)
    total_funding_brl = sum(t.get('funding_paid', 0.0) for t in trades)
    trading_pnl_net_brl = sum(t['pnl_brl'] for t in trades)
    trading_pnl_gross_brl = trading_pnl_net_brl + total_fees_brl + total_funding_brl

    expectancy_r = (np.mean([t['pnl_brl'] / (t['risk_brl'] + 1e-9) for t in trades]) if trades else 0.0)
    avg_mae_r = (np.mean([t['mae_r'] for t in trades]) if trades else 0.0)
    avg_mfe_r = (np.mean([t['mfe_r'] for t in trades]) if trades else 0.0)

    # Benchmarks B&H BTC/ETH no período (sem taxas)
    bnh = {}
    for sym in ['BTCUSDT', 'ETHUSDT']:
        df1 = pd.read_csv(os.path.join(MACRO_DIR, f'{sym}_1d.csv')) if sym == 'BTCUSDT' else None
        df4 = coins_4h_map.get(sym)
        val = 0.0
        if df4 is not None:
            d_in = df4[df4.index >= start_date]
            d_out = df4[df4.index <= end_date]
            if not d_in.empty and not d_out.empty:
                p0 = float(d_in.iloc[0]['close'])
                p1 = float(d_out.iloc[-1]['close'])
                if p0 > 0:
                    val = (p1 - p0) / p0 * 100
        bnh[sym.replace('USDT', '')] = val

    n = total_trades
    p_hat = win_rate / 100.0 if n > 0 else 0.0
    z = 1.96
    if n > 0:
        denom = 1 + z * z / n
        center = p_hat + z * z / (2 * n)
        margin = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n))
        ci_low = max(0.0, (center - margin) / denom) * 100
        ci_high = min(1.0, (center + margin) / denom) * 100
    else:
        ci_low, ci_high = 0.0, 0.0

    # Segmentações diagnósticas
    def segment_by(key_fn):
        seg = {}
        for t in trades:
            k = key_fn(t)
            seg.setdefault(k, {'n': 0, 'win': 0, 'pnl': 0.0, 'r_sum': 0.0})
            seg[k]['n'] += 1
            if t['pnl_brl'] > 0.001:
                seg[k]['win'] += 1
            seg[k]['pnl'] += t['pnl_brl']
            seg[k]['r_sum'] += t['pnl_brl'] / (t['risk_brl'] + 1e-9)
        out = {}
        for k, v in seg.items():
            out[k] = {
                'trades': v['n'],
                'win_rate_pct': round(v['win'] / v['n'] * 100, 1) if v['n'] else 0.0,
                'pnl_brl': round(v['pnl'], 2),
                'avg_r': round(v['r_sum'] / v['n'], 3) if v['n'] else 0.0
            }
        return out

    results = {
        'engine_version': ENGINE_VERSION,
        'params': p,
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
        'win_rate_ci95_low_pct': ci_low,
        'win_rate_ci95_high_pct': ci_high,
        'min_trades_warning': total_trades < 30,
        'profit_factor': profit_factor,
        'max_drawdown_pct': max_drawdown_pct,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'expectancy_r': expectancy_r,
        'avg_mae_r': avg_mae_r,
        'avg_mfe_r': avg_mfe_r,
        'total_cash_yield_brl': total_cash_yield_earned,
        'total_funding_fees_brl': total_funding_brl,
        'total_fees_brl': total_fees_brl,
        'trading_pnl_net_brl': trading_pnl_net_brl,
        'trading_pnl_gross_brl': trading_pnl_gross_brl,
        'bnh_btc_return_pct': bnh.get('BTC', 0.0),
        'bnh_eth_return_pct': bnh.get('ETH', 0.0),
        'coins_scanned': len(available_symbols),
        'semester_checkpoints': semester_checkpoints,
        'seg_by_regime': segment_by(lambda t: t.get('regime_macro', '?')),
        'seg_by_asset': segment_by(lambda t: t.get('asset_class', '?')),
        'seg_by_exit': segment_by(lambda t: t['exit_reasons'][-1] if t['exit_reasons'] else '?')
    }

    return results, trades, equity_df


def config_hash(params):
    blob = json.dumps(params, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()[:8]


def compact_metrics(res):
    return {
        'window': f"{res['start_date']} -> {res['end_date']}",
        'trades': res['total_trades'],
        'return_pct': round(res['return_pct'], 2),
        'trading_pnl': round(res['trading_pnl_net_brl'], 2),
        'pf': round(res['profit_factor'], 2),
        'win_rate': round(res['win_rate_pct'], 1),
        'dd_pct': round(res['max_drawdown_pct'], 2),
        'sharpe': round(res['sharpe_ratio'], 2),
        'expectancy_r': round(res['expectancy_r'], 3),
        'bnh_btc_pct': round(res['bnh_btc_return_pct'], 2)
    }


def _trade_record(t):
    def _iso(d):
        return d.strftime('%Y-%m-%d %H:%M') if isinstance(d, pd.Timestamp) else str(d)

    return {
        'entry_date': _iso(t['entry_date']),
        'symbol': t['symbol'],
        'direction': t.get('direction', 'LONG'),
        'pnl_brl': round(t['pnl_brl'], 4),
        'risk_brl': round(t.get('risk_brl', 0.0), 4),
        'fees_paid': round(t.get('fees_paid', 0.0), 4),
        'funding_paid': round(t.get('funding_paid', 0.0), 4),
        'stop_dist_pct': round(t.get('stop_dist_pct', 0.0), 6),
        'asset_class': t.get('asset_class', '?'),
        'regime_macro': t.get('regime_macro', '?'),
        'rsi_1d': round(t.get('rsi_1d', 0.0), 4),
        'atr_1d_pct': round(t.get('atr_1d_pct', 0.0), 6),
        'btc_adx_1d': round(t.get('btc_adx_1d', 0.0), 4),
        'exit_dates': [_iso(d) for d in t['exit_dates']],
        'exit_reasons': t['exit_reasons'],
    }


def append_analises_entry(entry_md):
    with open(ANALISES_PATH, 'a', encoding='utf-8') as f:
        f.write("\n" + entry_md)


def run_walkforward(params, initial_capital=100000.0, append=True, preloaded=None):
    if preloaded is None:
        print("Carregando dados uma única vez para todas as janelas...")
        preloaded = load_all_data()
    wf_results = {}
    wf_detail = {}
    for name, s, e in WALKFORWARD_WINDOWS:
        print(f"\n>>> Janela {name}: {s} -> {e}")
        res, trades, eq = run_portfolio_backtest(s, e, initial_capital, params=params, preloaded=preloaded)
        wf_results[name] = compact_metrics(res)
        wf_detail[name] = {
            'trades': [_trade_record(t) for t in trades],
            'equity_curve': [round(float(v), 2) for v in eq['capital'].tolist()],
        }

    oos = [wf_results[n] for n in ['OOS1', 'OOS2', 'OOS3', 'OOS4']]

    def agg(field):
        return sum(w[field] for w in oos)

    def median(field):
        vals = sorted(w[field] for w in oos)
        m = len(vals)
        return vals[m // 2] if m % 2 else (vals[m // 2 - 1] + vals[m // 2]) / 2

    summary = {
        'config': params,
        'config_hash': config_hash(params),
        'engine_version': ENGINE_VERSION,
        'generated_at': datetime.datetime.utcnow().isoformat(),
        'windows': wf_results,
        'windows_detail': wf_detail,
        'oos_aggregate': {
            'trades_total': agg('trades'),
            'return_pct_sum': round(agg('return_pct'), 2),
            'trading_pnl_sum': round(agg('trading_pnl'), 2),
            'pf_mean': round(np.mean([w['pf'] for w in oos]), 2),
            'pf_median': round(median('pf'), 2),
            'win_rate_mean': round(np.mean([w['win_rate'] for w in oos]), 1),
            'dd_max': round(max(w['dd_pct'] for w in oos), 2),
            'sharpe_mean': round(np.mean([w['sharpe'] for w in oos]), 2),
            'expectancy_r_mean': round(np.mean([w['expectancy_r'] for w in oos]), 3)
        }
    }

    exp_path = os.path.join(EXP_DIR, f'exp_{summary["config_hash"]}.json')
    with open(exp_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 100)
    print(f"WALK-FORWARD | config hash: {summary['config_hash']}")
    print(f"params: {json.dumps(params, ensure_ascii=False)}")
    print("=" * 100)
    hdr = f"{'Janela':<6} {'Trades':>7} {'Ret%':>9} {'TradingPnL':>12} {'PF':>6} {'Win%':>7} {'DD%':>7} {'Sharpe':>8} {'ExpR':>8} {'B&H BTC%':>9}"
    print(hdr)
    for name, m in wf_results.items():
        print(f"{name:<6} {m['trades']:>7} {m['return_pct']:>9.2f} {m['trading_pnl']:>12,.2f} {m['pf']:>6.2f} "
              f"{m['win_rate']:>7.1f} {m['dd_pct']:>7.2f} {m['sharpe']:>8.2f} {m['expectancy_r']:>8.3f} {m['bnh_btc_pct']:>9.2f}")
    oa = summary['oos_aggregate']
    print("-" * 100)
    print(f"OOS AGREGADO (4 blocos): trades={oa['trades_total']} | ret%={oa['return_pct_sum']} | "
          f"tradingPnL={oa['trading_pnl_sum']:,.2f} | PF méd={oa['pf_mean']} (med={oa['pf_median']}) | "
          f"Win%={oa['win_rate_mean']} | DDmáx={oa['dd_max']} | Sharpe={oa['sharpe_mean']} | ExpR={oa['expectancy_r_mean']}")
    print(f"Arquivo: {exp_path}")
    if not append:
        print("Registro no analises.md pulado (--no-append)")
        return summary

    entry = f"""## [{datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M')}] - Experimento Walk-Forward: config {summary['config_hash']}
- **Mudança Implementada:** Parâmetros testados: {json.dumps(params, ensure_ascii=False)}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{json.dumps(summary['oos_aggregate'], indent=2, ensure_ascii=False)}
```
- **Análise Diagnóstica:** IS/OOS por janela: {json.dumps(wf_results, ensure_ascii=False)}
"""
    append_analises_entry(entry)
    print("Registro adicionado ao analises.md")
    return summary


def save_outputs(args, res, trades, initial_capital):
    params = res['params']
    print("\n" + "=" * 80)
    print(f"RESUMO EXECUTIVO DO MOTOR QUANTITATIVO (Prompt {res['engine_version']} | Risco {params['risk_pct']*100:.2f}%)")
    print("=" * 80)
    print(f"Período: {res['start_date']} até {res['end_date']}")
    print(f"Universo Monitorado: {res['coins_scanned']} moedas")
    print(f"Capital Inicial: R$ {res['initial_capital']:,.2f}")
    print(f"Capital Final: R$ {res['final_capital']:,.2f} ({res['return_pct']:+.2f}%)")
    print(f"Total de Trades: {res['total_trades']} | Vencedores: {res['winning_trades']} | Perdedores: {res['losing_trades']} | 0x0: {res['breakeven_trades']}")
    print(f"Win Rate: {res['win_rate_pct']:.2f}% (IC 95%: {res['win_rate_ci95_low_pct']:.1f}% - {res['win_rate_ci95_high_pct']:.1f}%)")
    print(f"Profit Factor: {res['profit_factor']:.2f} | Expectância: {res['expectancy_r']:+.3f}R")
    print(f"Drawdown Máximo MtM: {res['max_drawdown_pct']:.2f}%")
    print(f"Sharpe Ratio: {res['sharpe_ratio']:.2f} | Sortino Ratio: {res['sortino_ratio']:.2f}")
    print("-" * 80)
    print("DECOMPOSIÇÃO DO RESULTADO:")
    print(f"  PnL de Trading (líquido): R$ {res['trading_pnl_net_brl']:,.2f} | (bruto): R$ {res['trading_pnl_gross_brl']:,.2f}")
    print(f"  Taxas: R$ {res['total_fees_brl']:,.2f} | Funding: R$ {res['total_funding_fees_brl']:,.2f} | Cash Yield: R$ {res['total_cash_yield_brl']:,.2f}")
    print(f"  Benchmark B&H BTC: {res['bnh_btc_return_pct']:+.2f}% | B&H ETH: {res['bnh_eth_return_pct']:+.2f}%")
    print(f"  MAE médio: {res['avg_mae_r']:.2f}R | MFE médio: {res['avg_mfe_r']:+.2f}R")
    print("-" * 80)
    print("CARTEIRAS HÍBRIDAS HIPOTÉTICAS (X% B&H BTC + (1-X)% Sistema, sem rebalanceamento):")
    for hb in [0.25, 0.50, 0.75]:
        hyb = hb * res['bnh_btc_return_pct'] + (1 - hb) * res['return_pct']
        print(f"  Híbrido {int(hb*100)}/{(1-hb)*100:.0f}: {hyb:+.2f}%")
    print("-" * 80)
    print("SEGMENTAÇÃO DIAGNÓSTICA:")
    print(f"  Por regime de entrada: {json.dumps(res['seg_by_regime'], ensure_ascii=False)}")
    print(f"  Por classe de ativo: {json.dumps(res['seg_by_asset'], ensure_ascii=False)}")
    print(f"  Por motivo de saída: {json.dumps(res['seg_by_exit'], ensure_ascii=False)}")
    if res['min_trades_warning']:
        print("  [AVISO ESTATISTICO] Menos de 30 trades.")
    print("=" * 80)

    print("\nCHECKPOINTS SEMESTRAIS (dentro do período):")
    prev_val = res['initial_capital']
    for dt_str, val in res['semester_checkpoints'].items():
        sem_ret = ((val - prev_val) / prev_val) * 100 if prev_val else 0
        cum_ret = ((val - res['initial_capital']) / res['initial_capital']) * 100
        print(f"• {dt_str} | Saldo: R$ {val:12,.2f} | Período: {sem_ret:+7.2f}% | Acumulado: {cum_ret:+7.2f}%")
        prev_val = val

    json_path = os.path.join(DATA_DIR, f'resumo_{args.mode}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=4, ensure_ascii=False)

    trades_records = []
    running_bal = initial_capital
    for t in trades:
        running_bal += t['pnl_brl']
        trades_records.append({
            'Data Entrada': t['entry_date'].strftime('%Y-%m-%d %H:%M') if isinstance(t['entry_date'], pd.Timestamp) else str(t['entry_date']),
            'Ativo': t['symbol'].replace('USDT', ''),
            'Direção': t.get('direction', 'LONG'),
            'Regime': t['regime'],
            'Regime Macro': t.get('regime_macro', '?'),
            'Classe': t.get('asset_class', '?'),
            'Score': round(t['score'], 1),
            'Preço Entrada': f"${t['entry_price']:.4f}",
            'Stop Inicial': f"${t.get('stop_initial', t['stop_loss']):.4f} ({t['stop_dist_pct']*100:.2f}%)",
            'Stop Final': f"${t.get('stop_final', t['stop_loss']):.4f}",
            'BE/Parcial (2.0R)': f"${t.get('target_partial', 0.0):.4f}",
            'MAE (R)': round(t.get('mae_r', 0.0), 2),
            'MFE (R)': round(t.get('mfe_r', 0.0), 2),
            'Datas Saída': " | ".join([d.strftime('%Y-%m-%d %H:%M') if isinstance(d, pd.Timestamp) else str(d) for d in t['exit_dates']]),
            'Preços Saída': " | ".join([f"${p:.4f}" for p in t['exit_prices']]),
            'Motivo Saída': " | ".join(t['exit_reasons']),
            'Taxas (R$)': f"R$ {t.get('fees_paid', 0.0):,.2f}",
            'Funding (R$)': f"R$ {t.get('funding_paid', 0.0):,.2f}",
            'Resultado (R$)': f"R$ {t['pnl_brl']:+,.2f}",
            'Resultado (R)': round(t['pnl_brl'] / (t['risk_brl'] + 1e-9), 2),
            'Saldo Acumulado (R$)': f"R$ {running_bal:,.2f}"
        })

    csv_path = os.path.join(DATA_DIR, f'trades_{args.mode}.csv')
    columns = ['Data Entrada', 'Ativo', 'Direção', 'Regime', 'Regime Macro', 'Classe', 'Score',
               'Preço Entrada', 'Stop Inicial', 'Stop Final', 'BE/Parcial (2.0R)', 'MAE (R)', 'MFE (R)',
               'Datas Saída', 'Preços Saída', 'Motivo Saída', 'Taxas (R$)', 'Funding (R$)',
               'Resultado (R$)', 'Resultado (R)', 'Saldo Acumulado (R$)']
    if trades_records:
        tdf = pd.DataFrame(trades_records)
        tdf.to_csv(csv_path, index=False, encoding='utf-8')
    else:
        pd.DataFrame(columns=columns).to_csv(csv_path, index=False, encoding='utf-8')

    md_report_path = os.path.join(REPORTS_DIR, f'relatorio_{args.mode}.md')
    md_content = f"""# Relatório de Auditoria Quantitativa: Modalidade [{args.mode.upper()}]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** {res['engine_version']}
- **Parâmetros Blindados:** {json.dumps(params, ensure_ascii=False)}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** {res['start_date']} até {res['end_date']}
- **Universo Monitorado:** {res['coins_scanned']} moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ {res['initial_capital']:,.2f}
- **Saldo Final:** R$ {res['final_capital']:,.2f} ({res['return_pct']:+.2f}%)
- **Lucro Líquido Real:** R$ {res['net_profit_brl']:,.2f}
- **Total de Trades:** {res['total_trades']} ({res['winning_trades']} Vitórias / {res['losing_trades']} Derrotas / {res['breakeven_trades']} no 0x0)
- **Taxa de Acerto (Win Rate):** {res['win_rate_pct']:.2f}% (IC 95%: {res['win_rate_ci95_low_pct']:.1f}% - {res['win_rate_ci95_high_pct']:.1f}%)
- **Fator de Lucro (Profit Factor):** {res['profit_factor']:.2f}
- **Expectância por Trade:** {res['expectancy_r']:+.3f}R | MAE médio {res['avg_mae_r']:.2f}R | MFE médio {res['avg_mfe_r']:+.2f}R
- **Drawdown Máximo (MtM):** {res['max_drawdown_pct']:.2f}%
- **Sharpe Ratio:** {res['sharpe_ratio']:.2f} | **Sortino Ratio:** {res['sortino_ratio']:.2f}

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | {res['trading_pnl_net_brl']:+,.2f} |
| PnL de Trading (bruto, antes de custos) | {res['trading_pnl_gross_brl']:+,.2f} |
| Taxas de Corretagem Pagas | {res['total_fees_brl']:,.2f} |
| Funding Pagos/Recebidos | {res['total_funding_fees_brl']:+,.2f} |
| Rendimento do Caixa (6% a.a.) | {res['total_cash_yield_brl']:,.2f} |
| **Benchmark Buy & Hold BTC (sem taxas)** | **{res['bnh_btc_return_pct']:+.2f}%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **{res['bnh_eth_return_pct']:+.2f}%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | {0.25 * res['bnh_btc_return_pct'] + 0.75 * res['return_pct']:+.2f}% |
| 50% BTC / 50% Sistema | {0.50 * res['bnh_btc_return_pct'] + 0.50 * res['return_pct']:+.2f}% |
| 75% BTC / 25% Sistema | {0.75 * res['bnh_btc_return_pct'] + 0.25 * res['return_pct']:+.2f}% |

{f"⚠️ **ATENÇÃO ESTATÍSTICA:** amostra de apenas {res['total_trades']} trades (< 30). Conclusões não são estatisticamente robustas." if res['min_trades_warning'] else ""}

---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
"""
    for k, v in res['seg_by_regime'].items():
        md_content += f"| {k} | {v['trades']} | {v['win_rate_pct']}% | {v['pnl_brl']:+,.2f} | {v['avg_r']:+.3f} |\n"

    md_content += "\n### Por Classe de Ativo\n| Classe | Trades | Win Rate | PnL (R$) | Avg R |\n| :--- | :---: | :---: | :---: | :---: |\n"
    for k, v in res['seg_by_asset'].items():
        md_content += f"| {k} | {v['trades']} | {v['win_rate_pct']}% | {v['pnl_brl']:+,.2f} | {v['avg_r']:+.3f} |\n"

    md_content += "\n### Por Motivo de Saída\n| Motivo | Trades | Win Rate | PnL (R$) | Avg R |\n| :--- | :---: | :---: | :---: | :---: |\n"
    for k, v in res['seg_by_exit'].items():
        md_content += f"| {k} | {v['trades']} | {v['win_rate_pct']}% | {v['pnl_brl']:+,.2f} | {v['avg_r']:+.3f} |\n"

    md_content += f"""

---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='full',
                        choices=['full', '5anos', 'preliminar', 'estresse_bear', 'estresse_bull', 'estresse_chop', 'all'],
                        help='Modalidade de teste')
    parser.add_argument('--start_date', type=str, default=None)
    parser.add_argument('--end_date', type=str, default=None)
    parser.add_argument('--capital', type=float, default=100000.0)
    parser.add_argument('--risk', type=float, default=0.015)
    parser.add_argument('--max_pos', type=int, default=4)
    parser.add_argument('--walkforward', action='store_true', help='Roda avaliação walk-forward deslizante')
    parser.add_argument('--btc-adx-min', type=float, default=0.0, help='e1: ADX 1D BTC mínimo para longs (0=off)')
    parser.add_argument('--entry-tf', type=str, default='1d', choices=['4h', '1d'], help='e2: timeframe do gatilho')
    parser.add_argument('--long-mode', type=str, default='pullback', choices=['pullback', 'breakout'], help='e9: gatilho LONG (pullback na EMA20 ou rompimento diario)')
    parser.add_argument('--runner-mode', type=str, default='ema20_1d', choices=['ema20_1d', 'prev_low_1d', 'atr_chandelier'], help='e3: modo do runner')
    parser.add_argument('--short-mode', type=str, default='breakout', choices=['revert', 'breakout', 'none'], help='e4: modo do short')
    parser.add_argument('--universe', type=str, default='alpha', choices=['alpha', 'top20', 'btceth'], help='e5: seleção de líderes')
    parser.add_argument('--fee', type=float, default=0.00075, help='e6: taxa de corretagem')
    parser.add_argument('--no-append', action='store_true', help='Nao registra a execucao no analises.md (re-runs de validacao)')
    args = parser.parse_args()

    modes_dates = {
        'full': ('2019-09-01', '2026-08-20'),
        '5anos': ('2021-11-15', '2026-08-20'),
        'preliminar': ('2023-10-01', '2024-10-01'),
        'estresse_bear': ('2022-01-01', '2022-12-31'),
        'estresse_bull': ('2023-10-01', '2024-03-31'),
        'estresse_chop': ('2024-04-01', '2024-09-30')
    }

    params = {
        'risk_pct': args.risk,
        'max_positions': args.max_pos,
        'fee_pct': args.fee,
        'btc_adx_min': args.btc_adx_min,
        'entry_tf': args.entry_tf,
        'runner_mode': args.runner_mode,
        'short_mode': args.short_mode,
        'universe': args.universe
    }

    if args.walkforward:
        run_walkforward(params, args.capital, append=not args.no_append)
        sys.exit(0)

    modes_to_run = list(modes_dates.keys()) if args.mode == 'all' else [args.mode]

    for mode in modes_to_run:
        if args.start_date is None or args.end_date is None:
            start_dt, end_dt = modes_dates[mode]
        else:
            start_dt, end_dt = args.start_date, args.end_date

        print(f"\n>>> EXECUTANDO MODALIDADE DE TESTE: [{mode.upper()}] ({start_dt} a {end_dt}) <<<\n")
        run_args = argparse.Namespace(mode=mode)
        res, trades, eq_df = run_portfolio_backtest(start_dt, end_dt, args.capital, params=params)
        save_outputs(run_args, res, trades, args.capital)
