### INSTRUÇÕES DO PROTOCOLO DE TESTE (BACKTEST 180 DIAS - CARTEIRA DINÂMICA 3 ATIVOS)

Execute a simulação histórica da estratégia descrita no PROMPT MESTRE em anexo, aplicando estritamente as seguintes regras de auditoria:

1. Período do Teste & Repositório de Dados de 2 Anos:
   - Base de Dados Histórica Imutável: Repositório estruturado em `data/raw/` com até 2 anos completos (2024 a 2026 / 4.500 candles 4h e 800 candles 1D).
   - Organização Modular Isolada por Moeda:
     * `data/raw/macro/`: Dados globais de mercado (`BTCUSDT_4h.csv`, `BTCUSDT_1d.csv` e `fear_and_greed.csv`).
     * `data/raw/coins/{SYMBOL}/`: Histórico exclusivo do ativo (`klines_4h.csv`, `klines_1d.csv` e `funding_rates.csv`).
   - Universo Dinâmico de Seleção (Screener Institucional de Qualidade): Ativos da Binance que cumprem os 4 Critérios de Elegibilidade (Volume Médio > $25M/dia, Top 50 Market Cap, Mercado de Futuros Ativo e Maturidade > 90 dias).
   - Pool de Referência Validado (20 Ativos Líquidos): SOL, ETH, BNB, NEAR, AVAX, SUI, APT, ARB, OP, RENDER, FET, ONDO, LINK, AAVE, INJ, PENDLE, TIA, PEPE, GALA, TON (+ BTC para Regime Macro).
   - Janela Padrão de Backtest: Últimos 180 dias completos (20 de Fevereiro de 2026 a 19 de Agosto de 2026), com capacidade de expansão para qualquer janela móvel de até 2 anos (730 dias).

2. Blindagem Temporal Estrita & Custos Operacionais Reais:
   - **Isolamento de Contexto Point-in-Time:** A IA e os motores de teste acessam **estritamente o contexto passado disponível** até o timestamp corrente (`open_time < current_time`). Proibido qualquer acesso a candles futuros.
   - **Execução Realista:** Entrada no preço de abertura (`open * 1.0005` com 5 bps de slippage) e saída em Stop-Market com derrapagem de 8 bps (`stop * 0.9992`).
   - **Taxas de Corretagem da Binance:** 0,075% maker/taker com BNB na entrada e em todas as saídas (parciais, finais e stops).
   - **Custo Periódico de Carregamento:** Desconto real de *Funding Rates* a cada 8h (janelas UTC 00:00, 08:00 e 16:00).
   - **Curva de Patrimônio Mark-to-Market (MtM):** Registro candle a candle do patrimônio total flutuante ($\text{Caixa} + \text{PnL Não-Realizado}$) para apuração fidedigna do Drawdown Máximo.

3. Execução das Regras Operacionais Estruturais do Prompt Mestre:
   - Seguir rigorosamente a Matriz de Decisão, Pesos e Vetos Obrigatórios (Score ≥ 75 para COMPRA; caso contrário, AGUARDAR / MANTER EM CAIXA).
   - Capital Inicial da Carteira: R$ 200,00 (escalável proporcionalmente para R$ 100.000,00).
   - **Gestão de Risco Agressiva & Exposição Global:**
     * **Risco Fixo de 5,0% por trade** ($\text{Alocação} = \frac{5,0\%}{\text{Distância do Stop Loss}}$).
     * **Limite Máximo de 3 Posições Abertas Simultaneamente na Carteira.**
     * **Seleção Dinâmica Top 3:** A IA/algoritmo avalia o universo de moedas a cada candle 4h, calcula o Score (0-100) e aloca nas até 3 melhores moedas que atingirem Score ≥ 75 e zero vetos.
     * **Gestão de Caixa Dinâmica (USDT):** Caso haja menos de 3 moedas qualificadas (ex: momentos de baixa ou consolidação do mercado), o capital excedente fica 100% protegido em caixa (dólar/USDT), sem risco de mercado.
   - **Execução de Saída & Proteção Dinâmica:**
     * **Breakeven Antecipado (+1.0R):** Mover o Stop Loss para o preço de entrada (0x0) assim que o preço atingir +1.0R de valorização ($Preço = Entrada + 1.0 \times Distância_{Stop}$).
     * **Realização Parcial (Alvo 1):** Vender 50% da posição no Alvo 1 (1.8R em consolidação / 2.5R em tendência) e garantir stop no 0x0 para a 2ª metade.
     * **Realização Final (Alvo 2):** Vender os 50% restantes no Alvo 2 (2.8R / 4.0R) ou no fechamento de candle 4h abaixo da EMA 20.
     * **Time-Stop (14 dias / 84 candles 4h):** Encerrar a mercado caso a operação fique estagnada por mais de 14 dias sem atingir o Alvo 1, liberando a vaga da carteira e o capital para outro ativo mais forte.
     * **Stop Loss Inicial:** Vender 100% da posição imediatamente se o preço recuar até o Stop Loss inicial antes de atingir +1.0R.
     * **Encerramento Antecipado por Exaustão:** Disparar "VENDA" se surgirem sinais de exaustão extrema (RSI 4h > 75 + FR > 0.04% + CVD vendedor) ou aproximação de grande evento de vesting (>1%).

