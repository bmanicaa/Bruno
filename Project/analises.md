# Registro de Análises — Índice e Estado do Projeto

> **LEIA PRIMEIRO:** as seções 1 (Estado Atual), 2 (Por Onde Começar) e 3 (Protocolo) são o ponto de entrada para qualquer nova sessão de IA. A seção 4 é o histórico condensado. Detalhes completos de cada experimento vivem em `data/experimentos/exp_*.json` (schema: config + janelas IS/OOS + trades + equity).

---

## 1. Estado Atual (24/08/2026)

- **Motor canônico:** `scripts/backtest_institucional.py` v**2.3.1** — matematicamente íntegro (zero lookahead, funding/notional corretos, **22 testes de regressão verdes**). Único motor que gera os artefatos oficiais.
- **Veredito da exploração (32 configurações limpas e distintas, 4 famílias de sinal):** NENHUMA estratégia tem edge OOS estatisticamente significativo. O "edge" da V2.2 era artefato de lookahead intra-diário — corrigido em V2.3.
- **g3 (`45c0eb3c`) foi REPROVADA e não é mais candidata.** Com a régua corrigida na Fase A ela aparece pelo que é:
  - **Sharpe de trading = -0,47** (o "Sharpe 1,20" incluía o cash yield). P(Sharpe>0) = 23,8%.
  - **Expectância média = -0,049R** e **PF mediano = 0,64** (a média 1,03 era carregada por um único bloco).
  - **Perde em 3 dos 4 blocos OOS**; todo o +R$4,5k vem do OOS2 (alta do ETF). Sem o OOS2: -R$6,7k, PF 0,43.
  - **82% do retorno era o rendimento do caixa** (R$20,3k de cash yield vs R$4,5k de trading).
  - **DSR p = 0,229** (REPROVA) — antes marcava p=1e-12 por um erro de escala, ver seção 4.
- **Nenhuma das 32 configs limpas a substitui.** Reprocessadas com a régua corrigida: 6 têm Sharpe de trading > 0, **zero** passam nos critérios endurecidos (seção 3). Nenhuma tem ≥3/4 blocos OOS positivos. Tabela completa na seção 4.
- **Recomendação vigente para dinheiro real:** INALTERADA — núcleo B&H BTC com DCA + airbag trend EMA200 semanal (`PLANO_OPERACIONAL_REAL.md`). A Fase A reforça a recomendação: o candidato de swing que parecia mais próximo de servir era ruído.
- **Git:** estado da fase anterior commitado em `90aaf4c`. As mudanças da Fase A ainda **não commitadas** — sugerir commit ao usuário (ele não pede automaticamente).

---

## 2. Por Onde Começar (próximos passos sugeridos)

**Fase A (medição) — CONCLUÍDA em 24/08.** Detalhes na seção 4. Não refazer.

**Fase B — retomar a busca de edge** no protocolo corrigido (seção 3). Candidatos ainda não testados, em ordem de prioridade:

1. **Híbrido trend + swing** (subiu para 1º): usar o airbag EMA200 como filtro macro do swing. É o único candidato cuja lógica ataca o padrão observado — a família swing só ganha em bull confirmado (OOS2) e sangra no resto.
2. **Vol-targeting** (risco inverso à volatilidade realizada) e **cap de correlação** (evitar 4 posições correlacionadas). *Atenção:* estes mudam o **tamanho** da aposta, não o **sinal**. Como a expectância por trade da g3 é negativa (-0,049R), dimensionar melhor uma aposta ruim não cria edge — reduz variância. Testar, mas sem esperar que resolvam.
3. **Momentum cross-sectional com hedge** (long top-N / short bottom-N) — hedge nunca testado; é a única variante que muda a natureza da exposição.
4. **Novas features para meta-labeling** (features de mercado/cross-section em vez das de entrada — AUC foi 0.48 com as atuais).

**Segundo momento (quando o usuário pedir):** módulo operacional diário (`scripts/operador.py`) — sinais para execução manual + controle de carteira + aportes; e substituição do vesting hardcoded por fonte real (necessário para o ao vivo).

**Não fazer:** re-otimizar parâmetros no período completo; operar com dinheiro real sem aprovação do protocolo; apagar experimentos marcados com `invalid_lookahead` (são evidência histórica); **julgar qualquer config pelo `sharpe_mean` — use sempre `sharpe_trading_mean`**.

---

## 3. Protocolo de Trabalho (obrigatório)

