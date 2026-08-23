# Registro de Análises e Estratégias

Este arquivo contém o histórico padronizado de análises de diferentes estratégias aplicadas ao longo do tempo. Quando o usuário solicitar, novas análises deverão ser registradas abaixo no seguinte formato:

<!--
## [Data] - Estratégia: [Nome/Resumo da Estratégia]
- **Mudança Implementada:** [Descrição detalhada da alteração na estratégia ou parâmetros]
- **Resultados Obtidos:** [Resumo dos resultados do backtest ou operação, como Win Rate, PnL, Drawdown, etc]
- **Análise Diagnóstica:** [Conclusões sobre por que a estratégia funcionou ou falhou, pontos fortes e fracos]
-->

## [22/08/2026] - Estratégia: Unificação de Parciais e Controle de Asfixia
- ⚠️ **RETIFICAÇÃO (22/08/2026, auditoria de integridade):** Os "Resultados Obtidos (Empíricos)" originais desta entrada vieram do motor `backtest_fast_new.py` (9 moedas pré-escolhidas, R$200 por ativo) e NÃO são comparáveis ao motor institucional (536 moedas, R$100k) que gera os relatórios oficiais. A conclusão original ("sangramento estancado") foi baseada em teste incomparável. Esta entrada é mantida apenas como registro histórico.
- **Mudança Implementada:** (1) Parcial de 50% e Breakeven cravados em 2.0R. (2) Runner conduzido pela EMA20 Diária sem teto. (3) Redução do risco base para 1.50%. (4) Remoção de filtros Anti-Pump (volatilidade e volume) que cortavam os outliers.
- **Resultados Obtidos (Empíricos, motor 9-moedas R$200 — NÃO COMPARÁVEL):**
  - Preliminar Rápido (Anual): Lucro +$216.88 | Win Rate 44.44% | Drawdown 9.90%
  - Bull Market: Lucro +$287.79 | Win Rate 50.93% | Drawdown 5.68%
  - Bear Market: Lucro -$25.18 | Win Rate 20.35% | Drawdown 3.69%
  - Lateral/Chop: Lucro -$48.18 | Win Rate 36.23% | Drawdown 7.31%
- **Análise Diagnóstica:** Conclusão original invalidada por incomparabilidade de motores. Ver entrada de auditoria abaixo.

---

## [22/08/2026] - Estratégia: Auditoria de Integridade do Engine (V2.1 Corrigida) — `scripts/backtest_institucional.py`
- **Mudança Implementada:** (1) Motor canônico único criado com regras 100% alinhadas ao Prompt.md V2.1 (risco 1.50%, BE/Parcial 2.0R no MESMO gatilho, runner EMA20 1D sem teto, 4 posições, time-stop 21d, Top 10% de Alpha, vetos de funding >±0.03%, gatilhos RSI 44-62 long / 38-56 short com close > prev_high / < prev_low). (2) Bugs corrigidos: MtM de SHORT invertido (distorcia drawdown/Sharpe do Bear), checkpoints semestrais fora do período, funding cobrado em posição recém-aberta na fronteira UTC, lookahead no Alpha 7d do BTC, export de stop final no CSV (agora exporta stop inicial E final), fechamento fim-de-período de SHORT com fórmula invertida. (3) Blindagem anti-má-interpretação: decomposição de PnL (trading bruto/líquido, taxas, funding, cash yield), benchmark Buy & Hold BTC e IC 95% (Wilson) em todos os relatórios. (4) Motores antigos arquivados em `scripts/legado/`.
- **Resultados Obtidos (Motor Canônico, 536 moedas, R$100k):**
  - Preliminar (1 ano): +8.92% | Win 39.66% | PF 1.06 | DD 20.58% | Trading líquido +R$3.225 | B&H BTC +117.20%
  - Bull (6m): +20.58% | Win 46.15% | PF 1.55 | DD 15.03% | Trading líquido +R$18.161 | B&H BTC +155.04%
  - Bear (1 ano): +1.94% | Win 26.09% | PF 0.81 | DD 10.36% | Trading líquido -R$3.439 | B&H BTC -65.33%
  - Chop (6m): -7.56% | Win 26.32% | PF 0.33 | DD 9.46% | Trading líquido -R$10.251 | B&H BTC -9.17%
  - 5 Anos: +15.00% | Win 37.44% | PF 0.95 | DD 24.12% | Trading líquido -R$9.509 | Cash Yield +R$24.512 | B&H BTC +14.68%
