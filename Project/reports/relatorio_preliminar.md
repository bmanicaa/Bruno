# Relatório de Auditoria Quantitativa: Modalidade [PRELIMINAR]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.2
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2023-10-01 até 2024-10-01
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 135,159.22 (+35.16%)
- **Lucro Líquido Real:** R$ 35,159.22
- **Total de Trades:** 77 (34 Vitórias / 43 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 44.16% (IC 95%: 33.6% - 55.3%)
- **Fator de Lucro (Profit Factor):** 1.43
- **Expectância por Trade:** +0.500R | MAE médio -0.62R | MFE médio +1.89R
- **Drawdown Máximo (MtM):** 16.83%
- **Sharpe Ratio:** 1.28 | **Sortino Ratio:** 1.46

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | +29,861.02 |
| PnL de Trading (bruto, antes de custos) | +37,737.66 |
| Taxas de Corretagem Pagas | 2,741.44 |
| Funding Pagos/Recebidos | +5,135.20 |
| Rendimento do Caixa (6% a.a.) | 5,298.20 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **+135.66%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **+57.10%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | +60.29% |
| 50% BTC / 50% Sistema | +85.41% |
| 75% BTC / 25% Sistema | +110.54% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bull | 69 | 46.4% | +34,760.56 | +0.615 |
| bear | 8 | 25.0% | -4,899.54 | -0.494 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ALT | 61 | 45.9% | +27,085.98 | +0.575 |
| BTC | 10 | 40.0% | +5,846.82 | +0.541 |
| ETH | 6 | 33.3% | -3,071.78 | -0.337 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Stop Loss Inicial | 41 | 0.0% | -68,239.07 | -1.055 |
| Trailing Runner 50% (ema20_1d) | 23 | 100.0% | +85,113.09 | +3.107 |
| Time-Stop (21d) | 4 | 75.0% | +2,521.03 | +0.765 |
| Stop BE Runner (50%) | 8 | 100.0% | +10,699.13 | +0.915 |
| Fechamento Fim do Período (MtM) | 1 | 0.0% | -233.16 | -0.113 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2023-10-01 | R$   100,002.74 |
| 2024-04-01 | R$   141,153.68 |
| 2024-10-01 | R$   135,184.89 |
