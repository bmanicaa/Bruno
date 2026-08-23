# Relatório de Auditoria Quantitativa: Modalidade [PRELIMINAR]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.3.1
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "long_mode": "pullback", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2023-10-01 até 2024-10-01
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 107,783.84 (+7.78%)
- **Lucro Líquido Real:** R$ 7,783.84
- **Total de Trades:** 92 (31 Vitórias / 61 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 33.70% (IC 95%: 24.9% - 43.8%)
- **Fator de Lucro (Profit Factor):** 1.03
- **Expectância por Trade:** +0.051R | MAE médio -0.78R | MFE médio +1.23R
- **Drawdown Máximo (MtM):** 29.53%
- **Sharpe Ratio:** 0.42 | **Sortino Ratio:** 0.45
- **Sharpe de TRADING** (excesso sobre o cash yield — mede edge, não o rendimento do caixa)**:** 0.19 | **Sortino de TRADING:** 0.20

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | +2,754.57 |
| PnL de Trading (bruto, antes de custos) | +10,167.29 |
| Taxas de Corretagem Pagas | 2,796.44 |
| Funding Pagos/Recebidos | +4,616.28 |
| Rendimento do Caixa (6% a.a.) | 5,029.27 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **+135.66%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **+57.10%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | +39.75% |
| 50% BTC / 50% Sistema | +71.72% |
| 75% BTC / 25% Sistema | +103.69% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bull | 84 | 34.5% | +9,831.14 | +0.109 |
| bear | 8 | 25.0% | -7,076.56 | -0.555 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ALT | 75 | 32.0% | +3,296.26 | +0.047 |
| BTC | 10 | 50.0% | +3,530.35 | +0.436 |
| ETH | 7 | 28.6% | -4,072.04 | -0.459 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Stop Loss Inicial | 58 | 0.0% | -85,575.53 | -1.040 |
| Trailing Runner 50% (ema20_1d) | 21 | 100.0% | +78,359.27 | +2.748 |
| Stop BE Runner (50%) | 6 | 100.0% | +7,466.90 | +0.953 |
| Time-Stop (21d) | 5 | 60.0% | +1,900.58 | +0.253 |
| Fechamento Fim do Período (MtM) | 2 | 50.0% | +603.35 | +0.180 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2023-10-01 | R$   100,002.74 |
| 2024-04-01 | R$   141,229.63 |
| 2024-10-01 | R$   107,817.50 |