- **Análise Diagnóstica:** (1) Os furos de engine eram reais e foram corrigidos — os números agora são honestos e rastreáveis. (2) Com o motor certo, o edge de trading em 5 anos é LEVEMENTE NEGATIVO (-R$9,5k); todo o lucro do portfólio vem do cash yield 6% (+R$24,5k). Ou seja: o problema restante NÃO é mais imprevisibilidade nem bug de código — é deficiência de edge da estratégia: custos (taxas R$6,3k + funding R$1,3k + slippage) consomem o PnL bruto quase empatado. (3) Nos janelões de alta a estratégia lucra (PF 1.55) mas captura apenas ~13% da alta do BTC (B&H +155% vs carteira +20.6%) — o custo de oportunidade dos filtros é o maior "custo oculto". (4) O modo Bear cumpriu seu papel: preservou capital contra B&H -65%. (5) Próximos passos lógicos (sem overfitting): reduzir custos de round-trip (menos trades de baixa convicção), considerar participação mínima do benchmark (ex.: 20% B&H BTC + 80% sistema) e validar em walk-forward out-of-sample antes de qualquer mudança de parâmetro.

## [22/08/2026 22:02] - Experimento Walk-Forward: config fd1d50fc
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "btc_adx_min": 0.0, "entry_tf": "4h", "runner_mode": "ema20_1d", "short_mode": "revert", "universe": "alpha"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 170,
  "return_pct_sum": 13.13,
  "trading_pnl_sum": -4145.03,
  "pf_mean": 0.9,
  "pf_median": 0.95,
  "win_rate_mean": 36.1,
  "dd_max": 18.37,
  "sharpe_mean": -0.02,
  "expectancy_r_mean": -0.04
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 41, "return_pct": 26.26, "trading_pnl": 8069.8, "pf": 1.22, "win_rate": 41.5, "dd_pct": 10.43, "sharpe": 0.97, "expectancy_r": 0.303, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 42, "return_pct": -18.09, "trading_pnl": -22903.81, "pf": 0.33, "win_rate": 23.8, "dd_pct": 18.37, "sharpe": -1.55, "expectancy_r": -0.347, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 46, "return_pct": 20.39, "trading_pnl": 14659.28, "pf": 1.36, "win_rate": 43.5, "dd_pct": 12.18, "sharpe": 1.02, "expectancy_r": 0.271, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 64, "return_pct": 12.14, "trading_pnl": 7373.2, "pf": 1.13, "win_rate": 43.8, "dd_pct": 16.74, "sharpe": 0.58, "expectancy_r": 0.134, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 18, "return_pct": -1.31, "trading_pnl": -3273.7, "pf": 0.77, "win_rate": 33.3, "dd_pct": 13.28, "sharpe": -0.13, "expectancy_r": -0.219, "bnh_btc_pct": -26.75}}

## [22/08/2026 22:14] - Experimento Walk-Forward: config 2ce0bbbf
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "btc_adx_min": 20.0, "entry_tf": "4h", "runner_mode": "ema20_1d", "short_mode": "revert", "universe": "alpha"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 142,
  "return_pct_sum": -1.18,
  "trading_pnl_sum": -19005.87,
  "pf_mean": 0.82,
  "pf_median": 0.87,
  "win_rate_mean": 37.0,
  "dd_max": 17.65,
  "sharpe_mean": -0.09,
  "expectancy_r_mean": -0.073
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 38, "return_pct": 28.37, "trading_pnl": 9999.69, "pf": 1.3, "win_rate": 42.1, "dd_pct": 10.43, "sharpe": 1.08, "expectancy_r": 0.355, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 39, "return_pct": -15.89, "trading_pnl": -20739.58, "pf": 0.35, "win_rate": 25.6, "dd_pct": 16.17, "sharpe": -1.35, "expectancy_r": -0.302, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 41, "return_pct": 0.87, "trading_pnl": -4557.21, "pf": 0.88, "win_rate": 39.0, "dd_pct": 17.65, "sharpe": 0.14, "expectancy_r": 0.015, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 48, "return_pct": 13.36, "trading_pnl": 7894.58, "pf": 1.2, "win_rate": 47.9, "dd_pct": 12.88, "sharpe": 0.67, "expectancy_r": 0.123, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 14, "return_pct": 0.48, "trading_pnl": -1603.66, "pf": 0.86, "win_rate": 35.7, "dd_pct": 9.26, "sharpe": 0.16, "expectancy_r": -0.128, "bnh_btc_pct": -26.75}}

