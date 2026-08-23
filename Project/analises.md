# Registro de Análises — Índice e Estado do Projeto

> **LEIA PRIMEIRO:** as seções 1 (Estado Atual), 2 (Por Onde Começar) e 3 (Protocolo) são o ponto de entrada para qualquer nova sessão de IA. A seção 4 é o histórico condensado. Detalhes completos de cada experimento vivem em `data/experimentos/exp_*.json` (schema: config + janelas IS/OOS + trades + equity).

---

## 1. Estado Atual (23/08/2026)

- **Motor canônico:** `scripts/backtest_institucional.py` v**2.3.1** — matematicamente íntegro (zero lookahead, funding/notional corretos, 15 testes de regressão verdes). Único motor que gera os artefatos oficiais.
- **Veredito da exploração (42 configurações, 4 famílias de sinal):** NENHUMA estratégia tem edge OOS estatisticamente significativo sob o protocolo rigoroso (walk-forward + bootstrap + Deflated Sharpe). O "edge" da V2.2 era artefato de lookahead intra-diário (usava o fechamento diário do próprio dia) — corrigido em V2.3.
- **Melhor configuração encontrada (g3, hash `45c0eb3c`):** BTC/ETH-only, sem shorts, risco 0,75%, fee VIP 0,02% → OOS +R$4,5k, PF 1.03, Sharpe 1.20, DD 4,7% — perfil excelente, edge NÃO provado (P(PF>1)=60,7%, 46 trades).
- **Recomendação vigente para dinheiro real:** núcleo B&H BTC com DCA + airbag trend EMA200 semanal (documento: `PLANO_OPERACIONAL_REAL.md`). Swing engine = satélite em observação, sem dinheiro real até alguma variante passar em TODOS os filtros.
- **Git:** ~67 arquivos alterados nesta fase ainda **NÃO commitados** — primeiro passo da próxima sessão deve ser revisar `git status` e commitar (o usuário não pede commit automaticamente; sugerir).

---

## 2. Por Onde Começar (próximos passos sugeridos)

1. **Commit do estado atual** (sugestão de mensagem: "V2.3.1: integridade do motor, validação estatística, 42 experimentos e plano operacional").
2. **Continuar a busca de edge** no protocolo (seção 3). Candidatos ainda não testados, em ordem de prioridade:
   - Vol-targeting (risco inverso à volatilidade realizada) e cap de correlação (evitar 4 posições correlacionadas) — refinamentos de gestão de risco que podem transformar g3 em algo significativo.
   - Híbrido trend BTC EMA200 + swing: usar o airbag como filtro macro do swing (só operar swing acima da EMA200).
   - Janelas de momentum mais longas no cross-sectional com hedge (long top-N / short bottom-N) — hedge não testado.
   - Novas features para meta-labeling (features de mercado/cross-section em vez das features de entrada atuais — AUC foi 0.48 com as atuais).
3. **Segundo momento (quando o usuário pedir):** módulo operacional diário (`scripts/operador.py`) — sinais prontos para execução manual + controle de carteira + aportes; e substituição do vesting hardcoded por fonte real (necessário para o ao vivo).
4. **Não fazer:** re-otimizar parâmetros no período completo; operar com dinheiro real sem aprovação do protocolo; apagar o baseline contaminado preservado (`data/experimentos/exp_9ea2dff4_v22_lookahead_baseline.json`).

---

## 3. Protocolo de Trabalho (obrigatório)

- **Motor canônico único:** `scripts/backtest_institucional.py`. Divergência motor × `Prompt.md` = bug (corrigir ou documentar).
- **Ambiente:** `.venv\Scripts\python.exe` (Python 3.11, pandas 3.0.5, numpy 2.4.6, sklearn 1.9.0, pytest 9.1.1).
- **Comandos principais:**
  ```
  .venv\Scripts\python.exe -m pytest tests/test_engine.py            # 15 testes de regressão (sempre antes de confirmar mudanças)
  .venv\Scripts\python.exe scripts\backtest_institucional.py --mode all              # artefatos oficiais (resumo/trades/relatório por modalidade)
  .venv\Scripts\python.exe scripts\backtest_institucional.py --walkforward --no-append --<param> <valor>   # experimento isolado
  .venv\Scripts\python.exe scripts\batch_experiments.py              # bateria (1 carga de dados); editar CONFIGS no arquivo
  .venv\Scripts\python.exe scripts\statistical_validation.py --exp <hash>           # bootstrap + leave-one-out + Deflated Sharpe
  .venv\Scripts\python.exe scripts\meta_label.py --exp <hash>        # screening ML (AUC IS)
  ```
