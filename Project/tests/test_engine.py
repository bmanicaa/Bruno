import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
sys.path.insert(0, os.path.dirname(__file__))

import backtest_institucional as bi
import world_builder as wb

DEFAULT_PARAMS = {
    'risk_pct': 0.015,
    'max_positions': 4,
    'fee_pct': 0.00075,
    'entry_tf': '1d',
    'runner_mode': 'ema20_1d',
    'short_mode': 'breakout',
    'universe': 'alpha',
}


def run_window(world, start, end):
    return bi.run_portfolio_backtest(start, end, 100000.0, params=DEFAULT_PARAMS, preloaded=world)


def rebuild_world_with_alt(world, alt4_raw, alt1_raw):
    alt4_sorted, alt4_merged = wb.recompute_alt(alt4_raw, alt1_raw)
    coins = dict(world[3])
    coins['TESTUSDT'] = alt4_merged
    return (world[0], world[1], world[2], coins, world[4], world[5])


def alt_trades(res, trades):
    return [t for t in trades if t['symbol'] == 'TESTUSDT']


class TestPureFunctions:

    def test_indicator_math_ema_rsi_atr(self):
        n = 300
        times = wb.BASE_TIME + pd.to_timedelta(np.arange(n) * 4, unit='h')
        close = 100 + 0.1 * np.arange(n) + 2 * np.sin(np.arange(n) / 5)
        open_ = np.concatenate([[100], close[:-1]])
        df = pd.DataFrame({
            'open_time': times,
            'open': open_,
            'high': np.maximum(open_, close) * 1.001,
            'low': np.minimum(open_, close) * 0.999,
            'close': close,
            'volume': np.full(n, 1e6),
            'quote_volume': np.full(n, 1e6) * close,
            'taker_buy_base': 0.6 * np.full(n, 1e6),
        })
        out = bi.compute_indicators_4h(df)
        expected_ema20 = pd.Series(close).ewm(span=20, adjust=False).mean()
        assert np.isclose(out['ema20'].iloc[-1], expected_ema20.iloc[-1])
        assert out['rsi14'].dropna().between(0, 100).all()
        assert (out['atr14'].dropna() >= 0).all()
        assert (out['cvd'].dropna() > 0).all()
        assert out['ema20'].iloc[-1] > 0

    def test_vesting_cliff_rules(self):
        import datetime as dt
        assert bi.is_vesting_cliff('SUIUSDT', dt.datetime(2024, 1, 28))[0]
        assert not bi.is_vesting_cliff('SUIUSDT', dt.datetime(2024, 1, 10))[0]
        assert bi.is_vesting_cliff('ARBUSDT', dt.datetime(2024, 3, 16))[0]
        assert not bi.is_vesting_cliff('ARBUSDT', dt.datetime(2024, 3, 20))[0]
        assert bi.is_vesting_cliff('OPUSDT', dt.datetime(2024, 3, 26))[0]
        assert not bi.is_vesting_cliff('OPUSDT', dt.datetime(2024, 3, 10))[0]
        assert bi.is_vesting_cliff('TIAUSDT', dt.datetime(2024, 10, 26))[0]
        assert bi.is_vesting_cliff('WLDUSDT', dt.datetime(2024, 3, 20))[0]
        assert bi.is_vesting_cliff('GALAUSDT', dt.datetime(2024, 4, 20))[0]
        assert bi.is_vesting_cliff('ILVUSDT', dt.datetime(2024, 6, 25))[0]
        assert not bi.is_vesting_cliff('TESTUSDT', dt.datetime(2024, 3, 16))[0]

    def test_asset_class(self):
        assert bi._asset_class('BTCUSDT') == 'BTC'
        assert bi._asset_class('ETHUSDT') == 'ETH'
        assert bi._asset_class('SOLUSDT') == 'ALT'

    def test_last_funding_before_point_in_time(self):
        fr = pd.DataFrame({
            'fundingTime': pd.to_datetime(['2024-01-01 00:00:00', '2024-01-01 08:00:00',
                                           '2024-01-01 16:00:00']),
            'fundingRate': [0.0001, 0.0002, 0.0005],
        })
        fm = {'XUSDT': fr}
        assert bi._last_funding_before(fm, 'XUSDT', pd.Timestamp('2024-01-01 04:00:00')) == 0.0001
        assert bi._last_funding_before(fm, 'XUSDT', pd.Timestamp('2024-01-01 08:00:00')) == 0.0002
        assert bi._last_funding_before(fm, 'XUSDT', pd.Timestamp('2023-12-31 23:00:00')) == 0.0001
        assert bi._last_funding_before(fm, 'YUSDT', pd.Timestamp('2024-01-01 04:00:00')) == 0.0001

    def test_config_hash_deterministic(self):
        p1 = {'risk_pct': 0.015, 'universe': 'alpha'}
        p2 = {'universe': 'alpha', 'risk_pct': 0.015}
        p3 = {'risk_pct': 0.020, 'universe': 'alpha'}
        assert bi.config_hash(p1) == bi.config_hash(p2)
        assert bi.config_hash(p1) != bi.config_hash(p3)

    def test_funding_charge_long_formula(self):
        charge = bi.funding_charge(True, 1000.0, 1.0, 100.0, 110.0, 0.0001)
        assert np.isclose(charge, 1000.0 * (110.0 / 100.0) * 0.0001)

    def test_funding_charge_short_formula_correct(self):
        charge = bi.funding_charge(False, 1000.0, 1.0, 100.0, 110.0, 0.0001)
        assert np.isclose(charge, -(1000.0 * (110.0 / 100.0) * 0.0001))

    def test_funding_charge_short_receives_when_fr_positive(self):
        charge = bi.funding_charge(False, 1000.0, 1.0, 100.0, 90.0, 0.0001)
        assert np.isclose(charge, -(1000.0 * (90.0 / 100.0) * 0.0001))


