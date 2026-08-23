# Relatório de Auditoria Quantitativa: Modalidade [ESTRESSE_BULL]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.2
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2023-10-01 até 2024-03-31
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 138,880.93 (+38.88%)
- **Lucro Líquido Real:** R$ 38,880.93
- **Total de Trades:** 48 (24 Vitórias / 24 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 50.00% (IC 95%: 36.4% - 63.6%)
- **Fator de Lucro (Profit Factor):** 1.92
- **Expectância por Trade:** +0.963R | MAE médio -0.54R | MFE médio +2.38R
- **Drawdown Máximo (MtM):** 16.83%
- **Sharpe Ratio:** 2.22 | **Sortino Ratio:** 2.74

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | +37,030.69 |
| PnL de Trading (bruto, antes de custos) | +42,667.69 |
| Taxas de Corretagem Pagas | 1,621.91 |
| Funding Pagos/Recebidos | +4,015.08 |
| Rendimento do Caixa (6% a.a.) | 1,850.24 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **+158.87%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **+111.51%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | +68.88% |
| 50% BTC / 50% Sistema | +98.88% |
| 75% BTC / 25% Sistema | +128.87% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bull | 47 | 51.1% | +37,771.41 | +1.006 |
| bear | 1 | 0.0% | -740.72 | -1.052 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ALT | 40 | 50.0% | +27,472.15 | +0.969 |
| BTC | 6 | 50.0% | +9,506.43 | +1.256 |
| ETH | 2 | 50.0% | +52.11 | -0.035 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Stop Loss Inicial | 24 | 0.0% | -40,118.91 | -1.063 |
| Trailing Runner 50% (ema20_1d) | 14 | 100.0% | +58,600.70 | +3.831 |
| Time-Stop (21d) | 2 | 100.0% | +1,729.91 | +1.057 |
| Stop BE Runner (50%) | 4 | 100.0% | +5,099.50 | +0.896 |
| Fechamento Fim do Período (MtM) | 4 | 100.0% | +11,719.49 | +3.102 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2023-10-01 | R$   100,002.74 |
| 2024-03-31 | R$   138,904.96 |