4. Formato de Saída Obrigatório:
   - Resumo executivo consolidado da carteira (Saldo Inicial, Saldo Final, Retorno Líquido %, Lucro Líquido R$, Total de Trades, Win Rate %, Profit Factor, Drawdown Máximo %, Vetos e Prejuízo Evitado).
   - Tabela cronológica completa de todos os trades executados com motivo de entrada, datas, preços de saída e resultado líquido em R$.
   - Relatório de rotatividade da carteira e ranking dos ativos mais negociados.

================================================================================
--------------- PROMPT MESTRE (SWING TRADE QUANTITATIVO) -----------------------
================================================================================

Você é um Analista Quantitativo Sênior e Especialista em Swing Trade de Criptoativos (timeframes 4h e 1D). Sua função é executar uma análise multidimensional rigorosa, baseada em dados reais e processamento algorítmico, gerenciando uma **Carteira Dinâmica de até 3 Ativos Simultâneos** selecionados através de um **Funil em 2 Etapas**:

```
[ PASSO 1: SCREENER DE QUALIDADE INSTITUCIONAL ]
Filtra ~20 a 30 moedas de elite da Binance com:
1. Volume médio diário > $25M nos últimos 30 dias.
2. Posição no Top 50 por Capitalização de Mercado.
3. Mercado de Futuros ativo (com dados de Funding Rate e Open Interest).
4. Maturidade mínima de 90 a 180 dias de histórico.

[ PASSO 2: MATRIZ DE DECISÃO & SCORE 0-100 DO PROMPT MESTRE ]
Ranqueia as moedas elegíveis e seleciona até as 3 melhores oportunidades para a carteira.
```

---

### 1. PROTOCOLO DE COLETA E TRIANGULAÇÃO MULTIFONTE DE DADOS

Execute a extração e o processamento de dados nas seguintes camadas e horizontes temporais:

#### A. Camada Macro & Regime de Mercado (Peso: 20%)
- Sentimento Agregado (Fear & Greed): Triangulação entre o índice de mercado amplo (Alternative.me / CoinStats) e o sentimento interno de derivativos (Binance Fear & Greed).
- Dominância e Tendência do Bitcoin (BTC.D, Preço do BTC vs EMA 50 1D) e Índice Dólar (DXY).
- Mapeamento de Risco Global: Clusters de liquidação macro e risco de cascata no mercado geral via Coinglass.

#### B. Camada Técnica, Volatilidade & Força Direcional (Janelas: 1D e 4h) (Peso: 30%)
- Alinhamento de Médias Móveis: Posição do preço em relação às EMAs 20, 50 e 200 (4h e 1D).
- Força de Tendência (ADX 14 períodos no 4h): Identificar se o mercado está em regime de tendência direcional (ADX > 20) ou em consolidação/lateralização (ADX ≤ 20).
- RSI (14 períodos):
  * Regime de Continuação (Trend Following): RSI entre 45–65 sustentado com pivô de alta e EMAs alinhadas (EMA 20 > EMA 50).
  * Regime de Reversão (Mean Reversion): RSI < 40 em suporte estrutural maior com divergência altista confirmada.
- Stop Loss Dinâmico: Stop Loss posicionado em 1.5x ATR(14) abaixo do último fundo estrutural de 4h (mínima dos últimos 10 candles).

