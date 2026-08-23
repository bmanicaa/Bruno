# Relatório de Auditoria Quantitativa: Modalidade [ESTRESSE_BEAR]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.2
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2022-01-01 até 2022-12-31
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 119,654.24 (+19.65%)
- **Lucro Líquido Real:** R$ 19,654.24
- **Total de Trades:** 27 (12 Vitórias / 15 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 44.44% (IC 95%: 27.6% - 62.7%)
- **Fator de Lucro (Profit Factor):** 1.75
- **Expectância por Trade:** +0.396R | MAE médio -0.52R | MFE médio +1.33R
- **Drawdown Máximo (MtM):** 10.90%
- **Sharpe Ratio:** 1.49 | **Sortino Ratio:** 1.55

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | +13,910.37 |
| PnL de Trading (bruto, antes de custos) | +14,556.29 |
| Taxas de Corretagem Pagas | 1,107.13 |
| Funding Pagos/Recebidos | -461.21 |
| Rendimento do Caixa (6% a.a.) | 5,743.87 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **-64.63%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **-67.91%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | -1.42% |
| 50% BTC / 50% Sistema | -22.49% |
| 75% BTC / 25% Sistema | -43.56% |

⚠️ **ATENÇÃO ESTATÍSTICA:** amostra de apenas 27 trades (< 30). Conclusões não são estatisticamente robustas.

---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bear | 27 | 44.4% | +13,910.37 | +0.396 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ETH | 12 | 50.0% | +7,326.34 | +0.513 |
| BTC | 15 | 40.0% | +6,584.03 | +0.302 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Trailing Runner 50% (ema20_1d) | 7 | 100.0% | +25,632.18 | +2.801 |
| Stop BE Runner (50%) | 4 | 100.0% | +6,915.59 | +0.979 |
| Stop Loss Inicial | 12 | 0.0% | -17,868.22 | -1.036 |
| Time-Stop (21d) | 2 | 0.0% | -786.82 | -0.216 |
| Fechamento Fim do Período (MtM) | 2 | 50.0% | +17.65 | +0.010 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2022-01-01 | R$   100,002.74 |
| 2022-07-01 | R$   118,096.91 |
| 2022-12-31 | R$   119,688.03 |
