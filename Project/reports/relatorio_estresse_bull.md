# Relatório de Auditoria Quantitativa: Modalidade [ESTRESSE_BULL]

## ⚙️ 0. Identificação do Teste
- **Motor:** `scripts/backtest_institucional.py` (Canônico) | **Versão da Estratégia:** V2.3.1
- **Parâmetros Blindados:** {"risk_pct": 0.015, "max_positions": 4, "fee_pct": 0.00075, "entry_slippage": 0.0005, "stop_slippage": 0.0008, "annual_cash_yield": 0.06, "btc_adx_min": 0.0, "entry_tf": "1d", "long_mode": "pullback", "runner_mode": "ema20_1d", "short_mode": "breakout", "universe": "alpha"}

## 📊 1. Resumo Executivo da Modalidade
- **Período Auditado:** 2023-10-01 até 2024-03-31
- **Universo Monitorado:** 552 moedas da Binance (inclui delistados)
- **Capital Inicial:** R$ 100,000.00
- **Saldo Final:** R$ 139,605.51 (+39.61%)
- **Lucro Líquido Real:** R$ 39,605.51
- **Total de Trades:** 57 (25 Vitórias / 32 Derrotas / 0 no 0x0)
- **Taxa de Acerto (Win Rate):** 43.86% (IC 95%: 31.8% - 56.7%)
- **Fator de Lucro (Profit Factor):** 1.79
- **Expectância por Trade:** +0.496R | MAE médio -0.66R | MFE médio +1.60R
- **Drawdown Máximo (MtM):** 18.43%
- **Sharpe Ratio:** 2.17 | **Sortino Ratio:** 2.54

---

## 🔬 2. Decomposição do Resultado (Onde o dinheiro foi feito/perdido)
| Componente | Valor (R$) |
| :--- | :---: |
| PnL de Trading (líquido de taxas/funding) | +37,493.36 |
| PnL de Trading (bruto, antes de custos) | +43,314.43 |
| Taxas de Corretagem Pagas | 1,762.09 |
| Funding Pagos/Recebidos | +4,058.99 |
| Rendimento do Caixa (6% a.a.) | 2,112.15 |
| **Benchmark Buy & Hold BTC (sem taxas)** | **+158.87%** |
| **Benchmark Buy & Hold ETH (sem taxas)** | **+111.51%** |

### Carteiras Híbridas Hipotéticas (X% B&H BTC + resto Sistema, sem rebalanceamento)
| Alocação | Retorno do Período |
| :--- | :---: |
| 25% BTC / 75% Sistema | +69.42% |
| 50% BTC / 50% Sistema | +99.24% |
| 75% BTC / 25% Sistema | +129.06% |



---

## 🧬 3. Diagnóstico Segmentado

### Por Regime de Entrada (BTC macro)
| Regime | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| bull | 56 | 44.6% | +39,013.23 | +0.523 |
| bear | 1 | 0.0% | -1,519.88 | -1.045 |

### Por Classe de Ativo
| Classe | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| ALT | 49 | 40.8% | +30,982.91 | +0.449 |
| BTC | 5 | 80.0% | +6,859.80 | +1.426 |
| ETH | 3 | 33.3% | -349.35 | -0.294 |

### Por Motivo de Saída
| Motivo | Trades | Win Rate | PnL (R$) | Avg R |
| :--- | :---: | :---: | :---: | :---: |
| Stop Loss Inicial | 32 | 0.0% | -47,567.37 | -1.041 |
| Trailing Runner 50% (ema20_1d) | 17 | 100.0% | +70,851.79 | +2.943 |
| Stop BE Runner (50%) | 3 | 100.0% | +4,699.11 | +0.888 |
| Time-Stop (21d) | 1 | 100.0% | +1,563.26 | +0.871 |
| Fechamento Fim do Período (MtM) | 4 | 100.0% | +7,946.57 | +2.003 |


---

## 📈 4. Evolução do Patrimônio (Checkpoints Semestrais)
| Checkpoint | Saldo da Carteira (R$) |
| :--- | :---: |
| 2023-10-01 | R$   100,002.74 |
| 2024-03-31 | R$   139,632.79 |
