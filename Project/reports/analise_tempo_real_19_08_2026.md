# Análise Operacional Point-in-Time — Formato Estrito do Prompt Mestre
**Data/Hora da Emissão:** 19 de Agosto de 2026 — 20:00 UTC  
**Ativos Cobertos:** SOL, SUI, ILV (+ BTC Macro)  

---

Macro & Regime: [Fear & Greed: 46 (Alternative.me) / 48 (Binance) | BTC.D: 56.2% | DXY: 102.4 | Risco de Liquidação: Baixo]

• SOL — VENDA / REALIZAÇÃO DE POSIÇÃO (Novas Compras: AGUARDAR) (Score: 78/100)
  - Gatilhos Ativos: Tendência de alta forte no 1D e 4h (Preço $85.21 > EMA20 $78.16 > EMA50 $76.71 > EMA200 $74.62). RSI 4h em 88.68 indicando exaustão compradora de curto prazo. Funding Rate saudável em +0.0041% (8h). TVL Solana estável em $5.16B com volume DEX liderando o mercado. Vesting sem cliffs relevantes.
  - Vetos / Invalidações: Para novas entradas a mercado: VETO técnico por assimetria de risco (RSI 4h > 85, preço afastado mais de 9% da EMA 20 4h, impossibilitando Stop com R:R $\ge 2.5:1$). Para posições abertas desde $73.99: Alvo 1 atingido ($82.35), 50% realizado com lucro e Stop dos 50% restantes garantido no Breakeven ($73.99).
  - Parâmetros Operacionais:
    * Entrada: Inativo para novas ordens (Preço atual: $85.21)
    * Stop Loss (100% da posição): $73.99 (Breakeven para posição remanescente)
    * Alvo 1 (Vender 50% + Mover Stop p/ Breakeven): $82.35 (+11.30%) [EXECUTADO] | R:R: 2.5:1
    * Alvo 2 (Vender 50% restantes): $87.36 (+18.08%) ou saída trailing se fechar candle 4h abaixo da EMA 20 ($78.16)
  - Gestão de Capital: Alocação: 0% para novas compras (Manter 50% da posição de swing trade protegida no 0x0).

• SUI — AGUARDAR (Score: 71/100)
  - Gatilhos Ativos: Recuperação no 4h com preço ($0.7044) superando EMA 20 ($0.6719) e EMA 50 ($0.6757). RSI 4h em 70.79. Funding Rate neutro em +0.0074% (8h). TVL Sui em $418M (+4.2% em 7d). Próximo grande cliff de vesting em 01/09/2026 (fora da janela de veto de 7 dias).
  - Vetos / Invalidações: Preço diário (1D) ainda testando a resistência da EMA 50 1D ($0.7194) sem rompimento com candle diário fechado; Score 71/100 (< 75). Aguardar pullback na EMA 20 4h ou rompimento confirmado de $0.7200.
  - Parâmetros Operacionais: Entrada: Inativo | Stop: Inativo | Alvo 1: Inativo | Alvo 2: Inativo | R:R: Inativo
  - Gestão de Capital: Alocação: 0% (Manter 100% em caixa aguardando gatilho).

• ILV — COMPRA (Score: 78/100)
  - Gatilhos Ativos: Estrutura de reversão e rompimento altista no 4h com pivô confirmado (Preço $3.08 > EMA20 $2.97 e EMA50 $2.97). RSI 4h em 62.33 perfeitamente posicionado na janela ideal de impulsão (45-65). Funding rate em +0.0050% (neutro). Volume agressor positivo (CVD positivo nas últimas 24h). Sem eventos de vesting nos próximos 7 dias.
  - Vetos / Invalidações: Nenhum veto violado.
  - Parâmetros Operacionais:
    * Entrada: $3.0800
    * Stop Loss (100% da posição): $2.8550 (-7.31%) [Fundo estrutural 4h - 1.5x ATR]
    * Alvo 1 (Vender 50% + Mover Stop p/ Breakeven): $3.6425 (+18.26%) | R:R: 2.5:1
    * Alvo 2 (Vender 50% restantes): $4.1000 (+33.12%)
  - Gestão de Capital: Alocação sugerida de 13.68% da banca total (R$ 25,94 para uma banca de R$ 189,62), com Risco Fixo de 1.0% do capital (R$ 1,90).
