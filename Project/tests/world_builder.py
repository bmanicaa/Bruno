import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import backtest_institucional as bi

N4H = 2400
N1D = N4H // 6
BASE_TIME = pd.Timestamp('2019-09-01 00:00:00')
WINDOW_START_IDX = 2000
WINDOW_END_IDX = 2398
PULLBACK_DAYS = list(range(336, 396, 12))
FUNDING_RATE = 0.0001


def _ohlcv_from_close(close, open_, drift_open=True):
    n = len(close)
    if drift_open:
        open_arr = np.empty(n)
        open_arr[0] = open_
        open_arr[1:] = close[:-1]
    else:
        open_arr = np.full(n, open_)
    high = np.maximum(open_arr, close) * (1 + 0.0015)
    low = np.minimum(open_arr, close) * (1 - 0.0015)
    return open_arr, high, low


def build_raw_4h(seed=42, drift=0.0004):
    rng = np.random.default_rng(seed)
    times = BASE_TIME + pd.to_timedelta(np.arange(N4H) * 4, unit='h')
    noise = rng.normal(0, 0.0006, N4H)
    close = 100.0 * np.exp(np.cumsum(drift + noise))
    open_arr, high, low = _ohlcv_from_close(close, 100.0)
    volume = np.full(N4H, 1_000_000.0)
    return pd.DataFrame({
        'open_time': times,
        'open': open_arr,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
        'quote_volume': volume * close,
        'taker_buy_base': 0.55 * volume,
    })


def build_raw_1d(seed=42, drift=0.0035, pullbacks=False):
    rng = np.random.default_rng(seed + 7)
    times = BASE_TIME + pd.to_timedelta(np.arange(N1D), unit='D')
    log_close = np.cumsum(drift + rng.normal(0, 0.002, N1D))
    close = 100.0 * np.exp(log_close)
    if pullbacks:
        for d in PULLBACK_DAYS:
            base = close[d]
            close[d] = base * (1 - 0.025)
            close[d + 1] = close[d] * (1 + 0.015)
    open_arr, high, low = _ohlcv_from_close(close, 100.0)
    return pd.DataFrame({
        'open_time': times,
        'open': open_arr,
        'high': high,
        'low': low,
        'close': close,
    })


def _merge_daily_into_4h(df4, df1, extra_cols=None):
    df1_sub = df1[['open_time', 'close', 'high', 'low', 'ema20_1d', 'ema50_1d', 'ema200_1d',
                   'rsi14_1d', 'atr14_1d'] + (extra_cols or [])].copy()
    df1_sub.columns = ['open_time_1d', 'close_1d', 'high_1d', 'low_1d', 'ema20_1d', 'ema50_1d',
                       'ema200_1d', 'rsi14_1d', 'atr14_1d'] + (extra_cols or [])
    df1_prev = df1_sub[['open_time_1d', 'close_1d', 'high_1d', 'low_1d']].copy()
    df1_prev.columns = ['open_time_1d_prev', 'close_1d_prev', 'high_1d_prev', 'low_1d_prev']
    df1_prev['open_time_1d_prev'] = df1_prev['open_time_1d_prev'] + pd.Timedelta(days=2)
    df1_sub['open_time_1d'] = df1_sub['open_time_1d'] + pd.Timedelta(days=1)
    merged = pd.merge_asof(df4, df1_sub, left_on='open_time', right_on='open_time_1d',
                           direction='backward')
    merged = pd.merge_asof(merged, df1_prev, left_on='open_time', right_on='open_time_1d_prev',
                           direction='backward')
    merged.set_index('open_time', inplace=True)
    return merged


def build_funding_frame():
    times = BASE_TIME + pd.to_timedelta(np.arange(N4H * 4) * 8, unit='h')
    return pd.DataFrame({
        'fundingTime': times,
        'fundingRate': np.full(len(times), FUNDING_RATE),
    })


def build_world(seed=42):
    world, _, _ = _build_world(seed)
    return world


def build_world_with_raws(seed=42):
    return _build_world(seed)


