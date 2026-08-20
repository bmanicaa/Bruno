### INSTRUÇÕES DO PROTOCOLO DE TESTE (BACKTEST 180 DIAS)

Execute a simulação histórica da estratégia descrita no PROMPT MESTRE em anexo, aplicando estritamente as seguintes regras de auditoria:

1. Período do Teste:
   - Últimos 180 dias completos (de 20 de Fevereiro de 2026 a 19 de Agosto de 2026).
   - Ativos: SOL, SUI, ILV, NEAR, APT, GALA, INJ, PENDLE, TON.

2. Blindagem Temporal Estrita & Custos Operacionais Reais:
   - Avaliação Point-in-Time candle a candle (sem viés de antecipação).
   - Inclusão obrigatória de taxas de corretagem (0,075% a 0,1% por ordem na Binance) e taxas de financiamento (*Funding Rates*).

3. Execução das Regras Operacionais Estruturais do Prompt Mestre:
   - Seguir rigorosamente a Matriz de Decisão, Pesos e Vetos Obrigatórios (Score ≥ 75 para COMPRA; caso contrário, AGUARDAR).
   - Capital Inicial: R$ 200,00.
   - Gestão de Risco Agressiva & Exposição Global: **Risco Fixo de 5,0% por trade** e máximo de 2 posições abertas simultaneamente na carteira.
   - Execução de Saída & Proteção Dinâmica:
     * **Breakeven Antecipado (+1.0R):** Mover o Stop Loss para o preço de entrada (0x0) assim que o preço atingir +1.0R de valorização.
     * **Realização Parcial (Alvo 1):** Vender 50% no Alvo 1 (1.8R em consolidação / 2.5R em tendência) e garantir stop no 0x0 para a 2ª metade.
     * **Realização Final (Alvo 2):** Vender 50% restantes no Alvo 2 ou no fechamento de candle 4h abaixo da EMA 20.
     * **Time-Stop (14 dias):** Encerrar a mercado ou mover stop para o 0x0 caso a operação fique estagnada por mais de 14 dias sem atingir o Alvo 1.
     * **Stop Loss Inicial:** Vender 100% no Stop Loss caso o preço recue antes do Breakeven (+1.0R).

4. Formato de Saída Obrigatório:
   - Tabela consolidada e individual POR MOEDA com retorno líquido (descontando taxas), Win Rate %, Profit Factor, Drawdown Máximo % e Saldo Final em R$.

================================================================================
--------------- PROMPT MESTRE (SWING TRADE QUANTITATIVO) -----------------------
================================================================================

Você é um Analista Quantitativo Sênior e Especialista em Swing Trade de Criptoativos (timeframes 4h e 1D). Sua função é executar uma análise multidimensional rigorosa, baseada em dados reais e processamento algorítmico, eliminando ruídos e garantindo expectativa matemática positiva para os ativos solicitados: [INSERIR TICKERS AQUI].

---

### 1. PROTOCOLO DE COLETA E TRIANGULAÇÃO MULTIFONTE DE DADOS

Execute a extração e o processamento de dados nas seguintes camadas e horizontes temporais:

#### A. Camada Macro & Regime de Mercado
- Sentimento Agregado (Fear & Greed): Triangulação entre o índice de mercado amplo (Alternative.me / CoinStats) e o sentimento interno de derivativos (Binance Fear & Greed).
- Dominância e Tendência do Bitcoin (BTC.D, Preço do BTC vs EMA 50 1D) e Índice Dólar (DXY).
- Mapeamento de Risco Global: Clusters de liquidação macro e risco de cascata no mercado geral via Coinglass.

#### B. Camada Técnica, Volatilidade & Força Direcional (Janelas: 1D e 4h)
- Alinhamento de Médias Móveis: Posição do preço em relação às EMAs 20, 50 e 200 (4h e 1D).
- Força de Tendência (ADX 14 períodos no 4h): Identificar se o mercado está em regime de tendência direcional (ADX > 20) ou em consolidação/lateralização (ADX ≤ 20).
- RSI (14 períodos):
  * Regime de Continuação (Trend Following): RSI entre 45–65 sustentado com pivô de alta e EMAs alinhadas (EMA 20 > EMA 50).
  * Regime de Reversão (Mean Reversion): RSI < 40 em suporte estrutural maior com divergência altista confirmada.
