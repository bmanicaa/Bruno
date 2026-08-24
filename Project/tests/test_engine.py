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


class TestValidationIntegrity:
    """Blindagens da regua estatistica (Fase A, 24/08/2026).

    Estes testes cobrem a camada que decide se uma estrategia pode receber
    dinheiro real. Um bug aqui nao quebra nada visivelmente — apenas aprova o
    que deveria reprovar, que e o modo de falha mais caro do projeto.
    """

    def test_sharpe_trading_exclui_cash_yield(self):
        """Uma carteira 100% parada no caixa tem Sharpe alto e Sharpe de trading ~0."""
        import statistical_validation as sv

        n = 2000
        # Equity crescendo exatamente ao cash yield: zero trades, zero risco.
        equity = 100000.0 * (1 + sv.CASH_YIELD_PER_BAR) ** np.arange(n)

        bruto = sv._window_returns(equity.tolist(), excess=False)
        liquido = sv._window_returns(equity.tolist(), excess=True)

        sharpe_bruto = bruto.mean() / (bruto.std() + 1e-12) * np.sqrt(sv.ANNUAL_FACTOR)
        assert sharpe_bruto > 100, 'poupanca pura deve exibir Sharpe absurdo na base bruta'
        assert abs(liquido.mean()) < 1e-12, 'o excesso sobre o cash yield deve ser ~zero'

    def test_dsr_nao_confunde_escala_anual_com_barras(self):
        """O Z do DSR nao pode escalar com sqrt(2190) por erro de unidade.

        Era este o bug: sr_obs chegava anualizado e n_obs contava barras de 4h,
        multiplicando o Z por ~46.8 e devolvendo p=1e-12 para configs sem edge.
        """
        import statistical_validation as sv

        rng = np.random.default_rng(7)
        rets = rng.normal(0.0, 0.01, 7500)
        # Sharpe anualizado modesto, tipico do projeto.
        sr_obs = 1.2
        sr_trials = [0.3, 0.5, 0.8, 1.0, 1.2, 0.4, 0.9, 1.1]

        ds = sv.deflated_sharpe(sr_obs, sr_trials, rets)
        assert ds is not None
        # Com Sharpe anualizado 1.2 e um piso de ruido da mesma ordem, o resultado
        # tem de ser inconclusivo — nao "certeza de 12 casas decimais".
        assert ds['p_value'] > 0.01, f"p={ds['p_value']:.2e} — escala do DSR voltou a quebrar"
        assert abs(ds['sr_obs_per_bar'] * np.sqrt(sv.ANNUAL_FACTOR) - sr_obs) < 1e-9

    def test_dsr_ainda_detecta_edge_real(self):
        """A correcao nao pode cegar o teste: um Sharpe genuinamente alto passa."""
        import statistical_validation as sv

        rng = np.random.default_rng(11)
        rets = rng.normal(0.0, 0.01, 7500)
        ds = sv.deflated_sharpe(4.0, [0.3, 0.5, 0.8, 1.0, 1.2, 0.4, 0.9, 1.1], rets)
        assert ds['p_value'] < 0.10, 'Sharpe anualizado 4.0 deveria passar no DSR'

    def test_bootstrap_sinaliza_amostra_insuficiente(self):
        """10 trades nao podem devolver p-valor confiante sem aviso."""
        import statistical_validation as sv

        trades = [{'pnl_brl': 1000.0 * (1 if i % 3 else -1), 'risk_brl': 750.0}
                  for i in range(10)]
        bt = sv.bootstrap_trade_stats(trades, n_iter=500, block_len=8)
        assert bt['insufficient_sample'] is True
        assert bt['block_len'] <= max(1, len(trades) // 3), 'bloco maior que n/3 colapsa a variancia'

    def test_experimentos_contaminados_saem_do_universo_dsr(self):
        """Configs pre-V2.3 nao podem contar como tentativa nem virar baseline."""
        import statistical_validation as sv

        trials = sv.collect_all_experiments()
        hashes = [t['hash'] for t in trials]
        assert len(hashes) == len(set(hashes)), 'config_hash duplicado inflaria n_trials'
        # b415fc06 e o pre-V2.3 de maior PnL (+R$80k) — o exato falso positivo que
        # uma sessao futura escolheria ao ordenar experimentos por resultado.
        assert 'b415fc06' not in hashes
        assert '9ea2dff4' in hashes, 'a versao corrigida da baseline deve permanecer'

    def test_trend_bh_falha_alto_com_ativo_ausente(self):
        """Ativo sem dados deve estourar, nunca ser descartado em silencio."""
        import backtest_trend_bh as tb

        with pytest.raises(FileNotFoundError, match='MOEDAINEXISTENTE'):
            tb.run_trend('2023-01-01', '2023-06-01',
                         {'assets': ['MOEDAINEXISTENTE']},
                         preloaded=(pd.DataFrame(), {}, {}, []))

    def test_cash_yield_nao_diverge_entre_motor_e_validador(self):
        """A taxa livre de risco esta escrita em dois lugares — travar o par.

        Se alguem mudar o cash yield do motor sem mudar o validador, o Sharpe de
        trading passa a subtrair a taxa errada e volta a medir parte da poupanca
        como se fosse edge. O teste falha antes que isso aconteca em silencio.
        """
        import statistical_validation as sv

        esperado = bi.CASH_YIELD_ANNUAL / 2190.0
        assert abs(sv.CASH_YIELD_PER_BAR - esperado) < 1e-15, (
            f'motor usa {bi.CASH_YIELD_ANNUAL:.4f} a.a., validador usa '
            f'{sv.CASH_YIELD_PER_BAR * 2190.0:.4f} a.a.')
        assert sv.ANNUAL_FACTOR == 2190.0


class TestMacroFilter:
    """Porta macro opcional (Fase B, item 1: hibrido trend + swing).

    A hipotese era "so operar swing com o BTC acima da EMA200 diaria". Os testes
    abaixo travam duas coisas: (a) a porta e opcional de verdade — desligada, o
    motor roda bit a bit como antes; (b) o modo ema200d e REDUNDANTE para longs,
    porque o regime bull ja exige close >= EMA200. Este segundo teste existe para
    impedir que uma sessao futura "reimplemente" o filtro achando que e novo.
    """

    def _daily(self, closes, start='2019-09-01'):
        times = pd.to_datetime(start) + pd.to_timedelta(np.arange(len(closes)), unit='D')
        close = np.asarray(closes, dtype=float)
        df = pd.DataFrame({
            'open_time': times,
            'open': close,
            'high': close * 1.001,
            'low': close * 0.999,
            'close': close,
        })
        return bi.compute_indicators_1d(df).sort_values('open_time')

    def test_off_nao_altera_nada(self):
        """macro_filter='off' deve abrir a porta em todos os dias."""
        d = self._daily(100 + np.arange(400) * 0.1)
        gate = bi.build_macro_gate(d, 'off')
        assert len(gate) == len(d)
        assert all(gate.values())
        # confirm_days nao pode ligar sozinho quando o filtro esta desligado.
        assert all(bi.build_macro_gate(d, 'off', confirm_days=7).values())

    def test_ema200d_fecha_a_porta_abaixo_da_media(self):
        subida = 100 * np.exp(np.cumsum(np.full(400, 0.004)))
        queda = subida[-1] * np.exp(np.cumsum(np.full(200, -0.006)))
        d = self._daily(np.concatenate([subida, queda]))
        gate = bi.build_macro_gate(d, 'ema200d')
        flags = np.array([gate[t] for t in d['open_time']])
        acima = (d['close'] >= d['ema200_1d']).to_numpy()
        assert (flags == acima).all()
        assert not flags[-1], 'no fim da queda o BTC esta abaixo da EMA200'

    def test_ema200d_e_redundante_para_longs(self):
        """O regime bull ja exige close >= EMA200 — o filtro nao pode mudar trade algum.

        Se este teste falhar, ou o regime bull mudou, ou a porta passou a vetar
        entradas que o motor ja permitia. Nos dois casos e preciso reler o
        analises.md antes de tratar o resultado como um edge novo.
        """
        world = wb.build_world()
        start, end = wb.window_dates()
        base = dict(DEFAULT_PARAMS, short_mode='none')
        _, trades_off, _ = bi.run_portfolio_backtest(start, end, 100000.0, params=base, preloaded=world)
        _, trades_gate, _ = bi.run_portfolio_backtest(
            start, end, 100000.0, params=dict(base, macro_filter='ema200d'), preloaded=world)

        assert len(trades_off) > 0, 'mundo sintetico sem trades nao testa nada'
        assert len(trades_off) == len(trades_gate)
        for a, b in zip(trades_off, trades_gate):
            assert a['entry_date'] == b['entry_date'] and a['symbol'] == b['symbol']
            assert abs(a['pnl_brl'] - b['pnl_brl']) < 1e-9

    def test_confirm_days_exige_persistencia(self):
        """A porta so abre depois de N fechamentos diarios seguidos com a condicao."""
        d = self._daily(100 * np.exp(np.cumsum(np.full(500, 0.003))))
        crua = bi.build_macro_gate(d, 'ema200d')
        firme = bi.build_macro_gate(d, 'ema200d', confirm_days=7)

        dias = list(d['open_time'])
        assert not any(firme[t] and not crua[t] for t in dias), 'confirmacao nao pode abrir porta fechada'
        primeira_crua = next(i for i, t in enumerate(dias) if crua[t])
        primeira_firme = next(i for i, t in enumerate(dias) if firme[t])
        assert primeira_firme == primeira_crua + 6, 'a porta confirmada abre exatamente 7 dias depois'

    def test_semanal_fica_fechado_durante_aquecimento(self):
        """Sem 50 semanas de historico a EMA semanal nao decide nada — porta fechada."""
        d = self._daily(100 * np.exp(np.cumsum(np.full(700, 0.003))))
        gate = bi.build_macro_gate(d, 'ema50w')
        flags = np.array([gate[t] for t in d['open_time']])
        # Contagem em semanas fechadas, nao em dias: a primeira semana do arquivo
        # costuma ser parcial e nao vale como observacao.
        semana = d['open_time'].dt.to_period('W')
        ordem = semana.map({w: i for i, w in enumerate(sorted(semana.unique()))}).to_numpy()
        assert not flags[ordem < 50].any(), 'porta semanal abriu antes de 50 semanas fechadas'
        assert flags.any(), 'em tendencia de alta a porta precisa abrir depois do aquecimento'

    def test_semanal_nao_olha_o_futuro(self):
        """A decisao de um dia so pode usar semanas ja fechadas.

        Truncar a serie no dia D nao pode mudar o valor da porta em D — se mudar,
        alguma barra futura estava entrando no calculo.
        """
        d = self._daily(100 * np.exp(np.cumsum(np.concatenate([
            np.full(500, 0.004), np.full(300, -0.005)]))))
        completo = bi.build_macro_gate(d, 'ema50w')
        for corte in (560, 640, 720):
            parcial = bi.build_macro_gate(d.iloc[:corte].copy(), 'ema50w')
            alvo = d['open_time'].iloc[corte - 1]
            assert parcial[alvo] == completo[alvo], f'porta semanal mudou ao truncar em {alvo}'

    def test_modo_invalido_falha_alto(self):
        d = self._daily(100 + np.arange(300) * 0.1)
        with pytest.raises(ValueError, match='macro_filter desconhecido'):
            bi.build_macro_gate(d, 'ema200_mensal')
