# Sistema Quantitativo de Swing Trade em Criptoativos — Prompt Mestre V2.2

Este repositório contém a arquitetura completa, o protocolo de auditoria e o **motor de simulação canônico** *point-in-time* (zero lookahead bias) para a estratégia de **Swing Trade Quantitativo Multidimensional** em timeframes de 4h e 1D, operando bi-direcionalmente (Long/Short) sobre o mercado total da Binance (~550 moedas + delistados), com **validação walk-forward out-of-sample**.

---

## 📁 Estrutura Organizada do Projeto

```
Project/
├── Prompt.md                     # Arquivo Mestre V2.2 (Protocolo de Teste + Operação + Engenharia)
├── README.md                     # Guia Geral e Documentação Executiva
├── analises.md                   # Registro histórico de análises, experimentos e diagnósticos
├── data/
│   ├── raw/                      # 🌟 DADOS BRUTOS IMUTÁVEIS (2019-09 → 2026-08 / Binance Futures)
│   │   ├── universe_metadata.json# Metadados globais + cobertura por ativo
│   │   ├── macro/                # BTCUSDT 4h/1d + Funding + Fear & Greed Index
│   │   └── coins/{SYMBOL}/       # klines_4h.csv | klines_1d.csv | funding_rates.csv (inclui delistados)
│   ├── resumo_{modo}.json        # Resumo estatístico da modalidade (1 arquivo por modo)
│   ├── trades_{modo}.csv         # Tabela de trades com instrumentação (MAE/MFE, regime, classe)
│   ├── experimentos/             # Resultados walk-forward (exp_{hash}.json)
│   └── legado/                   # Artefatos de estratégias antigas (apenas histórico)
├── reports/                      # relatorio_{modo}.md (Relatórios Executivos de Auditoria)
└── scripts/
    ├── backtest_institucional.py # ⚙️ MOTOR CANÔNICO ÚNICO (V2.2 + walk-forward + experimentos)
    ├── download_raw_market_data.py # Downloader de Dados Brutos (~7 anos + delistados)
    └── legado/                   # Motores antigos/experimentais (NÃO usar em novos testes)
```

---

## 🎯 As Regras Estruturais do Protocolo ([Prompt.md](Prompt.md))

1. **Universo:** ~550 moedas da Binance (Volume Médio Diário 30d > $25M, Maturidade > 180 dias) + delistados históricos (LUNA, FTT, SRM, ANC, MIR, DODO, EOS, YFII, BZRX, BTS, COCOS, GTO, TORN, VGX, TCT, REP).
2. **Regime Macro (1D):** Long apenas com BTC ≥ EMA50 e EMA200; Short (só BTC/ETH) apenas com BTC < EMA50 e EMA200; Transição = caixa remunerado.
3. **Seleção de Líderes:** Top 10% de Força Relativa (Alpha 7d vs BTC) + estrutura diária alinhada (Close 1D ≥ EMA20 ≥ EMA50).
4. **Gatilho LONG (1D — V2.2):** Pullback na EMA20 1D + confirmação diária (Close > dia anterior) + RSI 1D 44-62 + CVD 4h > 0.
   **Gatilho SHORT (V2.2):** Rompimento de fundo diário (Close 1D < mínima do dia anterior) + RSI 30-56 + CVD < 0 (trend-following).
5. **Stop Estrutural:** mín/máx dos últimos 10 candles 4h ± 1,5×ATR14 (faixa 3,5%–8%).
6. **Gestão de Risco:** 1,50% por trade | até 4 posições | Circuit Breaker (3 perdas → 0,75%; 5 perdas → pausa 5 dias) | Cooldown 2,5 dias por ativo.
7. **Condução Assimétrica:** em +2.0R → Breakeven (0x0) + Parcial de 50%; Runner (50%) sem teto, trailing na EMA20 1D. Time-Stop de 21 dias.
8. **Vetos:** Vesting > 1% em 7 dias; Funding > 0,03% (long) / < -0,03% (short).
9. **Custos Reais:** Binance 0,075% maker/taker, slippage 5 bps (entrada) e 8 bps (stop), Funding a cada 8h, Cash Yield 6% a.a. no caixa livre.
10. **Validação:** Walk-Forward deslizante (4 blocos OOS + holdout final intocado) obrigatório para qualquer mudança — aceite com melhora em ≥3/5 métricas OOS e PF OOS > 1.0.

