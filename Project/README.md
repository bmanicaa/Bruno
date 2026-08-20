# Sistema Quantitativo de Swing Trade em Criptoativos (180 Dias)

Este repositório contém a arquitetura completa, o protocolo de auditoria e os motores de simulação *point-in-time* (zero lookahead bias) para a estratégia de **Swing Trade Quantitativo Multidimensional** em timeframes de 4h e 1D.

---

## 📁 Estrutura Organizada do Projeto

```
Project/
├── Prompt.md                     # Arquivo Mestre Original (9 Ativos)
├── Prompt2.md                    # Novo Arquivo Mestre (Carteira Dinâmica 3 Moedas / 20 Ativos)
├── README.md                     # Guia Geral e Documentação Executiva
├── data/                         # Datasets de Resultados e Histórico de Trades
│   ├── resumo_estatistico_risco_2_5pct_360d.json         # Comparativo de Risco 2.5% (360d / 180d / 1 Ano)
│   ├── trades_executados_360d_a_180d.csv                 # Livro de ordens (360d a 180d atrás)
│   ├── oportunidades_vetadas_360d_a_180d.csv             # Log de vetos (360d a 180d atrás)
│   ├── resumo_estatistico_360d_a_180d.json               # Resumo estatístico (360d a 180d atrás)
│   ├── trades_executados_mercado_total.csv               # Livro de ordens (Mercado Total Binance)
│   ├── oportunidades_vetadas_mercado_total.csv           # Log de 5.632 vetos do mercado
│   ├── resumo_estatistico_mercado_total.json             # Resumo estatístico (Mercado Total)
│   ├── trades_executados_carteira_dinamica_3moedas.csv   # Livro de ordens (Carteira 3 Moedas)
│   ├── oportunidades_vetadas_carteira_dinamica_3moedas.csv # Vetos da carteira dinâmica
│   ├── resumo_estatistico_carteira_dinamica_3moedas.json # Resumo estatístico (+63,14%)
│   ├── resultado_9_moedas_risco_5pct_com_taxas.csv  # Performance dos 9 ativos iniciais
│   ├── resultado_6_novas_moedas_risco_5pct_com_taxas.csv # Performance dos 6 novos ativos
│   ├── trades_executados_6_novas_moedas.csv         # Livro de ordens dos 6 novos ativos
│   ├── oportunidades_vetadas_6_novas_moedas.csv     # Log de vetos dos 6 novos ativos
│   ├── resumo_estatistico_6_novas_moedas.json       # Estatísticas consolidadas (6 moedas)
│   ├── trades_executados_180d_otimizado.csv         # Livro de ordens detalhado (180d)
│   ├── oportunidades_vetadas_180d_otimizado.csv     # Log de vetos e prejuízos evitados
│   ├── resumo_estatistico_180d_otimizado.json       # Métricas consolidadas (9 moedas)
│   ├── trades_executados_oos.csv                    # Teste Fora da Amostra (NEAR/APT/GALA)
│   ├── oportunidades_vetadas_oos.csv                # Vetos Fora da Amostra
│   └── resumo_estatistico_oos.json                  # Estatísticas Fora da Amostra
├── reports/                      # Relatórios Detalhados em Markdown
│   ├── relatorio_risco_2_5pct_360d.md               # Auditoria Comparativa Risco 2.5% (360d)
│   ├── relatorio_backtest_360d_a_180d.md            # Auditoria Período 360d a 180d atrás
│   ├── relatorio_mercado_total_binance.md           # Auditoria Mercado Total Binance (+45,62%)
│   ├── relatorio_carteira_dinamica_3moedas.md       # Auditoria da Carteira Dinâmica (+63,14%)
│   ├── relatorio_backtest_6_novas_moedas.md         # Auditoria das 6 Novas Criptomoedas
│   ├── relatorio_backtest_180_dias.md               # Auditoria Semestral Consolidada
│   ├── relatorio_backtest_quantitativo.md           # Auditoria dos Primeiros 90 Dias
│   ├── analise_tempo_real_19_08_2026.md             # Snapshot de Tempo Real (Modelo Estrito)
│   └── analise_estrategica_melhorias.md             # Diagnóstico e Otimizações
└── scripts/                      # Motores de Backtest em Python
    ├── backtest_risco_2_5pct_360d.py         # Motor de Risco 2.5% para 360d, 180d e 1 Ano
    ├── backtest_mercado_total_binance.py     # Motor Mercado Total (65 Ativos Líquidos)
    ├── backtest_carteira_dinamica_3moedas.py # Motor da Carteira Dinâmica (3 Moedas / 20 Ativos)
    ├── backtest_6_novas_moedas.py# Motor das 6 Novas Moedas (ARB, RENDER, ONDO, PEPE, AAVE, TIA)
    ├── backtest_engine.py        # Motor Principal (9 Ativos, Risco 5%, Taxas Reais)
    ├── backtest_180d.py          # Motor de Simulação 180 Dias
    └── backtest_out_of_sample.py # Motor de Validação Fora da Amostra
```

---

## 🎯 As Regras Estruturais do Protocolo ([Prompt.md](file:///c:/Users/bmani/Documents/GitHub/Bruno/Project/Prompt.md))

1. **Gestão de Risco & Alocação:** Risco Fixo de **5,0% por trade** ($\text{Alocação} = \frac{5,0\%}{\text{Distância do Stop}}$).
2. **Controle de Correlação da Carteira:** Limite máximo de **2 posições abertas simultaneamente**.
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