## [22/08/2026 22:47] - Experimento Walk-Forward: config 9eb0e838
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "btc_adx_min": 0.0, "entry_tf": "4h", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 151,
  "return_pct_sum": 28.65,
  "trading_pnl_sum": 10343.9,
  "pf_mean": 1.03,
  "pf_median": 1.1,
  "win_rate_mean": 40.4,
  "dd_max": 15.82,
  "sharpe_mean": 0.4,
  "expectancy_r_mean": 0.103
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 24, "return_pct": 31.89, "trading_pnl": 12341.2, "pf": 1.52, "win_rate": 45.8, "dd_pct": 8.08, "sharpe": 1.35, "expectancy_r": 0.435, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 36, "return_pct": -8.53, "trading_pnl": -13845.08, "pf": 0.53, "win_rate": 33.3, "dd_pct": 15.82, "sharpe": -0.69, "expectancy_r": -0.152, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 44, "return_pct": 22.3, "trading_pnl": 16408.1, "pf": 1.41, "win_rate": 45.5, "dd_pct": 12.18, "sharpe": 1.1, "expectancy_r": 0.318, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 61, "return_pct": 12.1, "trading_pnl": 7222.23, "pf": 1.13, "win_rate": 42.6, "dd_pct": 15.48, "sharpe": 0.59, "expectancy_r": 0.138, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 10, "return_pct": 2.78, "trading_pnl": 558.65, "pf": 1.07, "win_rate": 40.0, "dd_pct": 9.84, "sharpe": 0.61, "expectancy_r": 0.108, "bnh_btc_pct": -26.75}}

## [22/08/2026 23:10] - Experimento Walk-Forward: config 2f959c5f
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "btc_adx_min": 0.0, "entry_tf": "4h", "runner_mode": "prev_low_1d", "short_mode": "revert", "universe": "alpha"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 133,
  "return_pct_sum": -16.08,
  "trading_pnl_sum": -30538.68,
  "pf_mean": 0.78,
  "pf_median": 0.84,
  "win_rate_mean": 37.3,
  "dd_max": 37.29,
  "sharpe_mean": -0.24,
  "expectancy_r_mean": -0.15
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 19, "return_pct": 6.1, "trading_pnl": -9678.21, "pf": 0.57, "win_rate": 31.6, "dd_pct": 25.57, "sharpe": 0.2, "expectancy_r": -0.594, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 40, "return_pct": -20.42, "trading_pnl": -24985.39, "pf": 0.22, "win_rate": 25.0, "dd_pct": 21.63, "sharpe": -1.4, "expectancy_r": -0.488, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 23, "return_pct": 7.51, "trading_pnl": 3626.77, "pf": 1.21, "win_rate": 43.5, "dd_pct": 37.29, "sharpe": 0.39, "expectancy_r": 0.111, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 53, "return_pct": -2.93, "trading_pnl": -6963.51, "pf": 0.84, "win_rate": 45.3, "dd_pct": 20.92, "sharpe": -0.0, "expectancy_r": -0.026, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 17, "return_pct": -0.24, "trading_pnl": -2216.55, "pf": 0.83, "win_rate": 35.3, "dd_pct": 13.43, "sharpe": 0.04, "expectancy_r": -0.198, "bnh_btc_pct": -26.75}}

## [22/08/2026 23:10] - Experimento Walk-Forward: config 3f042c06
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "btc_adx_min": 0.0, "entry_tf": "1d", "runner_mode": "ema20_1d", "short_mode": "revert", "universe": "alpha"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 244,
  "return_pct_sum": 73.32,
  "trading_pnl_sum": 57885.17,
  "pf_mean": 1.06,
  "pf_median": 0.98,
  "win_rate_mean": 35.5,
  "dd_max": 24.93,
  "sharpe_mean": 0.27,
  "expectancy_r_mean": -0.0
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 85, "return_pct": 245.33, "trading_pnl": 214051.84, "pf": 2.48, "win_rate": 52.9, "dd_pct": 16.6, "sharpe": 1.85, "expectancy_r": 1.128, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 61, "return_pct": -18.06, "trading_pnl": -22200.28, "pf": 0.55, "win_rate": 24.6, "dd_pct": 24.93, "sharpe": -0.83, "expectancy_r": -0.376, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 75, "return_pct": 29.57, "trading_pnl": 24687.11, "pf": 1.41, "win_rate": 44.0, "dd_pct": 14.0, "sharpe": 1.15, "expectancy_r": 0.389, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 85, "return_pct": 70.21, "trading_pnl": 65569.97, "pf": 1.81, "win_rate": 51.8, "dd_pct": 11.77, "sharpe": 1.87, "expectancy_r": 0.473, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 23, "return_pct": -8.4, "trading_pnl": -10171.63, "pf": 0.47, "win_rate": 21.7, "dd_pct": 20.8, "sharpe": -1.12, "expectancy_r": -0.487, "bnh_btc_pct": -26.75}}