- **Motor canônico único:** `scripts/backtest_institucional.py`. Divergência motor × `Prompt.md` = bug (corrigir ou documentar).
- **Ambiente:** `.venv\Scripts\python.exe` (Python 3.11, pandas 3.0.5, numpy 2.4.6, sklearn 1.9.0, pytest 9.1.1).
- **Comandos principais:**
  ```
  .venv\Scripts\python.exe -m pytest tests/test_engine.py            # 22 testes de regressão (sempre antes de confirmar mudanças)
  .venv\Scripts\python.exe scripts\backtest_institucional.py --mode all              # artefatos oficiais (resumo/trades/relatório por modalidade)
  .venv\Scripts\python.exe scripts\backtest_institucional.py --walkforward --no-append --<param> <valor>   # experimento isolado
  .venv\Scripts\python.exe scripts\batch_experiments.py              # bateria (1 carga de dados); editar CONFIGS no arquivo
  .venv\Scripts\python.exe scripts\statistical_validation.py --exp <hash>           # bootstrap + leave-one-out + Deflated Sharpe
  .venv\Scripts\python.exe scripts\meta_label.py --exp <hash>        # screening ML (AUC IS)
  .venv\Scripts\python.exe scripts\reprocess_experiments.py          # re-roda configs limpas (usar após mudar métricas do motor)
  ```
- **Critério de aceite de qualquer mudança** (endurecido na Fase A — os 3 primeiros itens são novos):
  1. **`sharpe_trading_mean` > 0.** O `sharpe_mean` inclui o cash yield e não mede edge — uma carteira 100% parada no caixa marca Sharpe > 100 nessa métrica.
  2. **Trading PnL OOS positivo em ≥3 dos 4 blocos.** Agregado positivo não basta: a g3 somava +R$4,5k perdendo em 3 de 4 blocos, com tudo concentrado na alta do ETF. Um edge que só existe num regime não é edge.
  3. **≥30 trades OOS.** Abaixo disso o bootstrap satura e devolve p-valores falsamente confiantes (a família trend marcava P(PF>1)=100% com 10 trades). O `statistical_validation.py` agora sinaliza `insufficient_sample`.
  4. Melhora em ≥3/5 métricas OOS (trading PnL, PF, **sharpe_trading**, DD, retorno) vs baseline vigente; PF OOS > 1.0; piora de DD ≤ 20% relativa.
  5. Bootstrap P(PF>1) ≥ 90% **e** Deflated Sharpe p < 0.10.
  6. Registrar em `analises.md` (seção 4, formato na seção 5) com hash da config.
- **Blindagens:** zero lookahead (dados diários usam apenas o dia completo anterior); walk-forward 4 blocos OOS + holdout (confirmado intocado); correção de múltiplos testes (DSR, na escala correta e só sobre configs limpas e distintas); experimentos em `data/experimentos/exp_{hash}.json`; configs pré-V2.3 marcadas com `invalid_lookahead` e excluídas do universo do DSR.
- **Limitações conhecidas e aceitas:** vesting hardcoded (~10 moedas), slippage fixo (adequado a R$100k), granularidade de 4h, cash yield 6% a.a. modelado.

---

## 4. Histórico Condensado

### 24/08 — Fase A: auditoria da própria régua estatística

Motivação: antes de gastar mais orçamento de múltiplos testes em novas configs, auditar os instrumentos que decidem o que é aprovado. Quatro defeitos encontrados — todos no sentido perigoso (aprovar demais), não no seguro.

**A1. Deflated Sharpe com erro de escala (o mais grave).** A fórmula do DSR exige Sharpe e nº de observações na mesma escala temporal. O código passava `sr_obs` **anualizado** (motor multiplica por √2190) junto com `n_obs` = 7.498 **barras de 4h**, multiplicando o Z por √2190 ≈ 46,8.
- Efeito medido na g3: **p = 1,1e-12 (PASSAVA)** vs bootstrap dizendo apenas 60,7% de P(PF>1) na mesma config. Os dois testes discordavam por 10 ordens de grandeza.
- Corrigido desanualizando `sr_obs` e `sr_trials` para a escala por barra. **g3 passou a marcar p = 0,229 (REPROVA)** — agora coerente com o bootstrap.
- Este era o portão entre o laboratório e o dinheiro real. Travado por 2 testes de regressão (`test_dsr_nao_confunde_escala_anual_com_barras`, `test_dsr_ainda_detecta_edge_real` — o segundo garante que a correção não cegou o teste).

