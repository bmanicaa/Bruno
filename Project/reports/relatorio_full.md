# Relatório de Auditoria Quantitativa: Modalidade [FULL]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.3.1
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "long_mode": "pullback", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2019-09-01 até 2026-08-20
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 192,800.49 (+92.80%)
- **Lucro Líquido Real:** R$ 92,800.49
- **Total de Trades:** 382 (142 Vitórias / 240 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 37.17% (IC 95%: 32.5% - 42.1%)
- **Fator de Lucro (Profit Factor):** 1.06
- **Expectância por Trade:** +0.115R | MAE médio -0.73R | MFE médio +1.36R
- **Drawdown Máximo (MtM):** 34.33%
- **Sharpe Ratio:** 0.52 | **Sortino Ratio:** 0.51

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | +36,775.79 |
| PnL de Trading (bruto, antes de custos) | +82,596.91 |
| Taxas de Corretagem Pagas | 19,633.71 |
| Funding Pagos/Recebidos | +26,187.41 |
| Rendimento do Caixa (6% a.a.) | 56,024.70 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **+569.08%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **+1441.68%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | +211.87% |
| 50% BTC / 50% Sistema | +330.94% |
| 75% BTC / 25% Sistema | +450.01% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bear | 78 | 30.8% | -35,011.20 | -0.131 |
| bull | 304 | 38.8% | +71,786.98 | +0.178 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| BTC | 77 | 35.1% | -6,651.13 | +0.119 |
| ETH | 49 | 40.8% | +188.55 | +0.157 |
| ALT | 256 | 37.1% | +43,238.37 | +0.106 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Trailing Runner 50% (ema20_1d) | 87 | 100.0% | +498,442.37 | +2.714 |
| Stop Loss Inicial | 229 | 0.0% | -563,157.90 | -1.039 |
| Time-Stop (21d) | 26 | 57.7% | +11,187.71 | +0.244 |
| Stop BE Runner (50%) | 40 | 100.0% | +90,303.61 | +0.983 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2019-09-01 | R$   100,002.74 |
| 2020-03-01 | R$   102,909.99 |
| 2020-09-01 | R$   124,115.30 |
| 2021-03-01 | R$   190,281.63 |
| 2021-09-01 | R$   213,355.40 |
| 2022-03-01 | R$   208,578.61 |
| 2022-09-01 | R$   208,976.48 |
| 2023-03-01 | R$   193,277.25 |
| 2023-09-01 | R$   159,072.97 |
| 2024-03-01 | R$   204,215.59 |
| 2024-09-01 | R$   162,864.50 |
| 2025-03-01 | R$   169,796.06 |
| 2025-09-01 | R$   183,527.54 |
| 2026-03-01 | R$   201,857.53 |
| 2026-08-20 | R$   192,800.49 |