---

## 🚀 Como Executar o Motor Canônico

```bash
python scripts/backtest_institucional.py --mode full           # Auditoria Completa (7 anos)
python scripts/backtest_institucional.py --mode preliminar     # 1 ano (rápido)
python scripts/backtest_institucional.py --mode estresse_bear  # Bear 2022 (Luna/FTX)
python scripts/backtest_institucional.py --mode estresse_bull  # Bull ETF/Halving
python scripts/backtest_institucional.py --mode estresse_chop  # Lateral 2024
python scripts/backtest_institucional.py --mode all            # Todas em sequência
python scripts/backtest_institucional.py --walkforward         # Validação OOS de qualquer mudança
```

Cada execução sobrescreve o trio padrão: `data/resumo_{modo}.json`, `data/trades_{modo}.csv` e `reports/relatorio_{modo}.md`.

---

## 📊 Resultados Atuais (V2.2 — validada por walk-forward OOS)

*Última auditoria: 22/08/2026 | 552 moedas | R$100k | custos reais Binance*

### Validação Out-of-Sample (4 blocos deslizantes, 2022-09 → 2026-02)

| Config | Trading PnL OOS | PF | Sharpe | DD Máx |
| :--- | :---: | :---: | :---: | :---: |
| V2.1 (antiga) | -R$4.145 | 0.90 | -0.02 | 18.4% |
| **V2.2 (adotada)** | **+R$73.098** | **1.18** | **0.63** | 24.4% |

*Holdout final intocado (2026-02→08): V2.2 -1.2% vs B&H BTC -12.2% (preservação confirmada).*

### Modalidades Oficiais

| Modalidade | Período | Retorno | Win Rate | PF | DD Máx | B&H BTC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Full (7 anos) | 2019-09 → 2026-08 | **+555.2%** | 43.4% | 1.47 | 34.0% | +569.1% |
| 5 anos | 2021-11 → 2026-08 | **+101.5%** | 39.5% | 1.28 | 34.0% | +5.2% |
| Preliminar (1 ano) | 2023-10 → 2024-10 | **+35.2%** | 44.2% | 1.43 | 16.8% | +135.7% |
| Bull (6m) | 2023-10 → 2024-03 | **+38.9%** | 50.0% | 1.92 | 16.8% | +158.9% |
| Bear (1 ano) | 2022 | **+19.7%** | 44.4% | 1.75 | 10.9% | -64.6% |
| Chop (6m) | 2024-04 → 2024-09 | **-2.3%** | 33.3% | 0.78 | 13.7% | -8.7% |

**Leitura honesta:** o sistema iguala o B&H BTC em 7 anos (+555% vs +569%) com ~1/3 do drawdown, vence nas janelas adversas (bear 2022: +19.7% vs -64.6%; 5 anos: +101% vs +5%) e cede upside apenas nos janelões de alta (Bull: +39% vs +159%). Nos 5 anos o trading líquido é de +R$73,2k (vs -R$9,5k da V2.1). Recomendação de alocação padrão: **75% sistema + 25% B&H BTC** (a tabela de híbridos está em cada relatório) e buscar tier VIP de taxas (meta: 0.02%).

---

## 🚀 Como Continuar em uma Nova Conversa

Ao abrir uma nova conversa, você pode simplesmente referenciar o arquivo:
> *"Siga as diretrizes e o protocolo conforme @Prompt.md"*

O arquivo [**`Prompt.md`**](Prompt.md) contém os 3 setores desacoplados e autocontidos:
1. **Setor 1:** Protocolo de Backtest e Auditoria (menu de modalidades + blindagens + walk-forward + armazenamento padrão).
2. **Setor 2:** Prompt Mestre Operacional para análise diária em tempo real (funil quantitativo bi-direcional V2.2).
3. **Setor 3:** Engenharia Quantitativa (motor canônico `scripts/backtest_institucional.py`) e Execução Prática.