**A2. Sharpe media a poupança, não o edge.** `sharpe_ratio` era calculado sobre a curva de patrimônio total, que inclui o cash yield de 6% a.a. Numa estratégia que fica a maior parte do tempo fora do mercado, esse componente quase sem risco domina o numerador.
- Efeito medido na g3: **Sharpe 1,20 → Sharpe de trading -0,47.** Decomposição do retorno OOS: R$20.317 de cash yield vs R$4.493 de trading — **82% do resultado era o rendimento do caixa.**
- Adicionados `sharpe_trading`/`sortino_trading` (excesso sobre o cash yield) no motor e nas 2 famílias alternativas, propagados para janelas, agregados, console e relatórios. `pooled_returns` e `bootstrap_sharpe` passaram a usar retornos em excesso.

**A3. Bootstrap saturado em amostras pequenas.** `block_len=8` com 10 trades faz cada reamostra repetir quase a série original (blocos > n/3), colapsando a variância. Era a origem do "P(PF>1)=100%" da família trend com 10 trades. Agora o bloco é limitado a n/3 e amostras < 30 trades vêm marcadas com `insufficient_sample`.

**A4. Higiene do universo de tentativas.** 9 experimentos pré-V2.3 (contaminados por lookahead) estavam soltos na pasta sem marcação — ordenando os 42 por PnL, o 1º lugar era `b415fc06` (+R$80.308), justamente uma config contaminada, que qualquer sessão futura escolheria como "melhor". Todos os 10 pré-V2.3 receberam `invalid_lookahead: true` + motivo, e `collect_all_experiments()` passou a excluí-los e a deduplicar por `config_hash` (o DSR contava a mesma config duas vezes; e `n_trials` variava entre execuções — 28 numa, 42 noutra — tornando o teste não reprodutível).

**A5. Bug silencioso no trend (menor).** `backtest_trend_bh.py` procurava `{ATIVO}_1d.csv` só em `raw/macro/`, onde só existe BTC; o ETH (em `raw/coins/ETHUSDT/`) era descartado com um `continue` mudo. Por isso as configs "BTC+ETH" tinham resultado **idêntico** às BTC-only — eram duplicatas. Agora busca nos dois diretórios e levanta `FileNotFoundError` em vez de fingir que rodou o pedido.

**Consequências para a contagem oficial:** os "42 experimentos" eram 42 *arquivos* = 32 configs limpas + 10 contaminadas. Antes da correção A5 duas das configs trend eram duplicatas silenciosas (o ETH nunca entrava), o que dava 30 distintas; com o bug resolvido as 32 passaram a ser genuinamente distintas. Usar a contagem correta é o que faz o DSR ser reprodutível.

**Entregues:** `scripts/reprocess_experiments.py` (re-roda as configs limpas com uma carga de dados, para quando as métricas do motor mudam) + 7 testes novos (22 no total, todos verdes).

#### Re-leitura das 32 configs limpas com a régua corrigida (24 min de reprocessamento)

Ranking pelo **Sharpe de trading** (a coluna que importa). Note o abismo entre as duas colunas de Sharpe — é o cash yield que estava sendo contado como habilidade:

| hash | família | **Sharpe TRADING** | Sharpe c/ caixa | PnL OOS | trades | ExpR | blocos+ |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :---: |
| db8f33f6 | cs_mom | **+0,29** | 0,36 | +75.740 | 1251 | +0,003 | 1/4 |
| fa47559c | trend | +0,19 | 0,51 | +64.249 | 11 | +0,115 | 2/4 |
| a0e57f10 | trend | +0,18 | 0,50 | +69.558 | 10 | +0,155 | 2/4 |
| 12616cbc | trend | +0,14 | 0,38 | +116.175 | 20 | +0,085 | 2/4 |
| 4fd4b30b | cs_mom | +0,07 | 0,15 | -25.128 | 1243 | -0,004 | 1/4 |
| a1d02e0c | swing | +0,03 | 0,23 | -11.956 | 326 | +0,137 | 2/4 |
| … | | | | | | | |
| **45c0eb3c (g3)** | swing | **-0,47** | **1,20** | +4.493 | 46 | -0,049 | **1/4** |
| 3dcce1dc | swing | -0,52 | 1,15 | +3.840 | 46 | -0,069 | 1/4 |
| 2c05c70c | swing | -1,02 | -0,12 | -8.995 | 47 | -0,253 | 1/4 |