class TestLookaheadRegression:

    def test_daily_merge_uses_previous_completed_day(self):
        d1 = pd.DataFrame({
            'open_time': pd.to_datetime(['2024-03-11 00:00:00', '2024-03-12 00:00:00']),
            'close': [100.0, 110.0],
            'high': [101.0, 111.0],
            'low': [99.0, 109.0],
        })
        d1 = bi.compute_indicators_1d(d1)
        d4 = pd.DataFrame({
            'open_time': pd.to_datetime(['2024-03-12 00:00:00', '2024-03-12 04:00:00']),
            'open': [110.0, 110.5],
            'high': [111.0, 111.5],
            'low': [109.0, 110.0],
            'close': [110.5, 111.0],
            'volume': [1e6, 1e6],
            'quote_volume': [1e6, 1e6],
            'taker_buy_base': [0.6e6, 0.6e6],
        })
        merged = wb._merge_daily_into_4h(d4, d1)
        assert merged.iloc[0]['close_1d'] == 100.0
        assert merged.iloc[1]['close_1d'] == 100.0


class TestMiniBacktest:

    def test_accounting_identity_and_equity(self):
        world = wb.build_world()
        start, end = wb.window_dates()
        res, trades, eq = run_window(world, start, end)
        assert np.isclose(res['net_profit_brl'], res['trading_pnl_net_brl'] + res['total_cash_yield_brl'], rtol=1e-6)
        assert np.isfinite(eq['capital']).all()
        assert 0.0 <= res['max_drawdown_pct'] <= 100.0
        assert res['win_rate_ci95_low_pct'] <= res['win_rate_pct'] <= res['win_rate_ci95_high_pct']
        assert len(trades) >= 3

    def test_entry_slippage_stop_clamp_and_sizing(self):
        world = wb.build_world()
        start, end = wb.window_dates()
        res, trades, eq = run_window(world, start, end)
        merged = world[3]['TESTUSDT']
        for t in trades:
            ts = pd.Timestamp(t['entry_date'])
            loc = merged.index.get_loc(ts)
            open_at_entry = merged.iloc[loc]['open']
            if t['direction'] == 'LONG':
                assert np.isclose(t['entry_price'], open_at_entry * 1.0005)
                lo, hi = 0.040, 0.080
            else:
                assert np.isclose(t['entry_price'], open_at_entry * 0.9995)
                lo, hi = 0.035, 0.080
            assert lo <= t['stop_dist_pct'] <= hi + 1e-9
            assert np.isclose(t['risk_brl'], t['allocated_capital'] * t['stop_dist_pct'], rtol=1e-6)

    def test_stop_loss_trade_math(self):
        world, alt4_raw, alt1_raw = wb.build_world_with_raws()
        alt4_merged = world[3]['TESTUSDT']
        idx = wb.find_long_candidate_idx(alt4_merged, world[3]['BTCUSDT'])
        assert idx is not None and idx % 6 == 1
        entry_price = alt4_merged.iloc[idx]['open'] * 1.0005
        stop_loss, sd = wb.compute_stop_at_entry(alt4_merged, idx, entry_price)
        alt4_raw = alt4_raw.copy()
        wb.craft_crash(alt4_raw, idx, stop_loss, entry_price)
        world = rebuild_world_with_alt(world, alt4_raw, alt1_raw)
        start, end = wb.window_dates()
        res, trades, eq = run_window(world, start, end)
        mine = [t for t in alt_trades(res, trades) if pd.Timestamp(t['entry_date']) == alt4_merged.index[idx]]
        assert len(mine) == 1
        t = mine[0]
        assert t['exit_reasons'][-1] == 'Stop Loss Inicial'
        r = t['pnl_brl'] / t['risk_brl']
        assert -1.10 < r < -0.95
        crash_open = alt4_raw.loc[idx + 1, 'open']
        expected_funding = t['allocated_capital'] * (crash_open / entry_price) * wb.FUNDING_RATE
        assert np.isclose(t['funding_paid'], expected_funding, rtol=1e-6)
        assert t['funding_paid'] > 0

    def test_breakeven_partial_runner(self):
        world, alt4_raw, alt1_raw = wb.build_world_with_raws()
        alt4_merged = world[3]['TESTUSDT']
        idx = wb.find_long_candidate_idx(alt4_merged, world[3]['BTCUSDT'])
        assert idx is not None
        entry_price = alt4_merged.iloc[idx]['open'] * 1.0005
        stop_loss, sd = wb.compute_stop_at_entry(alt4_merged, idx, entry_price)
        stop_dist = entry_price - stop_loss
        be_trigger = entry_price + 2 * stop_dist

        alt4_raw = alt4_raw.copy()
        alt4_raw.loc[idx + 1, 'open'] = entry_price * 1.001
        alt4_raw.loc[idx + 1, 'low'] = entry_price * 0.995
        alt4_raw.loc[idx + 1, 'high'] = be_trigger * 1.01
        alt4_raw.loc[idx + 1, 'close'] = be_trigger * 1.005

        world = rebuild_world_with_alt(world, alt4_raw, alt1_raw)
        alt4_merged = world[3]['TESTUSDT']
        alt4_raw.loc[idx + 2, 'open'] = be_trigger * 1.005
        alt4_raw.loc[idx + 2, 'low'] = entry_price * 1.005
        alt4_raw.loc[idx + 2, 'high'] = be_trigger * 1.02
        alt4_raw.loc[idx + 2, 'close'] = be_trigger * 1.01

        world = rebuild_world_with_alt(world, alt4_raw, alt1_raw)
        alt4_merged = world[3]['TESTUSDT']
        for k in range(3, 13):
            alt4_raw.loc[idx + k, 'open'] = entry_price * 1.06
            alt4_raw.loc[idx + k, 'low'] = entry_price * 1.05
            alt4_raw.loc[idx + k, 'high'] = entry_price * 1.07
            alt4_raw.loc[idx + k, 'close'] = entry_price * 1.06

        exit_day = pd.Timestamp(alt4_merged.index[idx]) + pd.Timedelta(days=1)
        day_mask = alt1_raw['open_time'] == exit_day.normalize()
        if day_mask.any():
            alt1_raw.loc[day_mask, 'close'] = entry_price * 1.30

        world = rebuild_world_with_alt(world, alt4_raw, alt1_raw)
        alt4_merged = world[3]['TESTUSDT']
        ema_at_exit = alt4_merged.iloc[idx + 13]['ema20_1d']
        exit_close = ema_at_exit * 0.995
        alt4_raw.loc[idx + 13, 'open'] = entry_price * 1.06
        alt4_raw.loc[idx + 13, 'low'] = max(exit_close * 0.998, entry_price * 1.002)
        alt4_raw.loc[idx + 13, 'high'] = entry_price * 1.07
        alt4_raw.loc[idx + 13, 'close'] = exit_close

        world = rebuild_world_with_alt(world, alt4_raw, alt1_raw)
        start, end = wb.window_dates()
        res, trades, eq = run_window(world, start, end)
        mine = [t for t in alt_trades(res, trades) if pd.Timestamp(t['entry_date']) == alt4_merged.index[idx]]
        assert len(mine) == 1
        t = mine[0]
        assert t['exit_reasons'] == ['Parcial Segurança (2.0R / 50%)', 'Trailing Runner 50% (ema20_1d)']
        assert np.isclose(t['exit_prices'][0], be_trigger)
        assert np.isclose(t['stop_final'], entry_price * 1.001)
        assert np.isclose(t['remaining_pct'], 0.5)
        r = t['pnl_brl'] / t['risk_brl']
        assert 0.8 < r < 1.9

    def test_time_stop(self):
        world, alt4_raw, alt1_raw = wb.build_world_with_raws()
        alt4_merged = world[3]['TESTUSDT']
        idx = wb.find_long_candidate_idx(alt4_merged, world[3]['BTCUSDT'])
        assert idx is not None
        entry_price = alt4_merged.iloc[idx]['open'] * 1.0005

        alt4_raw = alt4_raw.copy()
        for k in range(1, bi.TIME_STOP_CANDLES + 5):
            alt4_raw.loc[idx + k, 'open'] = entry_price * 1.0005
            alt4_raw.loc[idx + k, 'high'] = entry_price * 1.003
            alt4_raw.loc[idx + k, 'low'] = entry_price * 0.997
            alt4_raw.loc[idx + k, 'close'] = entry_price * 1.0005

        world = rebuild_world_with_alt(world, alt4_raw, alt1_raw)
        start, end = wb.window_dates()
        res, trades, eq = run_window(world, start, end)
        mine = [t for t in alt_trades(res, trades) if pd.Timestamp(t['entry_date']) == alt4_merged.index[idx]]
        assert len(mine) == 1
        t = mine[0]
        assert t['exit_reasons'][-1] == 'Time-Stop (21d)'
        assert abs(t['pnl_brl'] / t['risk_brl']) < 0.35

    def test_circuit_breaker_halves_risk_after_3_losses(self):
        world, alt4_raw, alt1_raw = wb.build_world_with_raws()
        alt4_raw = alt4_raw.copy()
        scan_start = wb.WINDOW_START_IDX
        entries = []
        for _ in range(5):
            alt4_merged = world[3]['TESTUSDT']
            idx = wb.find_long_candidate_idx(alt4_merged, world[3]['BTCUSDT'], start_idx=scan_start)
            if idx is None:
                break
            entry_price = alt4_merged.iloc[idx]['open'] * 1.0005
            stop_loss, sd = wb.compute_stop_at_entry(alt4_merged, idx, entry_price)
            wb.craft_crash(alt4_raw, idx, stop_loss, entry_price)
            world = rebuild_world_with_alt(world, alt4_raw, alt1_raw)
            alt4_merged = world[3]['TESTUSDT']
            entry2 = alt4_merged.iloc[idx + 1]['open'] * 1.0005
            stop2, sd2 = wb.compute_stop_at_entry(alt4_merged, idx + 1, entry2)
            alt4_raw.loc[idx + 2, 'open'] = entry2 * 1.001
            alt4_raw.loc[idx + 2, 'high'] = entry2 * 1.002
            alt4_raw.loc[idx + 2, 'low'] = stop2 * 0.99
            alt4_raw.loc[idx + 2, 'close'] = stop2 * 0.995
            world = rebuild_world_with_alt(world, alt4_raw, alt1_raw)
            entries.append(idx)
            scan_start = idx + 16

        assert len(entries) >= 4
        start, end = wb.window_dates()
        res, trades, eq = run_window(world, start, end)
        mine = sorted([t for t in alt_trades(res, trades)], key=lambda t: t['entry_date'])
        assert len(mine) >= 6
        assert all(t['pnl_brl'] < 0 for t in mine[:6])
        r1, r2 = mine[1]['risk_brl'] / mine[0]['risk_brl'], mine[2]['risk_brl'] / mine[1]['risk_brl']
        r5 = mine[4]['risk_brl'] / mine[3]['risk_brl']
        assert 0.9 < r1 < 1.05 and 0.9 < r2 < 1.05
        assert 0.4 < r5 < 0.6