def _build_world(seed=42):
    btc4_raw = build_raw_4h(seed=seed, drift=0.0001)
    alt4_raw = build_raw_4h(seed=seed + 1, drift=0.0015 / 6.0)
    btc1_raw = build_raw_1d(seed=seed + 2, drift=0.0035, pullbacks=False)
    alt1_raw = build_raw_1d(seed=seed + 3, drift=0.0015, pullbacks=True)

    btc4_raw['open_time'] = pd.to_datetime(btc4_raw['open_time'])
    alt4_raw['open_time'] = pd.to_datetime(alt4_raw['open_time'])
    btc1_raw['open_time'] = pd.to_datetime(btc1_raw['open_time'])
    alt1_raw['open_time'] = pd.to_datetime(alt1_raw['open_time'])

    btc4 = bi.compute_indicators_4h(btc4_raw)
    btc1 = bi.compute_indicators_1d(btc1_raw)
    alt4 = bi.compute_indicators_4h(alt4_raw)
    alt1 = bi.compute_indicators_1d(alt1_raw)

    btc4_sorted = btc4.sort_values('open_time').reset_index(drop=True)
    alt4_sorted = alt4.sort_values('open_time').reset_index(drop=True)

    btc4_merged = _merge_daily_into_4h(btc4_sorted, btc1, extra_cols=['adx14_1d'])
    alt4_merged = _merge_daily_into_4h(alt4_sorted, alt1)

    funding = build_funding_frame()
    funding_map = {'BTCUSDT': funding, 'TESTUSDT': funding}

    coins_4h_map = {'BTCUSDT': btc4_merged, 'TESTUSDT': alt4_merged}
    available_symbols = ['BTCUSDT', 'TESTUSDT']

    world = (btc4_sorted, btc1, pd.DataFrame(), coins_4h_map, funding_map, available_symbols)
    return world, alt4_raw, alt1_raw


def recompute_alt(alt4_raw, alt1_raw):
    alt4 = bi.compute_indicators_4h(alt4_raw)
    alt1 = bi.compute_indicators_1d(alt1_raw)
    alt4_sorted = alt4.sort_values('open_time').reset_index(drop=True)
    return alt4_sorted, _merge_daily_into_4h(alt4_sorted, alt1)


def window_dates():
    times = BASE_TIME + pd.to_timedelta(np.arange(N4H) * 4, unit='h')
    start = times[WINDOW_START_IDX]
    end = times[WINDOW_END_IDX]
    return start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')


def find_long_candidate_idx(alt4_merged, btc4_merged, start_idx=WINDOW_START_IDX):
    n = len(alt4_merged)
    for idx in range(max(start_idx, bi.MATURITY_CANDLES), min(WINDOW_END_IDX + 1, n)):
        prev = alt4_merged.iloc[idx - 1]
        if prev['daily_avg_vol_30d'] < bi.MIN_DAILY_VOLUME:
            continue
        if pd.isna(prev['close_1d']) or (prev['close_1d'] < prev['ema20_1d']) or (prev['ema20_1d'] < prev['ema50_1d']):
            continue
        if pd.isna(prev['return_7d']):
            continue
        if prev['low_1d'] > (prev['ema20_1d'] * 1.02):
            continue
        if not (bi.RSI_LONG_MIN <= prev['rsi14_1d'] <= bi.RSI_LONG_MAX):
            continue
        if not (prev['close_1d'] > prev['close_1d_prev']):
            continue
        if not (prev['cvd'] > 0):
            continue
        return idx
    return None


def craft_crash(alt4_raw, idx, stop_loss, entry_price):
    alt4_raw.loc[idx + 1, 'open'] = entry_price * 1.001
    alt4_raw.loc[idx + 1, 'high'] = entry_price * 1.002
    alt4_raw.loc[idx + 1, 'low'] = stop_loss * 0.99
    alt4_raw.loc[idx + 1, 'close'] = stop_loss * 0.995


def compute_stop_at_entry(alt4_merged, idx, entry_price):
    prev = alt4_merged.iloc[idx - 1]
    recent_10_lows = alt4_merged.iloc[max(0, idx - 10):idx]['low'].min()
    raw_stop = recent_10_lows - (1.5 * prev['atr14'])
    raw_dist_pct = (entry_price - raw_stop) / entry_price
    stop_dist_pct = min(max(raw_dist_pct, 0.040), 0.080)
    return entry_price * (1 - stop_dist_pct), stop_dist_pct
