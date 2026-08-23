# Relatório de Auditoria Quantitativa: Modalidade [FULL]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.2
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2019-09-01 até 2026-08-20
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 655,186.77 (+555.19%)
- **Lucro Líquido Real:** R$ 555,186.77
- **Total de Trades:** 334 (145 Vitórias / 189 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 43.41% (IC 95%: 38.2% - 48.8%)
- **Fator de Lucro (Profit Factor):** 1.47
- **Expectância por Trade:** +0.383R | MAE médio -0.63R | MFE médio +1.72R
- **Drawdown Máximo (MtM):** 34.03%
- **Sharpe Ratio:** 1.25 | **Sortino Ratio:** 1.29

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | +444,213.30 |
| PnL de Trading (bruto, antes de custos) | +520,799.94 |
| Taxas de Corretagem Pagas | 39,528.70 |
| Funding Pagos/Recebidos | +37,057.95 |
| Rendimento do Caixa (6% a.a.) | 110,973.48 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **+569.08%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **+1441.68%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | +558.66% |
| 50% BTC / 50% Sistema | +562.13% |
| 75% BTC / 25% Sistema | +565.61% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bear | 74 | 41.9% | +110,259.56 | +0.242 |
| bull | 260 | 43.8% | +333,953.74 | +0.423 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| BTC | 70 | 47.1% | +149,266.56 | +0.563 |
| ETH | 47 | 48.9% | +147,283.77 | +0.552 |
| ALT | 217 | 41.0% | +147,662.97 | +0.288 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Trailing Runner 50% (ema20_1d) | 97 | 100.0% | +1,196,730.85 | +2.855 |
| Stop Loss Inicial | 178 | 0.0% | -919,441.36 | -1.043 |
| Time-Stop (21d) | 23 | 52.2% | +7,261.95 | +0.111 |
| Stop BE Runner (50%) | 36 | 100.0% | +159,661.86 | +0.944 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2019-09-01 | R$   100,002.74 |
| 2020-03-01 | R$   102,909.99 |
| 2020-09-01 | R$   133,308.07 |
| 2021-03-01 | R$   257,622.44 |
| 2021-09-01 | R$   346,917.29 |
| 2022-03-01 | R$   336,910.85 |
| 2022-09-01 | R$   370,843.19 |
| 2023-03-01 | R$   385,085.52 |
| 2023-09-01 | R$   328,715.76 |
| 2024-03-01 | R$   353,833.83 |
| 2024-09-01 | R$   378,858.90 |
| 2025-03-01 | R$   485,934.03 |
| 2025-09-01 | R$   639,467.69 |
| 2026-03-01 | R$   675,483.77 |
| 2026-08-20 | R$   655,186.77 |
