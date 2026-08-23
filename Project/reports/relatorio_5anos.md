# Relatório de Auditoria Quantitativa: Modalidade [5ANOS]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.3.1
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "long_mode": "pullback", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2021-11-15 até 2026-08-20
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 101,888.65 (+1.89%)
- **Lucro Líquido Real:** R$ 1,888.65
- **Total de Trades:** 305 (108 Vitórias / 197 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 35.41% (IC 95%: 30.3% - 40.9%)
- **Fator de Lucro (Profit Factor):** 0.92
- **Expectância por Trade:** -0.014R | MAE médio -0.74R | MFE médio +1.15R
- **Drawdown Máximo (MtM):** 32.47%
- **Sharpe Ratio:** 0.13 | **Sortino Ratio:** 0.13

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | -19,405.03 |
| PnL de Trading (bruto, antes de custos) | -7,116.15 |
| Taxas de Corretagem Pagas | 8,441.24 |
| Funding Pagos/Recebidos | +3,847.64 |
| Rendimento do Caixa (6% a.a.) | 21,293.68 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **+5.21%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **-52.18%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | +2.72% |
| 50% BTC / 50% Sistema | +3.55% |
| 75% BTC / 25% Sistema | +4.38% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bull | 240 | 36.7% | -7,757.63 | +0.010 |
| bear | 65 | 30.8% | -11,647.40 | -0.101 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ALT | 213 | 35.7% | -11,463.21 | -0.022 |
| BTC | 54 | 31.5% | -5,685.64 | -0.063 |
| ETH | 38 | 39.5% | -2,256.18 | +0.103 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Trailing Runner 50% (ema20_1d) | 66 | 100.0% | +182,573.31 | +2.357 |
| Time-Stop (21d) | 25 | 60.0% | +6,222.69 | +0.268 |
| Stop BE Runner (50%) | 27 | 100.0% | +32,472.56 | +1.006 |
| Stop Loss Inicial | 187 | 0.0% | -240,673.59 | -1.036 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2021-11-15 | R$   100,002.74 |
| 2022-05-15 | R$   107,921.30 |
| 2022-11-15 | R$   108,723.80 |
| 2023-05-15 | R$    91,136.47 |
| 2023-11-15 | R$    90,416.56 |
| 2024-05-15 | R$    98,802.03 |
| 2024-11-15 | R$   105,197.55 |
| 2025-05-15 | R$   103,612.46 |
| 2025-11-15 | R$   103,241.68 |
| 2026-05-15 | R$   100,892.49 |
| 2026-08-20 | R$   101,888.65 |
