# Relatório de Auditoria Quantitativa: Modalidade [ESTRESSE_CHOP]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.3.1
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "long_mode": "pullback", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2024-04-01 até 2024-09-30
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 79,428.72 (-20.57%)
- **Lucro Líquido Real:** R$ -20,571.28
- **Total de Trades:** 36 (6 Vitórias / 30 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 16.67% (IC 95%: 7.9% - 31.9%)
- **Fator de Lucro (Profit Factor):** 0.17
- **Expectância por Trade:** -0.642R | MAE médio -0.94R | MFE médio +0.64R
- **Drawdown Máximo (MtM):** 21.43%
- **Sharpe Ratio:** -3.27 | **Sortino Ratio:** -3.04
- **Sharpe de TRADING** (excesso sobre o cash yield — mede edge, não o rendimento do caixa)**:** -3.70 | **Sortino de TRADING:** -3.48

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | -22,713.47 |
| PnL de Trading (bruto, antes de custos) | -21,668.90 |
| Taxas de Corretagem Pagas | 734.86 |
| Funding Pagos/Recebidos | +309.71 |
| Rendimento do Caixa (6% a.a.) | 2,142.19 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **-8.65%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **-27.27%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | -17.59% |
| 50% BTC / 50% Sistema | -14.61% |
| 75% BTC / 25% Sistema | -11.63% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bull | 29 | 13.8% | -18,647.71 | -0.680 |
| bear | 7 | 28.6% | -4,065.77 | -0.485 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ALT | 26 | 15.4% | -16,716.89 | -0.648 |
| BTC | 6 | 16.7% | -3,272.73 | -0.657 |
| ETH | 4 | 25.0% | -2,723.85 | -0.583 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Stop Loss Inicial | 27 | 0.0% | -26,463.34 | -1.042 |
| Stop BE Runner (50%) | 3 | 100.0% | +2,025.16 | +1.017 |
| Time-Stop (21d) | 3 | 33.3% | -175.13 | -0.061 |
| Trailing Runner 50% (ema20_1d) | 1 | 100.0% | +886.33 | +1.324 |
| Fechamento Fim do Período (MtM) | 2 | 50.0% | +1,013.50 | +0.416 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2024-04-01 | R$   100,002.74 |
| 2024-09-30 | R$    79,453.77 |