- **Critério de aceite de qualquer mudança:** melhora em ≥3/5 métricas OOS (trading PnL, PF, DD, Sharpe, retorno) vs baseline vigente; PF OOS > 1.0; piora de DD ≤ 20% relativa; **e** bootstrap P(PF>1) ≥ 90% + Deflated Sharpe p < 0.10. Registrar em `analises.md` (seção 4, formato na seção 5) com hash da config.
- **Blindagens:** zero lookahead (dados diários usam apenas o dia completo anterior); walk-forward 4 blocos OOS + holdout; correção de múltiplos testes (DSR); experimentos salvos em `data/experimentos/exp_{hash}.json`; baseline V2.2 contaminado preservado à parte.
- **Limitações conhecidas e aceitas:** vesting hardcoded (~10 moedas), slippage fixo (adequado a R$100k), granularidade de 4h, cash yield 6% a.a. modelado.

---

## 4. Histórico Condensado

### 22/08 — Antes da auditoria de integridade
- V2.1→V2.2 adotada (gatilho LONG confirmado no 1D, short por rompimento de fundo, runner EMA20 1D) com walk-forward "validando" OOS +R$73.098 (PF 1.18). **[INVÁLIDO — contaminado por lookahead]**
- Auditoria de integridade criou o motor canônico com decomposição de PnL, IC 95% Wilson e benchmarks B&H.

### 23/08 — Fase 0 (infraestrutura de validação)
- Suite de testes (15 verdes), bootstrap/DSR (`statistical_validation.py`), walk-forward gravando trades+equity (`windows_detail`), `--no-append`.
- **Bugs encontrados e corrigidos:** (1) lookahead intra-diário no merge diário (V2.2 via o fechamento do próprio dia) — corrigido em V2.3 com shift +1d/+2d; (2) notional do SHORT invertido no funding.
- Bootstrap V2.2: P(PF>1)=93,6% (sugestivo, não-significativo); leave-one-out: sem OOS3 o PnL OOS caía de +R$73.098 para +R$1.685.

### 23/08 — Correção V2.3 (lookahead + notional short)
- Mesma config: OOS cai de +R$73.098 (PF 1.18) para **-R$12.064 (PF 0.99)**; P(PF>1)=38%. Modalidades oficiais re-rodadas (Full +92,7% com cash yield; 5 anos +1,9% com trading líquido -R$19,4k; chop -20,6%).
- Conclusão: edge da V2.2 era majoritariamente lookahead.

### 23/08 — Baterias e1-g4 (17 configs, motor limpo)
- Novos parâmetros: `universe=btceth`, `short_mode=none`, `long_mode=breakout`.
- Melhores: **g3** (`45c0eb3c`: btceth, sem short, risco 0,75%, fee 0,02%) → OOS +R$4.493, PF 1.03, Sharpe 1.20, DD 4,7%; f4 (mesmo sem fee VIP) +R$3.840. Restante entre -R$408 e -R$16.690.
- Padrões: shorts perdem; alts pioram; breakout piora; risco menor + fee VIP ≈ breakeven positivo com DD mínimo.

### 23/08 — Meta-labeling ML (`meta_label.py`)
- Features de entrada (RSI/ATR/ADX/classe/regime) → **AUC IS 5-fold 0.484 ± 0.088** — sem sinal aprendível. Opção encerrada com evidência.

### 23/08 — Famílias alternativas (10 configs)
- Cross-sectional momentum (± filtros ts_mom>0 e BTC EMA200): todas perdem OOS (PF 0.74–0.92, DD 50–80%).
- Time-series trend BTC EMA200/252 semanal (`backtest_trend_bh.py`): +R$64–70k OOS, DD ~25%, porém só 10–11 trades; DSR com 42 configs → p=1.0 (indistinguível de ruído). Valor real: redução de DD.

### 23/08 — Rodada 1.5 (auditoria externa + V2.3.1)
- Hipótese 1 (funding antes do stop = overcharge): **PREMISSA ERRADA** — velas Binance usam open_time = início; o settlement das 08:00 ocorre na abertura da vela 08:00; stop às 05:00 é detectado na vela 04:00 e nunca paga o funding das 08:00. Ordem do motor estava correta.
- Hipótese 2 (path dependency): **ERRADA** — dicts ordenados por inserção (determinístico) e soma de PnL comutativa.
- Único refinamento real (V2.3.1): notional do funding usa a abertura da vela (instante do settlement). Delta OOS ≈ 0,08% (cosmético). Modalidades oficiais re-rodadas.
- Entregue: `PLANO_OPERACIONAL_REAL.md` (núcleo B&H BTC + airbag EMA200 para dinheiro real).

---

## 5. Formato para Novas Entradas

```
## [Data] - Estratégia: [Nome/Resumo]
- **Mudança Implementada:** [o quê + por quê]
- **Resultados Obtidos:** [WF OOS: PnL/PF/Sharpe/DD + bootstrap P(PF>1) + DSR p + hash da config]
- **Análise Diagnóstica:** [por que funcionou/falhou; próximo passo]
```