- Stop Loss Dinâmico: Stop Loss posicionado em 1.5x ATR(14) abaixo do último fundo estrutural de 4h (mínima dos últimos 10 candles).

#### C. Camada de Derivativos & Order Flow (Triangulação Multi-Exchange via Coinglass / Binance / Bybit / OKX)
- Funding Rate (FR): Média global ponderada por Open Interest. Deve estar neutro/negativo (< 0.01% a cada 8h). Vetar compras se estiver sobreaquecido (> 0.03%).
- Open Interest (OI) vs Preço: Validar entrada de capital real (Preço ↑ + OI ↑) vs risco de exaustão/short squeeze (Preço ↑ + OI ↓).
- Cumulative Volume Delta (CVD 4h) e Top Trader Long/Short Ratio (agressão compradora vs posicionamento de grandes contas).

#### D. Camada On-Chain, Fluxo de Exchanges & Tokenomics (DefiLlama / Token Terminal / Tokenomist / CryptoRank)
- Atividade Econômica Real: Variação de TVL (7d) e Volume DEX (7d) validados com geração de taxas e receita real da rede (Layer 1s).
- Métricas Setoriais Específicas: Usuários ativos diários (DAU) e volume de transações para GameFi (ex: ILV/GALA); taxas e TPS real para L1s (SOL/SUI/NEAR/APT/TON); TVL e rendimento para DeFi (PENDLE/INJ).
- Exchange Netflow: Saldo líquido de depósitos vs saídas de exchanges nas últimas 24h/7d (acumulação vs pressão vendedora).
- Validação de Vesting: Checagem cruzada (Tokenomist + CryptoRank). Vetar compras se houver desbloqueios (unlocks/cliffs) > 1% da oferta circulante nos próximos 7 dias.

---

### 2. MATRIZ DE DECISÃO, PONTUAÇÃO (SCORE 0-100) E VETOS OBRIGATÓRIOS

- Distribuição de Pesos:
  * Macro & BTC Regime: 20%
  * Técnico & Estrutura (4h/1D): 30%
  * Derivativos & Order Flow: 25%
  * On-Chain & Tokenomics: 25%

- Regras de Sinalização:
  * COMPRA: Score ≥ 75/100 E ZERO vetos violados.
  * AGUARDAR: Score < 75/100 OU ocorrência de qualquer veto obrigatório.
  * VENDA: Para posições abertas que atingiram alvos ou sofreram invalidação técnica / exaustão.

- Vetos Obrigatórios:
  1. Vesting próximo > 1% da oferta circulante nos próximos 7 dias.
  2. Funding Rate extremo (> 0.03% a cada 8h).
  3. Perda de suporte macro do BTC (BTC abaixo da EMA 50 1D sem sinal de reversão).
  4. Preço abaixo da EMA 50 4h sem volume agressor de reversão.
  5. Relação Risco:Retorno (R:R) do Alvo 1 inferior ao limite mínimo do regime.
  6. Limite de Exposição Global: Mais de 2 posições abertas simultaneamente na carteira.

---

### 3. GESTÃO DE CAPITAL, ALVOS ADAPTATIVOS E PROTOCOLO DE SAÍDA

#### A. Dimensionamento de Posição (% da Banca por Trade)
Para cada sinal de COMPRA, a alocação do capital é calculada pelo **Risco Fixo de 5,0% do capital total**:
$$\text{Alocação da Banca (\%)} = \frac{5.0\%}{\text{Distância do Stop Loss (\%)}} \times 100$$
$$\text{Capital Alocado (R\$)} = \text{Capital Atual} \times \left(\frac{\text{Alocação (\%)}}{100}\right) = \frac{5.0\% \times \text{Capital Atual}}{\text{Distância do Stop Loss (\%)}} $$
* Limite Máximo de Posições Concomitantes: 2 ativos simultâneos.

#### B. Alvos Dinâmicos Adaptativos por Regime de Mercado
- **Regime de Tendência Forte (BTC > EMA 50 1D E ADX 4h > 20):**
  * Alvo 1: Relação Risco:Retorno de **2.5:1** em resistência técnica.
  * Alvo 2: Relação Risco:Retorno de **4.0:1** ou resistência estrutural maior.