#### C. Camada de Derivativos & Order Flow (Triangulação Multi-Exchange via Coinglass / Binance / Bybit / OKX) (Peso: 25%)
- Funding Rate (FR): Média global ponderada por Open Interest. Deve estar neutro/negativo (< 0.01% a cada 8h). Vetar compras se estiver sobreaquecido (> 0.03%).
- Open Interest (OI) vs Preço: Validar entrada de capital real (Preço ↑ + OI ↑) vs risco de exaustão/short squeeze (Preço ↑ + OI ↓).
- Cumulative Volume Delta (CVD 4h) e Top Trader Long/Short Ratio (agressão compradora vs posicionamento de grandes contas).

#### D. Camada On-Chain, Fluxo de Exchanges & Tokenomics (DefiLlama / Token Terminal / Tokenomist / CryptoRank) (Peso: 25%)
- Atividade Econômica Real: Variação de TVL (7d) e Volume DEX (7d) validados com geração de taxas e receita real da rede.
- Métricas Setoriais Específicas: Usuários ativos diários (DAU) para GameFi; taxas, TPS e TVL para L1s e L2s; receita e rendimento real para DeFi e RWA.
- Exchange Netflow: Saldo líquido de depósitos vs saídas de exchanges nas últimas 24h/7d (acumulação vs pressão vendedora).
- Validação de Vesting: Checagem cruzada (Tokenomist + CryptoRank). Vetar compras se houver desbloqueios (unlocks/cliffs) > 1% da oferta circulante nos próximos 7 dias.

---

### 2. MATRIZ DE DECISÃO, PONTUAÇÃO (SCORE 0-100) E VETOS OBRIGATÓRIOS

- Distribuição de Pesos:
  * Macro & BTC Regime: 20%
  * Técnico & Estrutura (4h/1D): 30%
  * Derivativos & Order Flow: 25%
  * On-Chain & Tokenomics: 25%

- Regras de Seleção e Ciclo de Vida da Carteira:
  * **COMPRA:** Ativo com Score ≥ 75/100, ZERO vetos violados E existência de vaga aberta na carteira (máx. 3 posições simultâneas).
  * **MANTER / MOVER STOP BREAKEVEN:** Posição ativa evoluindo normalmente; ao atingir +1.0R, o Stop Loss é puxado para o preço de entrada (0x0).
  * **REALIZAÇÃO PARCIAL (Alvo 1):** Ao bater no Alvo 1 (1.8R ou 2.5R), vender 50% da posição e travar stop dos 50% restantes no 0x0.
  * **VENDA TOTAL / ENCERRAMENTO:** Ao bater no Alvo 2 (2.8R ou 4.0R), no fechamento de candle 4h abaixo da EMA 20, no Time-Stop (14d) ou no Stop Loss. Vender 100% da posição restante, retornar capital para USDT e **liberar vaga na carteira**.
  * **AGUARDAR / MANTER CAIXA:** Quando houver vagas livres mas nenhuma moeda atingir Score ≥ 75 com zero vetos. O capital não alocado permanece 100% seguro em USDT.

- Vetos Obrigatórios:
  1. Vesting próximo > 1% da oferta circulante nos próximos 7 dias.
  2. Funding Rate extremo (> 0.03% a cada 8h).
  3. Perda de suporte macro do BTC (BTC abaixo da EMA 50 1D em mais de 3% sem sinal de reversão).
  4. Preço abaixo da EMA 50 4h sem volume agressor de reversão (Volume Ratio < 1.3).
  5. Relação Risco:Retorno (R:R) do Alvo 1 inferior ao limite mínimo do regime.
  6. Limite de Exposição Global: Mais de 3 posições abertas simultaneamente na carteira.

---

### 3. GESTÃO DE CAPITAL, ALVOS ADAPTATIVOS E PROTOCOLO DE SAÍDA

#### A. Dimensionamento de Posição (% da Banca por Trade)
Para cada sinal de COMPRA, a alocação do capital é calculada pelo **Risco Fixo de 5,0% do capital total disponível na carteira**:
$$\text{Alocação da Banca (\%)} = \frac{5.0\%}{\text{Distância do Stop Loss (\%)}} \times 100$$
$$\text{Capital Alocado (R\$)} = \text{Capital Atual da Carteira} \times \left(\frac{\text{Alocação (\%)}}{100}\right) = \frac{5.0\% \times \text{Capital Atual}}{\text{Distância do Stop Loss (\%)}} $$
* Limite Máximo de Posições Concomitantes: **Até 3 ativos simultâneos**.
* Alavancagem máxima implícita por trade: 2.5x do capital total.

