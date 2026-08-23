# Relatório de Auditoria Quantitativa: Modalidade [ESTRESSE_CHOP]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.2
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2024-04-01 até 2024-09-30
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 97,686.46 (-2.31%)
- **Lucro Líquido Real:** R$ -2,313.54
- **Total de Trades:** 30 (10 Vitórias / 20 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 33.33% (IC 95%: 19.2% - 51.2%)
- **Fator de Lucro (Profit Factor):** 0.78
- **Expectância por Trade:** -0.214R | MAE médio -0.72R | MFE médio +1.03R
- **Drawdown Máximo (MtM):** 13.74%
- **Sharpe Ratio:** -0.15 | **Sortino Ratio:** -0.16

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | -4,762.58 |
| PnL de Trading (bruto, antes de custos) | -3,113.85 |
| Taxas de Corretagem Pagas | 841.75 |
| Funding Pagos/Recebidos | +806.97 |
| Rendimento do Caixa (6% a.a.) | 2,449.03 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **-8.65%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **-27.27%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | -3.90% |
| 50% BTC / 50% Sistema | -5.48% |
| 75% BTC / 25% Sistema | -7.06% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bull | 23 | 34.8% | -1,769.49 | -0.153 |
| bear | 7 | 28.6% | -2,993.09 | -0.414 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ALT | 21 | 38.1% | +1,713.67 | -0.060 |
| BTC | 5 | 20.0% | -4,227.99 | -0.640 |
| ETH | 4 | 25.0% | -2,248.25 | -0.488 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Stop Loss Inicial | 17 | 0.0% | -20,406.94 | -1.046 |
| Stop BE Runner (50%) | 2 | 100.0% | +2,915.26 | +0.958 |
| Trailing Runner 50% (ema20_1d) | 7 | 100.0% | +13,447.68 | +1.338 |
| Time-Stop (21d) | 2 | 50.0% | +569.36 | +0.473 |
| Fechamento Fim do Período (MtM) | 2 | 0.0% | -1,287.93 | -0.434 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2024-04-01 | R$   100,002.74 |
| 2024-09-30 | R$    97,718.02 |