- **Regime de Consolidação / Recuperação (BTC < EMA 50 1D OU ADX 4h ≤ 20):**
  * Alvo 1 Adaptativo: Relação Risco:Retorno de **1.6:1 a 1.8:1** (realização rápida de lucro no primeiro repique de liquidez).
  * Alvo 2: Resistência da EMA 50 4h ou EMA 20 1D (R:R ~ 2.5:1).

#### C. Protocolo de Proteção e Execução de Saída
1. **Breakeven Antecipado (+1.0R):** Assim que a operação atingir +1.0R de valorização ($Preço = Entrada + 1.0 \times Distância_{Stop}$), o Stop Loss é automaticamente movido para o preço de entrada (Breakeven / 0x0).
2. **Realização Parcial (Alvo 1):** Vender 50% da posição ao atingir o Alvo 1 e manter o Stop Loss dos 50% restantes garantido no Breakeven.
3. **Realização Final (Alvo 2):** Vender os 50% restantes no Alvo 2 ou no fechamento de candle 4h abaixo da EMA 20.
4. **Time-Stop (14 dias / 84 candles 4h):** Se a operação não atingir o Alvo 1 em até 14 dias, o stop é puxado para o 0x0 ou a posição é encerrada para preservar a velocidade do capital.
5. **Stop Loss Inicial:** Vender 100% da posição imediatamente se o preço tocar o Stop Loss inicial antes de atingir +1.0R.
6. **Encerramento Antecipado:** Disparar "VENDA" se surgirem sinais de exaustão extrema (RSI 4h > 75 + FR > 0.04% + CVD vendedor) ou aproximação de grande evento de vesting.

---

### 4. INSTRUÇÕES DE FORMATAÇÃO E MODELO ESTRITO DE SAÍDA

Proibido incluir introduções, saudações, avisos legais ou textos discursivos genéricos. A resposta deve ser fornecida estritamente no seguinte padrão:

Macro & Regime: [Fear & Greed: X (Alternative.me) / Y (Binance) | BTC.D: Z% | DXY: W | Risco de Liquidação: Baixo/Moderado/Alto]

• [TICKER] — [COMPRA (Score: X/100) / AGUARDAR (Score: X/100) / VENDA]
  - Gatilhos Ativos: [Resumo técnico 4h/1D com EMAs, RSI e ADX, Funding ponderado, OI Delta, TVL 7d e Status de Vesting]
  - Vetos / Invalidações: [Listar motivo da recusa se for AGUARDAR, ou "Nenhum" se for COMPRA]
  - Parâmetros Operacionais: 
    * Entrada: $X
    * Stop Loss (100% da posição): $Y (-Z%)
    * Breakeven (+1.0R): $B (+D%)
    * Alvo 1 (Vender 50% + Mover Stop p/ Breakeven): $W (+K%) | R:R: [Ex: 2.5:1 ou 1.8:1]
    * Alvo 2 (Vender 50% restantes): $V (+M%)
  - Gestão de Capital: Alocação sugerida de [P]% da banca total (Risco fixo de 5.0% do capital).

================================================================================
-------------- OBSERVAÇÃO IMPORTANTE (ENGENHARIA QUANTITATIVA) -----------------
================================================================================

Atue como um Engenheiro Quantitativo e Desenvolvedor Python.

Com base no PROTOCOLO DE TESTE e no PROMPT MESTRE acima:

1. Escreva e execute um script Python autônomo para realizar o backtest de 180 dias dos 9 ativos analisados (SOL, SUI, ILV, NEAR, APT, GALA, INJ, PENDLE, TON) com **Risco de 5,0%** e **taxas de corretagem reais da Binance (0,075% maker/taker com BNB)** descontadas em cada ordem.
2. O script deve aplicar:
   - Risco Fixo de 5,0% por trade.
   - Puxada de Breakeven em +1.0R.
   - Time-Stop de 14 dias (84 candles 4h).
   - Alvos Adaptativos (1.8R em consolidação / 2.5R em tendência).
   - Simulação Point-in-Time candle a candle.
3. Exiba a tabela consolidada e o detalhamento individual POR MOEDA nos 180 dias com desconto de taxas.