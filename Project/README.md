# Sistema Quantitativo de Swing Trade em Criptoativos (180 Dias)

Este repositório contém a arquitetura completa, o protocolo de auditoria e os motores de simulação *point-in-time* (zero lookahead bias) para a estratégia de **Swing Trade Quantitativo Multidimensional** em timeframes de 4h e 1D.

---

## 📁 Estrutura Organizada do Projeto

```
Project/
├── Prompt.md                     # Arquivo Mestre (Carteira Dinâmica 3 Moedas / 20 Ativos)
├── README.md                     # Guia Geral e Documentação Executiva
├── data/
│   ├── raw/                      # 🌟 DADOS BRUTOS IMUTÁVEIS (2 Anos: 2024–2026 / Binance)
│   │   ├── universe_metadata.json# Metadados globais do reservatório de dados
│   │   ├── macro/                # Referência Macro & Sentimento Global
│   │   │   ├── BTCUSDT_4h.csv    # 4.500 velas 4h do Bitcoin (Benchmark)
│   │   │   ├── BTCUSDT_1d.csv    # 800 velas diárias do Bitcoin
│   │   │   └── fear_and_greed.csv# Histórico diário do Fear & Greed Index
│   │   └── coins/                # Datasets Modulares Isolados por Ativo
│   │       ├── SOLUSDT/          # [klines_4h.csv, klines_1d.csv, funding_rates.csv]
│   │       ├── ETHUSDT/          # [klines_4h.csv, klines_1d.csv, funding_rates.csv]
│   │       ├── SUIUSDT/          # [klines_4h.csv, klines_1d.csv, funding_rates.csv]
│   │       └── [SYMBOL]/         # Estrutura modular idêntica para todas as moedas
│   │
│   └── [Arquivos .csv e .json de resultados serão gerados ao executar os scripts]
├── reports/                      # Relatórios de Auditoria (Pronto para novas execuções)
└── scripts/                      # Motores de Backtest e Utilitários
    ├── download_raw_market_data.py           # Downloader de Dados Brutos (2 Anos / Binance)
    ├── backtest_carteira_dinamica_3moedas.py # Motor da Carteira Dinâmica (3 Moedas / 20 Ativos)
    ├── backtest_engine.py                    # Motor Principal de Validação Monomoeda
    └── backtest_mercado_total_binance.py     # Motor de Varredura do Mercado Amplo
```

---

## 🗄️ Repositório de Dados Brutos de Mercado (`data/raw/`)

Para garantir **zero viés de contaminação temporal** e permitir que qualquer IA acesse **estritamente o contexto necessário** para tomada de decisões:

1. **Isolamento Total por Moeda (`data/raw/coins/{SYMBOL}/`):**
   - Cada pasta contém exclusivamente os 3 arquivos brutos do ativo (`klines_4h.csv`, `klines_1d.csv` e `funding_rates.csv`).
   - A IA/algoritmo só precisa carregar o arquivo da moeda que estiver analisando no momento.

2. **Cegueira Temporal (*Point-in-Time Slicing*):**
   - Em qualquer instante de simulação $T$, o sistema filtra as linhas onde `open_time < T`.
   - Nenhuma informação futura (candles seguintes, preços de fechamento futuros) é visível no momento da avaliação.

---

## 🎯 As Regras Estruturais do Protocolo ([Prompt.md](Prompt.md))

1. **Gestão de Risco & Alocação:** Risco Fixo de **5,0% por trade** ($\text{Alocação} = \frac{5,0\%}{\text{Distância do Stop}}$).
2. **Controle de Correlação da Carteira:** Limite máximo de **3 posições abertas simultaneamente**.
3. **Breakeven Antecipado em +1.0R:** Ao atingir $+1.0R$ de valorização, o Stop Loss é automaticamente movido para o preço de entrada (0x0).
4. **Alvos Adaptativos por Regime (ADX / EMAs):**
   - *Tendência Forte ($BTC > EMA\ 50\ 1D$ e $ADX > 20$):* Alvo 1 em **$2.5R$** e Alvo 2 em **$4.0R$**.
   - *Consolidação / Recuperação:* Alvo 1 em **$1.8R$** (lucro rápido) e Alvo 2 na resistência da EMA 50 4h.
5. **Time-Stop de 14 Dias (84 candles 4h):** Se a operação ficar estagnada sem atingir o Alvo 1 em 14 dias, é encerrada a mercado para liberar capital.
6. **Vetos Obrigatórios:** Bloqueio de compras em semanas de desbloqueio de *Vesting* (>1%), *Funding Rate* extremo (>0.03%), perda de suporte do BTC ou preço abaixo da EMA 50 sem volume.