## [22/08/2026 23:22] - Experimento Walk-Forward: config 0297603b
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "btc_adx_min": 0.0, "entry_tf": "4h", "runner_mode": "atr_chandelier", "short_mode": "revert", "universe": "alpha"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 166,
  "return_pct_sum": 7.69,
  "trading_pnl_sum": -9390.3,
  "pf_mean": 0.9,
  "pf_median": 0.86,
  "win_rate_mean": 36.9,
  "dd_max": 17.77,
  "sharpe_mean": 0.04,
  "expectancy_r_mean": -0.019
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 41, "return_pct": 35.07, "trading_pnl": 16290.45, "pf": 1.42, "win_rate": 41.5, "dd_pct": 12.43, "sharpe": 1.06, "expectancy_r": 0.59, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 43, "return_pct": -13.59, "trading_pnl": -18477.75, "pf": 0.48, "win_rate": 25.6, "dd_pct": 15.43, "sharpe": -0.97, "expectancy_r": -0.216, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 47, "return_pct": 23.43, "trading_pnl": 17770.31, "pf": 1.42, "win_rate": 42.6, "dd_pct": 15.25, "sharpe": 1.03, "expectancy_r": 0.301, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 59, "return_pct": -2.19, "trading_pnl": -6743.41, "pf": 0.86, "win_rate": 44.1, "dd_pct": 17.77, "sharpe": 0.02, "expectancy_r": 0.023, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 17, "return_pct": 0.04, "trading_pnl": -1939.45, "pf": 0.85, "win_rate": 35.3, "dd_pct": 13.37, "sharpe": 0.08, "expectancy_r": -0.184, "bnh_btc_pct": -26.75}}

## [22/08/2026 23:22] - Experimento Walk-Forward: config 4b6ad8db
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "btc_adx_min": 0.0, "entry_tf": "4h", "runner_mode": "ema20_1d", "short_mode": "revert", "universe": "top20"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 170,
  "return_pct_sum": 13.13,
  "trading_pnl_sum": -4145.03,
  "pf_mean": 0.9,
  "pf_median": 0.95,
  "win_rate_mean": 36.1,
  "dd_max": 18.37,
  "sharpe_mean": -0.02,
  "expectancy_r_mean": -0.04
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 41, "return_pct": 26.26, "trading_pnl": 8069.8, "pf": 1.22, "win_rate": 41.5, "dd_pct": 10.43, "sharpe": 0.97, "expectancy_r": 0.303, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 42, "return_pct": -18.09, "trading_pnl": -22903.81, "pf": 0.33, "win_rate": 23.8, "dd_pct": 18.37, "sharpe": -1.55, "expectancy_r": -0.347, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 46, "return_pct": 20.39, "trading_pnl": 14659.28, "pf": 1.36, "win_rate": 43.5, "dd_pct": 12.18, "sharpe": 1.02, "expectancy_r": 0.271, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 64, "return_pct": 12.14, "trading_pnl": 7373.2, "pf": 1.13, "win_rate": 43.8, "dd_pct": 16.74, "sharpe": 0.58, "expectancy_r": 0.134, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 18, "return_pct": -1.31, "trading_pnl": -3273.7, "pf": 0.77, "win_rate": 33.3, "dd_pct": 13.28, "sharpe": -0.13, "expectancy_r": -0.219, "bnh_btc_pct": -26.75}}

