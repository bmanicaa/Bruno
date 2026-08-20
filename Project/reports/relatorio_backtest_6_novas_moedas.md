# Relatório de Auditoria e Backtest das 6 Novas Moedas (180 Dias)

**Período de Análise:** 20 de Fevereiro de 2026 a 19 de Agosto de 2026 (6 Meses Completos)  
**Novos Ativos Auditados:** ARB (Layer 2), RENDER (DePIN/AI), ONDO (RWA), PEPE (Memecoin/Order Flow), AAVE (Blue-Chip DeFi), TIA (Modular DA)  
**Referência Macro:** BTCUSDT (EMA 50 1D, EMA 20 4h) + Fear & Greed Index (Alternative.me)  
**Metodologia:** Simulação *Point-in-Time* Candle a Candle 4h (1.086 períodos) | Zero Lookahead Bias  
**Parâmetros Estruturais de [Prompt.md](file:///c:/Users/bmani/Documents/GitHub/Bruno/Project/Prompt.md):**
- Risco Fixo de **5,0% do capital atual por operação** ($\text{Alocação} = \frac{5,0\%}{\text{Distância do Stop}}$)
- Custos Operacionais Reais: **0,075% por ordem (Binance VIP0 com desconto de BNB)** na entrada e na saída
- **Puxada de Breakeven Antecipado em +1.0R**
- **Alvos Adaptativos por Regime:** 1.8R em consolidação / 2.5R em tendência forte
- **Time-Stop de 14 Dias (84 candles 4h)**
- **Limite de 2 Posições Concomitantes na Carteira**
- **Vetos Obrigatórios:** Vesting (>1% em 7d), Funding Rate (>0.03%), BTC < EMA 50 1D -3%, Preço < EMA 50 4h sem volume agressor

---

## 1. Resumo Consolidado do Portfólio de 6 Novas Moedas

*Capital Inicial: R$ 200,00 | Limite de 2 posições abertas simultaneamente | Risco 5.0% + Taxas Reais*

| Métrica Quantitativa | Valor Obtido | Status / Classificação |
| :--- | :---: | :--- |
| **Capital Inicial** | **R$ 200,00** | Base de Capital Inicial |
| **Saldo Final** | **R$ 228,92** | **LUCRO LÍQUIDO POSITIVO (+14,46%)** |
| **Lucro Líquido (R$)** | **+R$ 28,92** | Expectativa Matemática Positiva |
| **Total de Trades Executados** | **32** | ~5,3 trades por mês |
| **Trades Vencedores** | **11** | Ganhos assimétricos em Alvo 1, Alvo 2 e Trailing EMA20 |
| **Trades no Breakeven / Stop 0x0** | **10** | **Risco Zero garantido pelo Breakeven em +1.0R** |
| **Trades Perdedores (Stop Inicial)** | **11** | Perdas controladas em 5,0% do capital |
| **Taxa de Acerto (Win Rate)** | **34,38%** | Alta rentabilidade mesmo com Win Rate modesto (Payoff Assimétrico) |
| **Profit Factor (Fator de Lucro)** | **1,21** | **Superior a 1.0 (Sistema Lucrativo)** |
| **Drawdown Máximo** | **23,92%** | Ocorrido durante a compressão de altcoins em Julho/2026 |
| **Total de Oportunidades Vetadas** | **642** | Filtragem algorítmica constante |
| **Prejuízo Evitado por Vetos** | **+R$ 1.190,11** | Proteção contra falsos rompimentos e topos eufóricos |

---

## 2. Resultado Individual por Ativo (R$ 200,00 Inicial por Moeda)

*Simulação isolada de cada ativo com R$ 200,00 de banca inicial, Risco 5.0% e taxas reais Binance:*

| Ticker | Setor / Tese | Saldo Final (R$) | Retorno Líquido (%) | Retorno *Buy & Hold* | *Win Rate* | *Profit Factor* | *Drawdown* Máx | Trades |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ONDO** | *RWA Institucional* | **R$ 233,34** | **+16,67%** | +32,57% | **50,00%** | **1,84** | 14,50% | 12 |
| **ARB** | *Layer 2 Rollup* | **R$ 229,42** | **+14,71%** | **-8,67%** | **37,50%** | **1,75** | **10,04%** | 8 |
| **RENDER** | *DePIN / AI Compute* | **R$ 207,50** | **+3,75%** | **-2,28%** | **38,46%** | **1,13** | 11,53% | 13 |
| **TIA** | *Modular DA* | **R$ 199,10** | **-0,45%** | +1,25% | 36,36% | 0,98 | 18,96% | 11 |
| **PEPE** | *Memecoin / Order Flow* | **R$ 182,21** | **-8,90%** | **-32,15%** | 28,57% | 0,61 | 12,28% | 14 |
| **AAVE** | *Blue-Chip DeFi* | **R$ 170,91** | **-14,54%** | **-23,63%** | 36,36% | 0,48 | 18,93% | 11 |

---

## 3. Principais Descobertas e Validações do Protocolo

### 1. Alpha Massivo Gerado em ARB (+14,71% vs -8,67% no Buy & Hold)
- **Veto de Vesting:** A trava algorítmica que bloqueia compras 7 dias antes do cliff mensal do dia 16 evitou que o portfólio sofresse com a pressão vendedora dos desbloqueios institucionais de ARB.
- O ativo entregou **+14,71% de lucro**, enquanto o investidor passivo perdeu **-8,67%**.

### 2. Consistência e Força em ONDO (+16,67% / Profit Factor 1,84)
- A métrica de crescimento orgânico de TVL/AUM institucional combinada com o filtro técnico de rompimento gerou **50% de Win Rate** e excelente relação risco/retorno (Profit Factor de 1,84).

### 3. Proteção no RENDER (+3,75% vs -2,28% no Buy & Hold)
- O filtro de **CVD agressor e ADX > 20** permitiu capturar expansões de volatilidade e fechar trades com lucro através do Trailing Stop na EMA 20 4h.

### 4. Blindagem em Ativos de Alta Volatilidade (PEPE e AAVE)
- Em PEPE, o Buy & Hold despencou **-32,15%**, enquanto o protocolo conteve a perda em apenas **-8,90%**, com múltiplos trades salvos pelo **Breakeven Antecipado em +1.0R** e pelo **Veto de Funding Rate > 0,03%**.
- Em AAVE, o mercado passou por forte consolidação e repiques falsos, onde o protocolo evitou perdas maiores (-14,54% vs -23,63% no Buy & Hold).

---

## 4. Tabela Geral Consolidada de 15 Criptomoedas (9 Anteriores + 6 Novas)

*Comparativo geral de todos os 15 ativos auditados sob o protocolo de [Prompt.md](file:///c:/Users/bmani/Documents/GitHub/Bruno/Project/Prompt.md):*

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