---

## 📊 Resumo de Performance das 6 Novas Criptomoedas (180 Dias — Risco 5% + Taxas Reais)

*Período: 20 de Fevereiro de 2026 a 19 de Agosto de 2026 | Capital Inicial: R$ 200,00 por moeda*

| Ticker | Perfil do Ativo | Saldo Final (R$) | Retorno Líquido (%) | Retorno *Buy & Hold* | *Win Rate* | *Profit Factor* | *Drawdown* Máx |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ONDO** | *RWA Institucional* | **R$ 233,34** | **+16,67%** | +32,57% | **50,00%** | **1,84** | 14,50% |
| **ARB** | *Layer 2 Rollup* | **R$ 229,42** | **+14,71%** | **-8,67%** | 37,50% | **1,75** | **10,04%** |
| **RENDER** | *DePIN / AI Compute* | **R$ 207,50** | **+3,75%** | **-2,28%** | 38,46% | **1,13** | 11,53% |
| **TIA** | *Modular DA* | **R$ 199,10** | **-0,45%** | +1,25% | 36,36% | 0,98 | 18,96% |
| **PEPE** | *Memecoin / Order Flow* | **R$ 182,21** | **-8,90%** | **-32,15%** | 28,57% | 0,61 | 12,28% |
| **AAVE** | *Blue-Chip DeFi* | **R$ 170,91** | **-14,54%** | **-23,63%** | 36,36% | 0,48 | 18,93% |

---

## 🏆 Tabela Consolidada de Todos os 15 Ativos Auditados (Risco 5% + Taxas Reais)

| Ticker | Perfil / Setor | Saldo Final (R$) | Retorno Líquido (%) | Retorno *Buy & Hold* | *Win Rate* | *Profit Factor* |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **NEAR** | *Major Layer 1* | **R$ 248,58** | **+24,29%** | +72,10% | 45,45% | **1,86** |
| **INJ** | *DeFi / L1 Derivativos* | **R$ 242,57** | **+21,29%** | +40,17% | 46,15% | **1,92** |
| **ONDO** 🆕 | *RWA Institucional* | **R$ 233,34** | **+16,67%** | +32,57% | **50,00%** | **1,84** |
| **ARB** 🆕 | *Layer 2 Rollup* | **R$ 229,42** | **+14,71%** | **-8,67%** | 37,50% | **1,75** |
| **RENDER** 🆕| *DePIN / AI Compute* | **R$ 207,50** | **+3,75%** | **-2,28%** | 38,46% | **1,13** |
| **GALA** | *GameFi / Metaverso* | **R$ 203,23** | **+1,61%** | **-62,82%** | 42,86% | **1,08** |
| **ILV** | *GameFi / Mid-Cap* | **R$ 202,61** | **+1,31%** | **-18,30%** | 41,67% | **1,05** |
| **TIA** 🆕 | *Modular DA* | **R$ 199,10** | **-0,45%** | +1,25% | 36,36% | 0,98 |
| **PENDLE** | *DeFi Yields* | **R$ 196,38** | **-1,81%** | +20,30% | 30,77% | 0,94 |
| **APT** | *Move-VM L1 (Vesting)* | **R$ 194,79** | **-2,61%** | **-34,99%** | 33,33% | 0,80 |
| **SOL** | *Major Layer 1* | **R$ 186,18** | **-6,91%** | +3,65% | 38,46% | 0,80 |
| **PEPE** 🆕 | *Memecoin / Order Flow*| **R$ 182,21** | **-8,90%** | **-32,15%** | 28,57% | 0,61 |
| **SUI** | *Move-VM L1 (Vesting)* | **R$ 178,81** | **-10,59%** | **-23,89%** | 25,00% | 0,61 |
| **TON** | *Telegram L1* | **R$ 177,68** | **-11,16%** | +17,04% | 14,29% | 0,55 |
| **AAVE** 🆕 | *Blue-Chip DeFi* | **R$ 170,91** | **-14,54%** | **-23,63%** | 36,36% | 0,48 |

---

## 🚀 Como Continuar em uma Nova Conversa

Ao abrir uma nova conversa, você pode simplesmente referenciar o arquivo:
> *"Siga as diretrizes e o protocolo conforme @Prompt.md"*

O arquivo [**`Prompt.md`**](file:///c:/Users/bmani/Documents/GitHub/Bruno/Project/Prompt.md) contém os 3 setores desacoplados e autocontidos:
1. **Setor 1:** Protocolo de Backtest e Auditoria.
2. **Setor 2:** Prompt Mestre Operacional para análise diária em tempo real.
3. **Setor 3:** Instruções de Engenharia Quantitativa e Execução.
