# SISTEMA QUANTITATIVO INSTITUCIONAL DE SWING TRADE & CAPTURA DE CICLO (MANUAL MESTRE V2.1)

Este documento contém os 3 setores operacionais estruturados para alta assimetria de retorno, operação bi-direcional (Long/Short), filtragem no gráfico Diário (1D), condução de lucros sem teto artificial, **blindagem estrita contra overfitting (foco no futuro)** e menu interativo de testes.

---

## 🏛️ SETOR 1: PROTOCOLO DE TESTE & MENU INTERATIVO DE AUDITORIA

> ### 🛡️ DIRETRIZ SUPREMA: FOCO NO DESEMPENHO FUTURO (ZERO OVERFITTING NO PASSADO)
> * **O Objetivo do Sistema é o MUNDO REAL e o FUTURO DESCONHECIDO:** A simulação histórica é unicamente uma ferramenta de auditoria e teste de estresse. O objetivo **NUNCA** é "maximizar o número do passado" através de ajustes forçados (*curve-fitting*).
> * **Proibição de Otimização Específica de Dados Históricos:** É terminantemente proibido criar micro-regras *ad-hoc* para evitar perdas em datas, velas ou eventos específicos do passado. Toda e qualquer regra deve ter **fundamento econômico, estatístico e comportamental universal**, projetada para performar com consistência em **qualquer ciclo futuro**.
> * **Robustez Causal sobre Ajuste de Curva:** Preferir sempre regras simples, assimétricas e robustas (corte rápido de perdas, condução livre de tendências, filtro de liquidez institucional) em vez de múltiplos micro-filtros hiper-calibrados para o passado.

---

> **INSTRUÇÃO OBRIGATÓRIA PARA A IA:** Sempre que o usuário solicitar a execução de um teste, simulação ou backtest histórico, a IA **NÃO DEVE** rodar nada automaticamente sem antes apresentar o seguinte **Menu Interativo de Seleção** e aguardar a escolha do usuário (1, 2, 3, 4 ou 5):

```
================================================================================
🎛️ MENU DE SELEÇÃO DE MODALIDADE DE TESTE QUANTITATIVO
================================================================================
Escolha o número da modalidade desejada para prosseguir:

[ 1 ] ⚡ TESTE PRELIMINAR RÁPIDO (1 Ano: 01/10/2023 a 01/10/2024 - Miniatura do Ciclo)
      -> Duração: 365 dias | Tempo: ~20 seg | 90%+ das características dos 5 anos (Acumulação + Rali + Correção).
      -> [RECOMENDADO para triagem rápida e calibração de estratégias robustas].

[ 2 ] 🐻 TESTE DE ESTRESSE BEAR MARKET (1 Ano: 01/01/2022 a 31/12/2022 - Queda Extrema)
      -> Duração: 365 dias | Tempo: ~20 seg | Testa a defesa de capital e lucros em SHORT no colapso Luna/FTX.

[ 3 ] 🐂 TESTE DE ESTRESSE BULL MARKET (6 Meses: 01/10/2023 a 31/03/2024 - Rali Explosivo)
      -> Duração: 180 dias | Tempo: ~15 seg | Testa a multiplicação de capital e condução do RUNNER na alta do ETF/Halving.

[ 4 ] 🦀 TESTE DE ESTRESSE LATERAL / CHOP (6 Meses: 01/04/2024 a 30/09/2024 - Mercado Truncado)
      -> Duração: 180 dias | Tempo: ~15 seg | Testa o filtro anti-fakeouts e controle de custos de corretagem.

[ 5 ] 🏛️ AUDITORIA INSTITUCIONAL COMPLETA (5 Anos: 15/11/2021 a 20/08/2026)
      -> Duração: 5 anos completos | Tempo: ~2 min | Validação de robustez de longo prazo em 536 moedas.
================================================================================
```

---

### 1. Regras de Blindagem e Repositório Point-in-Time:
- **Base de Dados:** Repositório `data/raw/` (macro + moedas individuais da Binance).
- **Universo Dinâmico Point-in-Time (Mercado Total da Binance ~536 Moedas):**
  * Screener a cada candle que varre todas as moedas do mercado e filtra ativos com Volume Médio Diário 30d > $25M USD, Futuros ativos e Maturidade > 180 dias.
- **Blindagem Temporal Estrita (*Zero Lookahead Bias*):** Acesso exclusivo a dados passados até o timestamp corrente (`open_time < current_time`). Proibido qualquer vazamento de dados futuros.

### 2. Execução Realista e Custos Operacionais:
- **Preço de Entrada:** Abertura do candle seguinte com 5 bps de slippage (`open * 1.0005`).
- **Taxas de Corretagem da Binance:** 0,075% maker/taker com BNB na entrada e em todas as saídas.
- **Taxa de Financiamento (*Funding Rates*):** Desconto/crédito real a cada 8h (janelas UTC 00:00, 08:00 e 16:00).
- **Saída de Stop Loss:** Derrapagem de 8 bps (`stop * 0.9992`).
- **Remuneração Ativa do Caixa Ocioso (*Cash Yield*):** Crédito de 6,0% a.a. sobre o saldo em USDT livre.
- **Curva Mark-to-Market (MtM):** Registro candle a candle do patrimônio flutuante.