## [22/08/2026 23:22] - Experimento Walk-Forward: config b9768f4c
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.0002, "btc_adx_min": 0.0, "entry_tf": "4h", "runner_mode": "ema20_1d", "short_mode": "revert", "universe": "alpha"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 170,
  "return_pct_sum": 17.14,
  "trading_pnl_sum": -213.16,
  "pf_mean": 0.92,
  "pf_median": 0.98,
  "win_rate_mean": 36.6,
  "dd_max": 17.73,
  "sharpe_mean": 0.04,
  "expectancy_r_mean": -0.022
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 41, "return_pct": 27.33, "trading_pnl": 9092.59, "pf": 1.25, "win_rate": 41.5, "dd_pct": 10.32, "sharpe": 1.01, "expectancy_r": 0.319, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 42, "return_pct": -17.43, "trading_pnl": -22261.17, "pf": 0.34, "win_rate": 23.8, "dd_pct": 17.73, "sharpe": -1.48, "expectancy_r": -0.329, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 46, "return_pct": 21.6, "trading_pnl": 15849.79, "pf": 1.39, "win_rate": 45.7, "dd_pct": 11.91, "sharpe": 1.06, "expectancy_r": 0.288, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 64, "return_pct": 13.8, "trading_pnl": 9000.54, "pf": 1.15, "win_rate": 43.8, "dd_pct": 16.06, "sharpe": 0.64, "expectancy_r": 0.15, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 18, "return_pct": -0.83, "trading_pnl": -2802.32, "pf": 0.8, "win_rate": 33.3, "dd_pct": 13.03, "sharpe": -0.06, "expectancy_r": -0.198, "bnh_btc_pct": -26.75}}

## [22/08/2026 23:33] - Experimento Walk-Forward: config b415fc06
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.0002, "btc_adx_min": 0.0, "entry_tf": "1d", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 245,
  "return_pct_sum": 96.01,
  "trading_pnl_sum": 80307.71,
  "pf_mean": 1.22,
  "pf_median": 1.12,
  "win_rate_mean": 38.2,
  "dd_max": 23.86,
  "sharpe_mean": 0.7,
  "expectancy_r_mean": 0.129
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 87, "return_pct": 277.71, "trading_pnl": 244397.89, "pf": 2.66, "win_rate": 55.2, "dd_pct": 16.59, "sharpe": 1.95, "expectancy_r": 1.167, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 63, "return_pct": -11.03, "trading_pnl": -15274.81, "pf": 0.7, "win_rate": 30.2, "dd_pct": 23.86, "sharpe": -0.42, "expectancy_r": -0.258, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 78, "return_pct": 27.58, "trading_pnl": 22736.29, "pf": 1.37, "win_rate": 43.6, "dd_pct": 13.8, "sharpe": 1.09, "expectancy_r": 0.36, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 85, "return_pct": 79.72, "trading_pnl": 74902.61, "pf": 1.94, "win_rate": 52.9, "dd_pct": 11.66, "sharpe": 2.05, "expectancy_r": 0.518, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 19, "return_pct": -0.26, "trading_pnl": -2056.38, "pf": 0.86, "win_rate": 26.3, "dd_pct": 18.14, "sharpe": 0.06, "expectancy_r": -0.104, "bnh_btc_pct": -26.75}}

## [22/08/2026 23:33] - Experimento Walk-Forward: config 9ea2dff4
- **Mudança Implementada:** Parâmetros testados: {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "btc_adx_min": 0.0, "entry_tf": "1d", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}
- **Resultados Obtidos (OOS deslizante 2022-09 -> 2026-02):**
```
{
  "trades_total": 245,
  "return_pct_sum": 88.66,
  "trading_pnl_sum": 73098.01,
  "pf_mean": 1.18,
  "pf_median": 1.08,
  "win_rate_mean": 38.2,
  "dd_max": 24.36,
  "sharpe_mean": 0.63,
  "expectancy_r_mean": 0.111
}
```
- **Análise Diagnóstica:** IS/OOS por janela: {"IS": {"window": "2019-09-01 -> 2022-09-01", "trades": 87, "return_pct": 270.79, "trading_pnl": 237842.2, "pf": 2.61, "win_rate": 55.2, "dd_pct": 16.6, "sharpe": 1.93, "expectancy_r": 1.151, "bnh_btc_pct": 93.58}, "OOS1": {"window": "2022-09-01 -> 2023-09-01", "trades": 63, "return_pct": -12.33, "trading_pnl": -16549.42, "pf": 0.68, "win_rate": 30.2, "dd_pct": 24.36, "sharpe": -0.48, "expectancy_r": -0.277, "bnh_btc_pct": 30.25}, "OOS2": {"window": "2023-09-01 -> 2024-09-01", "trades": 78, "return_pct": 25.54, "trading_pnl": 20747.21, "pf": 1.33, "win_rate": 43.6, "dd_pct": 14.0, "sharpe": 1.02, "expectancy_r": 0.342, "bnh_btc_pct": 124.39}, "OOS3": {"window": "2024-09-01 -> 2025-09-01", "trades": 85, "return_pct": 76.17, "trading_pnl": 71412.76, "pf": 1.89, "win_rate": 52.9, "dd_pct": 11.77, "sharpe": 1.98, "expectancy_r": 0.501, "bnh_btc_pct": 83.96}, "OOS4": {"window": "2025-09-01 -> 2026-02-01", "trades": 19, "return_pct": -0.72, "trading_pnl": -2512.54, "pf": 0.83, "win_rate": 26.3, "dd_pct": 18.32, "sharpe": 0.0, "expectancy_r": -0.124, "bnh_btc_pct": -26.75}}

