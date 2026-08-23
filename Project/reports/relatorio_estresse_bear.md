# Relatório de Auditoria Quantitativa: Modalidade [ESTRESSE_BEAR]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.3.1
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "long_mode": "pullback", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2022-01-01 até 2022-12-31
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 104,142.30 (+4.14%)
- **Lucro Líquido Real:** R$ 4,142.30
- **Total de Trades:** 28 (10 Vitórias / 18 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 35.71% (IC 95%: 20.7% - 54.2%)
- **Fator de Lucro (Profit Factor):** 0.94
- **Expectância por Trade:** +0.035R | MAE médio -0.64R | MFE médio +0.98R
- **Drawdown Máximo (MtM):** 11.70%
- **Sharpe Ratio:** 0.43 | **Sortino Ratio:** 0.42

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | -1,399.08 |
| PnL de Trading (bruto, antes de custos) | -857.97 |
| Taxas de Corretagem Pagas | 925.77 |
| Funding Pagos/Recebidos | -384.65 |
| Rendimento do Caixa (6% a.a.) | 5,541.38 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **-64.63%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **-67.91%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | -13.05% |
| 50% BTC / 50% Sistema | -30.24% |
| 75% BTC / 25% Sistema | -47.44% |

⚠️ **ATENÇÃO ESTATÍSTICA:** amostra de apenas 28 trades (< 30). Conclusões não são estatisticamente robustas.

---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bear | 27 | 37.0% | -601.67 | +0.074 |
| bull | 1 | 0.0% | -797.41 | -1.032 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ETH | 11 | 45.5% | +3,139.76 | +0.403 |
| BTC | 16 | 31.2% | -3,741.43 | -0.152 |
| ALT | 1 | 0.0% | -797.41 | -1.032 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Trailing Runner 50% (ema20_1d) | 5 | 100.0% | +16,387.65 | +2.834 |
| Stop BE Runner (50%) | 2 | 100.0% | +3,171.24 | +0.981 |
| Stop Loss Inicial | 16 | 0.0% | -22,496.08 | -1.035 |
| Time-Stop (21d) | 3 | 66.7% | +1,331.33 | +0.420 |
| Fechamento Fim do Período (MtM) | 2 | 50.0% | +206.79 | +0.066 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2022-01-01 | R$   100,002.74 |
| 2022-07-01 | R$   112,823.38 |
| 2022-12-31 | R$   104,189.80 |