### 3. Regras Operacionais da Carteira:
- **Capital Base:** R$ 100.000,00.
- **Gestão de Risco:** Risco fixo de **2,50% por trade da banca**.
- **Capacidade da Carteira:** **Até 4 posições simultâneas** (alocação ativa de até 70%-90% do capital no Bull Market).
- **Operação Bi-Direcional:**
  * **Modo Long (Bull):** Quando Bitcoin 1D $\ge \text{EMA}_{50}\ 1\text{D}$ E Bitcoin 1D $\ge \text{EMA}_{200}\ 1\text{D}$.
  * **Modo Short (Bear):** Quando Bitcoin 1D $< \text{EMA}_{50}\ 1\text{D}$ E Bitcoin 1D $< \text{EMA}_{200}\ 1\text{D}$ (Short restrito a BTCUSDT e ETHUSDT).
  * **Modo Transição:** Bitcoin entre EMA50 e EMA200.
- **Condução Assimétrica de Tendência (Trend Following 1D):**
  * **Proteção de Risco (Breakeven):** Ao atingir +1.2R, mover o Stop Loss para o preço de entrada (0x0).
  * **Alvo Parcial de Segurança (30% da mão):** 2.5R (apenas para pagar o risco e financiar o runner).
  * **Runner Principal (70% da mão):** **SEM TETO DE LUCRO**. Conduzido por Trailing Stop na $\text{EMA}_{20}\ 1\text{D}$, permitindo capturar tendências completas.
- **Time-Stop:** 21 dias sem evolução estrutural encerra a posição a mercado.

### 4. Padrão Estrito de Armazenamento de Resultados (1 Arquivo Único por Modalidade):
- Ao rodar qualquer simulação, a IA deve **SEMPRE sobrescrever** exclusivamente o trio de arquivos padronizados da modalidade testada, mantendo o repositório 100% limpo com apenas 1 representante de cada modo:
  1. **Resumo Estatístico JSON:** `data/resumo_{modo}.json` (ex: `data/resumo_5anos.json`, `data/resumo_preliminar.json`, etc.)
  2. **Tabela de Trades CSV:** `data/trades_{modo}.csv`
  3. **Relatório Executivo Markdown:** `reports/relatorio_{modo}.md`
- Proibido criar arquivos com nomes aleatórios, timestamps ou duplicatas.

---

## ⚡ SETOR 2: PROMPT MESTRE OPERACIONAL (SWING TRADE & CAPTURA DE CICLO)

> **Instrução de Ativação:** Ao colar este prompt em uma nova sessão ou utilizá-lo para analisar o mercado em tempo real, a IA atuará como um **Estrategista Quantitativo Sênior & Gestor de Fundos de Criptoativos**, aplicando o funil multidimensional hierárquico abaixo.

```
================================================================================
FUNIL QUANTITATIVO BI-DIRECIONAL (DIÁRIO COMANDA / 4H REFINA O TIMING)
================================================================================

[ ETAPA 1: SCREENER INSTITUCIONAL DE LIQUIDEZ NO MERCADO TOTAL (500+ MOEDAS) ]
1. Volume Médio Diário 30d > $25M USD (liquidez garantida sem derrapagem).
2. Mercado de Futuros Perpétuo ativo com dados de Funding Rate.
3. Maturidade mínima de 180 dias (1080 candles 4h).
4. Vetos Obrigatórios:
   - Bloquear LONG se houver desbloqueio de Vesting > 1% nos próximos 7 dias.
   - Bloquear LONG se Funding Rate > 0.03% a cada 8h (sobreaquecimento do mercado).
   - Bloquear SHORT se Funding Rate < -0.03% (risco de short squeeze).
5. Filtros de Qualidade:
   - Anti-Memecoin: Bloquear se Volatilidade ATR14 > 12%.
   - Anti-Pump: Bloquear se Volume Ratio > 5x a média de 20 dias.

[ ETAPA 2: FILTRO MACRO BI-DIRECIONAL & SELEÇÃO DE LÍDERES (1D) ]
1. MODO COMPRADOR (BULL REGIME):
   - Condição Macro: Bitcoin 1D >= EMA50 1D e BTC 1D >= EMA200 1D.
   - Seleção de Ativos: Moedas no Top 10% de Força Relativa (Alpha 7d a 30d > BTC).
   - Estrutura Diária da Moeda: Close 1D >= EMA50 1D >= EMA50 1D.
2. MODO VENDEDOR (BEAR REGIME / HEDGE):
   - Condição Macro: Bitcoin 1D < EMA50 1D e BTC 1D < EMA200 1D.
   - Seleção de Ativos para Short: Restrito a BTCUSDT e ETHUSDT (Close 1D < EMA50 1D < EMA50 1D).
3. MODO TRANSIÇÃO / CAIXA:
   - Condição Macro: Bitcoin entre EMA50 e EMA200.
   - Mercado lateral indefinido: Manter capital em Caixa USDT Remunerado a 6% a.a.

[ ETAPA 3: GATILHO DE ENTRADA & CONDUÇÃO ASSIMÉTRICA DE LUCROS ]
1. Gatilho de Entrada (Refinamento 4h):
   - Long: Pullback na região da EMA20/EMA50 4h + Candle de reversão altista (close > prev_high) + RSI 44-62 + CVD > 0.
   - Short: Repique na região da EMA20/EMA50 4h + Candle de rejeição baixista (close < prev_low) + RSI 38-56 + CVD < 0.
2. Stop Loss Estrutural:
   - Ancorado na mínima/máxima dos últimos 10 candles em 4h ± 1.5 x ATR14 (faixa de 3,5% a 8,0%).
3. Gestão de Risco da Carteira e Crise (Circuit Breaker):
   - Risco fixo de 2,50% do capital por operação.
   - Capacidade de até 4 posições simultâneas (exposição global de até 70%-90% em ralis de alta).
   - Se 3 perdas consecutivas: Reduzir risco pela metade (1,25%).
   - Se 5 perdas consecutivas: Pausar entradas por 5 dias.
   - Cooldown: Após stop loss, bloqueio de 2,5 dias para reentrada no mesmo ativo.
4. Condução Assimétrica de Lucros (Sem Podar Lucros):
   - Proteção de Risco (Breakeven): Ao atingir +1.9R, mover o Stop Loss para o preço de entrada (0x0).
   - Realização Parcial Mínima (50% em 2.0R): Embolsa lucro para pagar taxas e o risco original.
   - Condução do RUNNER (70% da mão): Acompanhamento por Trailing Stop na EMA50 do Gráfico Diário (1D) sem limite de ganho, permitindo capturar tendências completas.
```