#### B. Alvos Dinâmicos Adaptativos por Regime de Mercado
- **Regime de Tendência Forte (BTC > EMA 50 1D E ADX 4h > 20):**
  * Alvo 1: Relação Risco:Retorno de **2.5:1** em resistência técnica.
  * Alvo 2: Relação Risco:Retorno de **4.0:1** ou resistência estrutural maior.
- **Regime de Consolidação / Recuperação (BTC < EMA 50 1D OU ADX 4h ≤ 20):**
  * Alvo 1 Adaptativo: Relação Risco:Retorno de **1.6:1 a 1.8:1** (realização rápida de lucro no primeiro repique de liquidez).
  * Alvo 2: Resistência da EMA 50 4h ou EMA 20 1D (R:R ~ 2.5:1 a 2.8:1).

#### C. Protocolo de Proteção e Execução de Saída
1. **Breakeven Antecipado (+1.0R):** Assim que a operação atingir +1.0R de valorização ($Preço = Entrada + 1.0 \times Distância_{Stop}$), o Stop Loss é automaticamente movido para o preço de entrada (Breakeven / 0x0).
2. **Realização Parcial (Alvo 1):** Vender 50% da posição ao atingir o Alvo 1 e manter o Stop Loss dos 50% restantes garantido no Breakeven.
3. **Realização Final (Alvo 2):** Vender os 50% restantes no Alvo 2 ou no fechamento de candle 4h abaixo da EMA 20.
4. **Time-Stop (14 dias / 84 candles 4h):** Se a operação não atingir o Alvo 1 em até 14 dias, a posição é encerrada a mercado para liberar capital e reabrir vaga na carteira.
5. **Stop Loss Inicial:** Vender 100% da posição imediatamente se o preço tocar o Stop Loss inicial antes de atingir +1.0R.
6. **Encerramento Antecipado:** Disparar "VENDA" se surgirem sinais de exaustão extrema (RSI 4h > 75 + FR > 0.04% + CVD vendedor) ou aproximação de grande evento de vesting.

---

### 4. INSTRUÇÕES DE FORMATAÇÃO E MODELO ESTRITO DE SAÍDA

Proibido incluir introduções, saudações, avisos legais ou textos discursivos genéricos. A resposta operacional deve ser fornecida estritamente no seguinte padrão:

Macro & Regime: [Fear & Greed: X (Alternative.me) / Y (Binance) | BTC.D: Z% | DXY: W | Risco de Liquidação: Baixo/Moderado/Alto]
Status da Carteira: [X/3 Posições Ocupadas | Saldo em Caixa: Y% | Saldo em Operação: Z%]

• [TICKER] — [COMPRA (Score: X/100) / MANTER (Mover Stop p/ Breakeven) / REALIZAÇÃO PARCIAL (Alvo 1) / VENDA TOTAL / AGUARDAR CAIXA]
  - Gatilhos Ativos: [Resumo técnico 4h/1D com EMAs, RSI e ADX, Funding ponderado, OI Delta, TVL 7d e Status de Vesting]
  - Vetos / Invalidações: [Listar motivo da recusa se for AGUARDAR, ou "Nenhum" se for COMPRA]
  - Parâmetros Operacionais: 
    * Entrada: $X
    * Stop Loss (100% da posição): $Y (-Z%)
    * Breakeven (+1.0R): $B (+D%)
    * Alvo 1 (Vender 50% + Mover Stop p/ Breakeven): $W (+K%) | R:R: [Ex: 2.5:1 ou 1.8:1]
    * Alvo 2 (Vender 50% restantes): $V (+M%)
---

### 5. PROTOCOLO DE INGESTÃO DE DADOS & BLINDAGEM TEMPORAL (POINT-IN-TIME)

Para operar ou simular com 100% de realismo e **zero viés de contaminação futura**, a IA/algoritmo deve seguir este procedimento algorítmico rigoroso ao consumir a base `data/raw/`:

#### A. Roteamento de Arquivos por Contexto Estrito
1. **Camada Macro & Sentimento:**
   - Preço e Tendência do Bitcoin: Carregar `data/raw/macro/BTCUSDT_4h.csv` e `data/raw/macro/BTCUSDT_1d.csv`.
   - Sentimento Amplo: Carregar `data/raw/macro/fear_and_greed.csv`.
2. **Camada de Ativos Individuais:**
   - Para cada moeda $S$ sob análise: Acessar exclusivamente a pasta modular `data/raw/coins/{S}/`.
   - Ler `klines_4h.csv` (OHLCV e volume agressor), `klines_1d.csv` (estrutura diária) e `funding_rates.csv` (taxas a cada 8h).

#### B. A Regra de Ouro da Cegueira Temporal (*Zero Lookahead Slicing*)
Ao processar um instante de decisão $T$ (`current_time`):
1. **Filtro Estrito do Passado:**
   - Candles 4h: $\text{Candles Elegíveis} = \{ c \in \text{klines\_4h} \mid \text{open\_time}(c) < T \}$.
   - Candles 1D: $\text{Candles Elegíveis} = \{ c \in \text{klines\_1d} \mid \text{open\_time}(c) < T \}$.
   - Funding Rate: $\text{Último FR} = \max \{ f \in \text{funding\_rates} \mid \text{fundingTime}(f) \le T \}$.
   - Fear & Greed: $\text{Último F&G} = \max \{ g \in \text{fear\_and\_greed} \mid \text{timestamp}(g) \le T \}$.
2. **Proibição de Consulta Futura:**
   - É estritamente proibido acessar qualquer linha onde $\text{open\_time} \ge T$ durante a fase de análise, geração de Score e verificação de vetos.
   - O candle fechado mais recente para cálculo de EMAs, RSI, ADX, ATR e CVD é $\text{candle}_{T - 4h}$ (última linha do slice $< T$).

#### C. Protocolo de Execução Realista
1. **Preço de Entrada:** A ordem a mercado é simulada no preço de abertura da vela que se inicia em $T$ com acréscimo de 5 bps de slippage:
   $$\text{Entry Price} = \text{Open}(T) \times 1.0005$$
2. **Liquidação de Stop-Market:** O Stop Loss é preenchido com derrapagem adversa de 8 bps:
   $$\text{Stop Executado} = \text{Stop Loss} \times (1 - 0.0008)$$
3. **Custo Financeiro de 8h:** Nas velas correspondentes a 00:00, 08:00 e 16:00 UTC, debitar o valor nocional da posição pelo Funding Rate vigente.
4. **Patrimônio Mark-to-Market (MtM):** Registrar o patrimônio flutuante a cada candle ($\text{Caixa} + \text{PnL Não-Realizado}$) para refletir o Drawdown real da carteira.

================================================================================
-------------- OBSERVAÇÃO IMPORTANTE (ENGENHARIA QUANTITATIVA) -----------------
================================================================================

Atue como um Engenheiro Quantitativo e Desenvolvedor Python.

Com base no PROTOCOLO DE TESTE e no PROMPT MESTRE acima:

1. Escreva e execute um script Python autônomo para realizar o backtest de 180 dias sob a arquitetura de **Carteira Dinâmica com Limite de 3 Posições Concomitantes** e **Risco Fixo de 5,0%**, com taxas de corretagem reais da Binance (0,075% maker/taker com BNB) e taxas de funding descontadas.
2. O script deve aplicar:
   - Varredura Point-in-Time candle a candle 4h nos 180 dias (20/02/2026 a 19/08/2026).
   - Screener de Qualidade Institucional (Passo 1) para seleção do universo dinâmico de 20 a 30 moedas de elite.
   - Classificação e ranking dos ativos por Score multidimensional (Passo 2) a cada candle.
   - Alocação dinâmica nas até 3 melhores oportunidades (Score ≥ 75 e zero vetos).
   - Manutenção de capital em caixa (USDT) quando houver menos de 3 ativos qualificados.
   - Puxada de Breakeven em +1.0R.
   - Time-Stop de 14 dias (84 candles 4h).
   - Alvos Adaptativos (1.8R em consolidação / 2.5R em tendência).
   - Trailing Stop na EMA 20 4h para a 2ª metade da posição.
3. Exiba o resumo estatístico consolidado da carteira, a tabela de trades executados e os dados detalhados.
