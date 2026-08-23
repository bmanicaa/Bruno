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

## 📊 Resultados Atuais (V2.3.1 — motor corrigido, zero lookahead)

*Última auditoria: 23/08/2026 | 552 moedas | R$100k | custos reais Binance*

> **Para o seu dinheiro real:** o documento [**`PLANO_OPERACIONAL_REAL.md`**](PLANO_OPERACIONAL_REAL.md) contém o passo a passo simples (núcleo Bitcoin + airbag EMA200) baseado na evidência desta auditoria.

### Auditoria de integridade (achado crítico da Fase 0)

A auditoria estatística (bootstrap + testes de regressão) descobriu que a V2.2 usava o fechamento diário do **mesmo dia** (lookahead intra-diário) no gatilho de entrada. A correção (V2.3, merge diário usa apenas o dia completo anterior + notional do short corrigido) **eliminou o edge OOS**:

| Métrica OOS (4 blocos) | V2.2 (bug) | V2.3 (corrigido) |
| :--- | :---: | :---: |
| Trading PnL | +R$73.098 | **-R$12.064** |
| PF / Sharpe | 1.18 / 0.63 | **0.99 / 0.11** |
| P(PF>1) bootstrap | 93,6% | **38,0%** |

### Modalidades Oficiais (motor V2.3.1 limpo)

| Modalidade | Período | Retorno | Win Rate | PF | DD Máx | B&H BTC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Full (7 anos) | 2019-09 → 2026-08 | +92.7% | 37.2% | 1.06 | 34.3% | +569.1% |
| 5 anos | 2021-11 → 2026-08 | +1.9% | 35.4% | 0.92 | 32.5% | +5.2% |
| Preliminar (1 ano) | 2023-10 → 2024-10 | +7.8% | 33.7% | 1.03 | 29.5% | +135.7% |
| Bull (6m) | 2023-10 → 2024-03 | +39.6% | 43.9% | 1.79 | 18.4% | +158.9% |
| Bear (1 ano) | 2022 | +4.1% | 35.7% | 0.94 | 11.7% | -64.6% |
| Chop (6m) | 2024-04 → 2024-09 | -20.6% | 16.7% | 0.17 | 21.4% | -8.7% |

**Leitura honesta:** após 42 configurações em 4 famílias de sinal (swing pullback, meta-labeling ML, momentum cross-sectional, trend time-series), **nenhuma tem edge OOS estatisticamente significativo** sob o protocolo rigoroso (walk-forward + bootstrap + Deflated Sharpe). O B&H BTC não foi batido em retorno total; o valor demonstrável dos sistemas é **redução de risco** (trend-timing BTC EMA200/252 corta o DD pela metade; a config conservadora g3 — BTC/ETH, sem shorts, risco 0,75%, taxa VIP — tem DD ~5%). Recomendação: núcleo B&H BTC + camada opcional de trend-timing + sistemas de swing apenas como satélite de observação, até nova validação.

### Infraestrutura de validação (entregável principal desta fase)

- `tests/` — 15 testes unitários de regressão (sizing, stops, BE/parcial, funding, breakers, identidade contábil).
- `scripts/statistical_validation.py` — bootstrap em blocos, leave-one-out, Deflated Sharpe Ratio.
- `scripts/meta_label.py` — screening de filtro ML (AUC IS = 0.48: sem sinal aprendível).
- `scripts/batch_experiments.py` — baterias de experimentos com 1 carga de dados.
- `scripts/backtest_cs_momentum.py` e `scripts/backtest_trend_bh.py` — famílias de sinal alternativas no mesmo protocolo.
- `PLANO_OPERACIONAL_REAL.md` — plano de carteira real baseado na evidência (núcleo B&H BTC + airbag EMA200).
- Baseline contaminado preservado em `data/experimentos/exp_9ea2dff4_v22_lookahead_baseline.json`.

*Nota V2.3.1:* auditoria externa de mecânica foi avaliada — a ordem funding/stop do motor está correta (velas Binance usam open_time = início; o settlement ocorre na abertura da vela). Único refinamento: notional do funding passou a usar a abertura da vela (delta OOS ≈ 0,08%, cosmético).

---

## 🚀 Como Continuar em uma Nova Conversa

Ao abrir uma nova conversa, você pode simplesmente referenciar o arquivo:
> *"Siga as diretrizes e o protocolo conforme @Prompt.md"*

O arquivo [**`Prompt.md`**](Prompt.md) contém os 3 setores desacoplados e autocontidos:
1. **Setor 1:** Protocolo de Backtest e Auditoria (menu de modalidades + blindagens + walk-forward + armazenamento padrão).
2. **Setor 2:** Prompt Mestre Operacional para análise diária em tempo real (funil quantitativo bi-direcional V2.2).
3. **Setor 3:** Engenharia Quantitativa (motor canônico `scripts/backtest_institucional.py`) e Execução Prática.