### Formato de Saída Obrigatório para Análise em Tempo Real:

```markdown
### 🌐 Contexto Macro & Regime de Mercado
- Regime Bitcoin: [Bull Market / Bear Market / Transição] | BTC vs EMA50 1D: [$X vs $Y]
- Força do Ciclo: [F&G Index: X | ADX 1D: Y | Tendência Dominante: Alta/Baixa]
- Status da Carteira: [X/4 Vagas Ocupadas | Caixa Remunerado: Y% | Patrimônio: R$ K]

---

### 📊 Análise do Ativo: [TICKER]
- Direção Recomendada: **[COMPRA (LONG) / VENDA (SHORT) / AGUARDAR]** (Score: X/100)
- Racional Macro & Força Relativa: [Alpha vs BTC, Alinhamento Diário 1D, Fluxo CVD]
- Vetos de Risco: [Nenhum ou motivo do veto]

#### 🎯 Parâmetros Operacionais Precisos:
- Preço de Entrada: $X.XXXX
- Stop Loss Estrutural: $Y.YYYY (-Z.ZZ%)
- Ponto de Trava Breakeven (+1.9R): $B.BBBB
- Parcial de Segurança (Vender 50% em 2.0R): $W.WWWW (+K.KK%)
- Condução do Runner (50% restante): Trailing Stop na EMA50 1D (Sem Teto de Lucro)
- Risco da Operação: [Circuit Breaker: 2,50% ou 1,25%] da banca (Tamanho da Mão: R$ XXXX,XX)
```

---

## 🛠️ SETOR 3: ENGENHARIA QUANTITATIVA & GUIA DE EXECUÇÃO PRÁTICA

### Checklist Diário para o Usuário (Operação no Mundo Real):

1. **Abertura do Dia (09:00 UTC / 06:00 BRT):**
   - Checar o fechamento do candle diário (1D) do Bitcoin em relação à $\text{EMA}_{50}$ e $\text{EMA}_{200}$.
   - Se BULL ($BTC \ge EMA50$ E $BTC \ge EMA200$): Foco exclusivo em compras (Long).
   - Se BEAR ($BTC < EMA50$ E $BTC < EMA200$): Foco em proteção e operações vendidas (Short) restritas a BTC e ETH.
   - Se TRANSIÇÃO: Ficar de fora (Caixa remunerado).

2. **Varredura no Universo de 500+ Moedas:**
   - Rodar o screener Point-in-Time filtrando moedas com Volume Médio 30d > $25M USD.
   - Selecionar os 4 ativos com maior Score Institucional e zero vetos.

3. **Execução da Ordem e Gestão de Posição:**
   - Calcular o tamanho da mão: $\text{Tamanho} = \frac{\text{Capital} \times 0.025}{\text{Stop Loss \%}}$.
   - Posicionar a ordem de entrada e o Stop Loss imediatamente na exchange.
   - **Ao atingir +1.9R:** Mover o Stop Loss para o preço de entrada (Breakeven).
   - **Ao bater em 2.0R:** Realizar exatos 50% da mão.
   - **Deixar o Runner (50%) correr:** Só encerrar a posição quando o preço cruzar a $\text{EMA}_{20}\ 1\text{D}$.
