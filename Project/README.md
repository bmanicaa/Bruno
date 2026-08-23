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

*Última auditoria: 24/08/2026 | 552 moedas | R$100k | custos reais Binance*

> **Para o seu dinheiro real:** o documento [**`PLANO_OPERACIONAL_REAL.md`**](PLANO_OPERACIONAL_REAL.md) contém o passo a passo simples (núcleo Bitcoin + airbag EMA200) baseado na evidência desta auditoria.

### Auditoria de integridade (achado crítico da Fase 0)

A auditoria estatística (bootstrap + testes de regressão) descobriu que a V2.2 usava o fechamento diário do **mesmo dia** (lookahead intra-diário) no gatilho de entrada. A correção (V2.3, merge diário usa apenas o dia completo anterior + notional do short corrigido) **eliminou o edge OOS**:

| Métrica OOS (4 blocos) | V2.2 (bug) | V2.3 (corrigido) |
| :--- | :---: | :---: |
| Trading PnL | +R$73.098 | **-R$12.064** |
| PF / Sharpe | 1.18 / 0.63 | **0.99 / 0.11** |
| P(PF>1) bootstrap | 93,6% | **38,0%** |

### Modalidades Oficiais (motor V2.3.1 limpo)

As duas últimas colunas separam o que veio de **operar** do que veio de **dinheiro parado rendendo 6% a.a.** — sem essa separação, três das seis linhas se leem ao contrário do que realmente aconteceram.

| Modalidade | Período | Retorno | PF | DD Máx | B&H BTC | PnL de trading | Cash yield | **Sharpe de trading** |
| :--- | :--- | :---: | :---: | :---: | :---: | ---: | ---: | :---: |
| Full (7 anos) | 2019-09 → 2026-08 | +92.8% | 1.06 | 34.3% | +569.1% | +R$36.776 | +R$56.025 | **+0.26** |
| 5 anos | 2021-11 → 2026-08 | +1.9% | 0.92 | 32.5% | +5.2% | **-R$19.405** | +R$21.294 | **-0.14** |
| Preliminar (1 ano) | 2023-10 → 2024-10 | +7.8% | 1.03 | 29.5% | +135.7% | +R$2.755 | +R$5.029 | **+0.19** |
| Bull (6m) | 2023-10 → 2024-03 | +39.6% | 1.79 | 18.4% | +158.9% | +R$37.493 | +R$2.112 | **+1.99** |
| Bear (1 ano) | 2022 | +4.1% | 0.94 | 11.7% | -64.6% | **-R$1.399** | +R$5.541 | **-0.12** |
| Chop (6m) | 2024-04 → 2024-09 | -20.6% | 0.17 | 21.4% | -8.7% | -R$22.713 | +R$2.142 | **-3.70** |

**Como ler esta tabela (revisão da Fase A):**

- **Bull é o único resultado genuíno.** +R$37,5k de trading contra R$2,1k de caixa, Sharpe de trading +1,99. Em alta confirmada o sistema funciona.
- **"Bear +4,1%" não foi defesa por habilidade.** O trading *perdeu* R$1.399; os +4,1% são o rendimento do caixa. A proteção contra os -64,6% do BTC é real — mas vem de **ficar fora do mercado**, não de operar bem. Isso é o filtro de regime funcionando, não edge.
- **"5 anos +1,9%" esconde uma perda.** O trading queimou R$19.405; o caixa cobriu.
- **Nos 7 anos, 60% do retorno é o caixa** (R$56k de R$92,8k).

**Conclusão de uma linha:** o sistema só ganha dinheiro em bull confirmado; em todo o resto, o "lucro" é o juro do dinheiro parado.

**Leitura honesta:** após 32 configurações limpas e distintas em 4 famílias de sinal (swing pullback, meta-labeling ML, momentum cross-sectional, trend time-series), **nenhuma tem edge OOS estatisticamente significativo** sob o protocolo (walk-forward + bootstrap + Deflated Sharpe). O B&H BTC não foi batido em retorno total; o valor demonstrável dos sistemas é **redução de risco** (trend-timing BTC EMA200/252 corta o DD pela metade). Recomendação: núcleo B&H BTC + camada opcional de trend-timing + sistemas de swing apenas como satélite de observação, até nova validação.

### Fase A (24/08/2026) — auditoria da régua estatística

Antes de gastar mais orçamento de múltiplos testes, os instrumentos de validação foram auditados. Quatro defeitos, todos no sentido de **aprovar demais**:

| Defeito | Efeito medido | Correção |
| :--- | :--- | :--- |
| DSR misturava Sharpe **anualizado** com `n_obs` em **barras de 4h** | Z inflado ~46,8× → g3 marcava **p=1e-12 (PASSA)** contra 60,7% no bootstrap | Desanualiza para a escala por barra → g3 marca **p=0,229 (REPROVA)** |
| Sharpe calculado sobre a curva **com o cash yield dentro** | g3: Sharpe **1,20 → -0,47** ao medir só o trading | `sharpe_trading` (excesso sobre o cash yield) em todo o pipeline |
| Block bootstrap com bloco > n/3 | Família trend marcava **P(PF>1)=100%** com 10 trades | Bloco limitado a n/3 + flag `insufficient_sample` (< 30 trades) |
| 9 experimentos pré-V2.3 sem marcação | Ordenando por PnL, o 1º lugar era contaminado (`b415fc06`, +R$80k) | `invalid_lookahead: true` + exclusão do universo do DSR + dedup por hash |

**A config g3 (`45c0eb3c`) foi reprovada e deixou de ser candidata.** Com a régua corrigida: Sharpe de trading **-0,47**, expectância **-0,049R**, PF mediano **0,64**, perde em **3 dos 4 blocos OOS**, e **82% do retorno era o rendimento do caixa** (R$20,3k de cash yield vs R$4,5k de trading). Não foi uma estratégia que piorou — foi uma medição que ficou honesta.

Também corrigido: `backtest_trend_bh.py` descartava o ETH em silêncio (procurava só em `raw/macro/`), tornando as configs "BTC+ETH" duplicatas das BTC-only. Com o ETH entrando de fato, a família trend melhorou no bruto (+R$64k → +R$116k) — e continua reprovando por amostra insuficiente.

**As 32 configs limpas foram reprocessadas com a métrica correta.** Resultado: **6 têm Sharpe de trading > 0, zero passam** nos critérios endurecidos, e **nenhuma tem ≥3/4 blocos OOS positivos** — quase tudo lucra só na alta do ETF (2023-09→2024-09) e sangra nos outros três blocos.

**Nada foi aprovado indevidamente pelo protocolo antigo — mas por sorte, não por desenho.** Reconstituindo os vereditos antigos das duas configs mais perigosas:

| config | DSR antigo | bootstrap | o que a barrou |
| :--- | :--- | :--- | :--- |
| g3 `45c0eb3c` | p=0,0000 **PASSA** | 60,5% reprova | o bootstrap |
| trend `12616cbc` | p=1,0000 reprova | 97,4% **passa** | o DSR |

Os dois filtros estavam desalinhados em direções opostas e cada um cobriu o buraco do outro. Um teste que discorda do outro por 10 ordens de grandeza na mesma config acerta por acidente. Depois da Fase A os dois **concordam**, e a `12616cbc` passa a ser barrada por três motivos independentes (amostra de 20 trades, concentração em 2/4 blocos, DSR p=0,82) em vez de um acaso.

### Infraestrutura de validação (entregável principal desta fase)

- `tests/` — **22 testes** unitários de regressão (sizing, stops, BE/parcial, funding, breakers, identidade contábil, merge point-in-time + 7 blindagens da régua estatística da Fase A).
- `scripts/statistical_validation.py` — bootstrap em blocos, leave-one-out, Deflated Sharpe Ratio (escala corrigida).
- `scripts/meta_label.py` — screening de filtro ML (AUC IS = 0.48: sem sinal aprendível).
- `scripts/batch_experiments.py` — baterias de experimentos com 1 carga de dados.
- `scripts/reprocess_experiments.py` — re-roda todas as configs limpas quando as métricas do motor mudam (mantém o universo do DSR na mesma escala).
- `scripts/backtest_cs_momentum.py` e `scripts/backtest_trend_bh.py` — famílias de sinal alternativas no mesmo protocolo.
- `PLANO_OPERACIONAL_REAL.md` — plano de carteira real baseado na evidência (núcleo B&H BTC + airbag EMA200).
- Experimentos pré-V2.3 preservados e marcados com `invalid_lookahead: true` (excluídos do universo de múltiplos testes).

*Nota V2.3.1:* auditoria externa de mecânica foi avaliada — a ordem funding/stop do motor está correta (velas Binance usam open_time = início; o settlement ocorre na abertura da vela). Único refinamento: notional do funding passou a usar a abertura da vela (delta OOS ≈ 0,08%, cosmético).

---

## 🚀 Como Continuar em uma Nova Conversa

Ao abrir uma nova conversa, você pode simplesmente referenciar o arquivo:
> *"Siga as diretrizes e o protocolo conforme @Prompt.md"*

O arquivo [**`Prompt.md`**](Prompt.md) contém os 3 setores desacoplados e autocontidos:
1. **Setor 1:** Protocolo de Backtest e Auditoria (menu de modalidades + blindagens + walk-forward + armazenamento padrão).
2. **Setor 2:** Prompt Mestre Operacional para análise diária em tempo real (funil quantitativo bi-direcional V2.2).
3. **Setor 3:** Engenharia Quantitativa (motor canônico `scripts/backtest_institucional.py`) e Execução Prática.
