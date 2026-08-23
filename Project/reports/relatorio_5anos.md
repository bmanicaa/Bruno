# Relatório de Auditoria Quantitativa: Modalidade [5ANOS]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.2
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2021-11-15 até 2026-08-20
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 201,504.53 (+101.50%)
- **Lucro Líquido Real:** R$ 101,504.53
- **Total de Trades:** 266 (105 Vitórias / 161 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 39.47% (IC 95%: 33.8% - 45.5%)
- **Fator de Lucro (Profit Factor):** 1.28
- **Expectância por Trade:** +0.138R | MAE médio -0.66R | MFE médio +1.39R
- **Drawdown Máximo (MtM):** 34.03%
- **Sharpe Ratio:** 0.78 | **Sortino Ratio:** 0.82

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | +73,215.40 |
| PnL de Trading (bruto, antes de custos) | +85,690.73 |
| Taxas de Corretagem Pagas | 10,731.69 |
| Funding Pagos/Recebidos | +1,743.63 |
| Rendimento do Caixa (6% a.a.) | 28,289.12 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **+5.21%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **-52.18%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | +77.43% |
| 50% BTC / 50% Sistema | +53.36% |
| 75% BTC / 25% Sistema | +29.28% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bull | 203 | 39.9% | +44,519.42 | +0.116 |
| bear | 63 | 38.1% | +28,695.98 | +0.211 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ALT | 181 | 38.1% | -279.05 | +0.011 |
| ETH | 37 | 43.2% | +36,554.10 | +0.419 |
| BTC | 48 | 41.7% | +36,940.36 | +0.400 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Stop Loss Inicial | 152 | 0.0% | -253,623.08 | -1.039 |
| Trailing Runner 50% (ema20_1d) | 69 | 100.0% | +284,679.52 | +2.409 |
| Time-Stop (21d) | 19 | 52.6% | +3,324.28 | +0.184 |
| Stop BE Runner (50%) | 26 | 100.0% | +38,834.68 | +0.959 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2021-11-15 | R$   100,002.74 |
| 2022-05-15 | R$   103,910.79 |
| 2022-11-15 | R$   116,201.36 |
| 2023-05-15 | R$   118,100.19 |
| 2023-11-15 | R$    96,645.38 |
| 2024-05-15 | R$   126,320.11 |
| 2024-11-15 | R$   135,455.23 |
| 2025-05-15 | R$   184,199.01 |
| 2025-11-15 | R$   178,657.94 |
| 2026-05-15 | R$   194,903.65 |
| 2026-08-20 | R$   201,504.53 |