- **32 configs limpas | 6 com Sharpe de trading > 0 | 0 passam nos critérios endurecidos** (Sharpe trading > 0 **e** ≥3/4 blocos positivos **e** ≥30 trades).
- **Nenhuma config tem ≥3/4 blocos OOS positivos** — a melhor marca é 3/4 (`ad61cd70`), e essa tem Sharpe de trading -0,12. O padrão é universal: quase tudo lucra só no OOS2 (alta do ETF 2023-09→2024-09) e sangra nos outros três.
- **DSR na base de trading, 32 tentativas** (piso de ruído SR0 = 0,63): db8f33f6 p=0,736 | 12616cbc p=0,816 | g3 p=0,980. Todos REPROVAM.
- **A blindagem de amostra pequena provou seu valor na prática:** `12616cbc` marca **P(PF>1) = 97,4%**, o que passaria no filtro de ≥90% — mas dispara `insufficient_sample` (20 trades) e o DSR o reprova com p=0,82. Sem a blindagem da Fase A, esta config seria anunciada como "achamos algo".
- **Efeito colateral da correção A5 (ETH):** com o ETH realmente entrando, a família trend melhorou no PnL bruto (`12616cbc`: +R$64k → +R$116k; `fd9a996d`: +R$70k → +R$94k) e ganhou trades (11→20, 10→19). Continua reprovando por amostra e por Sharpe de trading, mas agora os números são reais. As 4 configs trend deixaram de ser 2 duplicatas.

#### Efeito nas modalidades oficiais (re-rodadas com a métrica nova)

A separação trading × caixa inverte a leitura de 3 das 6 modalidades:

| Modalidade | Retorno | PnL de trading | Cash yield | Sharpe de trading |
| :--- | ---: | ---: | ---: | ---: |
| Full (7 anos) | +92,8% | +R$36.776 | +R$56.025 | +0,26 |
| 5 anos | +1,9% | **-R$19.405** | +R$21.294 | **-0,14** |
| Preliminar | +7,8% | +R$2.755 | +R$5.029 | +0,19 |
| Bull (6m) | +39,6% | **+R$37.493** | +R$2.112 | **+1,99** |
| Bear (2022) | +4,1% | **-R$1.399** | +R$5.541 | **-0,12** |
| Chop (6m) | -20,6% | -R$22.713 | +R$2.142 | -3,70 |

- **"Bear 2022 +4,1% contra -64,6% do B&H" não é defesa por habilidade.** O trading perdeu R$1.399; os +4,1% são o cash yield. A proteção existe e é real, mas vem do filtro de regime **manter o capital fora do mercado** — não de operar bem no bear. Descrever isso como "lucro em SHORT no colapso Luna/FTX" (como faz o menu do `Prompt.md`, opção 2) está errado.
- **Bull é o único resultado genuíno** do conjunto: +R$37,5k de trading contra R$2,1k de caixa, Sharpe de trading +1,99.
- **Nos 7 anos, 60% do retorno é caixa.** Nos 5 anos, o trading queimou R$19,4k e o caixa cobriu.
- **Síntese:** o sistema só ganha dinheiro em bull confirmado; em todo o resto o "lucro" é juro de dinheiro parado. Isso é coerente com o achado dos blocos OOS (só o OOS2 lucra) e é a razão de o candidato nº1 da Fase B ser o híbrido trend+swing.

**Veredito da fase:** a g3 deixa de ser candidata, e nenhuma das 32 a substitui. Não foi uma estratégia que piorou — foi uma medição que ficou honesta. A recomendação de dinheiro real (`PLANO_OPERACIONAL_REAL.md`) não muda, e sai reforçada.


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
- Melhores: **g3** (`45c0eb3c`: btceth, sem short, risco 0,75%, fee 0,02%) → OOS +R$4.493, PF 1.03, Sharpe 1.20, DD 4,7%; f4 (mesmo sem fee VIP) +R$3.840. Restante entre -R$408 e -R$16.690. **[Leitura revista em 24/08 — ver Fase A: o Sharpe 1.20 era o cash yield; o Sharpe de trading é -0,47 e a config foi reprovada.]**
- Padrões: shorts perdem; alts pioram; breakout piora; risco menor + fee VIP ≈ breakeven positivo com DD mínimo.

### 23/08 — Meta-labeling ML (`meta_label.py`)
- Features de entrada (RSI/ATR/ADX/classe/regime) → **AUC IS 5-fold 0.484 ± 0.088** — sem sinal aprendível. Opção encerrada com evidência.

### 23/08 — Famílias alternativas (10 configs)
- Cross-sectional momentum (± filtros ts_mom>0 e BTC EMA200): todas perdem OOS (PF 0.74–0.92, DD 50–80%).
- Time-series trend BTC EMA200/252 semanal (`backtest_trend_bh.py`): +R$64–70k OOS, DD ~25%, porém só 10–11 trades; DSR → p=1.0 (indistinguível de ruído). Valor real: redução de DD. **[Revisto em 24/08: o "P(PF>1)=100%" desta família era artefato de bootstrap saturado com 10 trades; e as configs "BTC+ETH" eram duplicatas das BTC-only por um bug de leitura. Ver Fase A.]**

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