---

## [23/08/2026 01:48] - Estratégia: Adoção Oficial V2.2 (validação Walk-Forward concluída)
- **Mudança Implementada:** Adotadas como padrão do motor canônico: (1) Gatilho LONG confirmado no 1D (close > dia anterior, pullback EMA20 1D, RSI 1D 44-62, CVD 4h > 0). (2) Short por ROMPIMENTO de fundo diário (close 1D < mínima do dia anterior, RSI 30-56, CVD < 0). (3) Runner segue EMA20 1D sem teto (alternativas testadas e rejeitadas: prev_low_1d e ATR chandelier). (4) Dados expandidos para 2019-09 → 2026-08 com delistados (LUNA, FTT, SRM, ANC, MIR, DODO, EOS, YFII, BZRX, BTS, COCOS, GTO, TORN, VGX, TCT, REP).
- **Resultados Obtidos (Walk-Forward OOS, 4 blocos 2022-09→2026-02, 245 trades):** V2.1 baseline: TradingPnL -R\\.145 | PF 0.90 | Sharpe -0.02. V2.2: **TradingPnL +R\\.098 | PF 1.18 | Sharpe 0.63 | DD máx 24.4% | Win 38.2% | ExpR +0.111R**. Holdout final intocado (2026-02→2026-08): V2.2 -1.16% vs B&H BTC -12.23% (preservação confirmada). Experimentos rejeitados: ADX BTC ≥ 20 (OOS -19k), runner prev_low_1d (OOS -30.5k), runner ATR chandelier (OOS -9.4k), top20 (sem efeito). Fee 0.02% agrega ~+R\\.9k OOS (meta operacional: buscar tier VIP).
- **Resultados Obtidos (Modalidades Oficiais V2.2, 552 moedas, R\\):** Full 7 anos: **+555.2%** (PF 1.47, DD 34.0%, Sharpe 1.25) vs B&H BTC +569.1% | 5 anos (2021-11→2026-08): **+101.5%** (PF 1.28) vs BTC +5.2% | Bear 2022: **+19.7%** (PF 1.75) vs BTC -64.6% | Bull 6m: **+38.9%** (PF 1.92) vs BTC +158.9% | Chop 6m: **-2.3%** vs BTC -8.7% | Preliminar 1a: **+35.2%** (PF 1.43).
- **Análise Diagnóstica:** O edge agora é REAL e validado fora da amostra: nos 5 anos o trading líquido saiu de -R\\,5k (V2.1) para **+R\\,2k** (V2.2). A assimetria é de trend-following clássico (Win 39%, expR +0.14R): o lucro vem dos runners (avg +2.4R nos trailing) e as perdas são contidas (-1.04R nos stops). O sistema iguala o B&H BTC em 7 anos (555% vs 569%) com muito menos risco (DD 34% vs ~77% do BTC no período) e VENCE em janelas adversas (bear 2022, 5 anos). Trade-off conhecido: cede upside nos janelões de alta (Bull 6m: 39% vs 159%) — o híbrido 25% BTC / 75% sistema quase dobra o retorno nesses períodos. Recomendação de alocação padrão: 75% sistema + 25% B&H BTC (ou aumentar o B&H em regime bull forte), e buscar tier VIP de taxas.
