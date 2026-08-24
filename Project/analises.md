# Registro de Análises — Índice e Estado do Projeto

> **LEIA PRIMEIRO:** as seções 1 (Estado Atual), 2 (Por Onde Começar) e 3 (Protocolo) são o ponto de entrada para qualquer nova sessão de IA. A seção 4 é o histórico condensado. Detalhes completos de cada experimento vivem em `data/experimentos/exp_*.json` (schema: config + janelas IS/OOS + trades + equity).

---

## 1. Estado Atual (24/08/2026)

- **Motor canônico:** `scripts/backtest_institucional.py` v**2.3.1** — matematicamente íntegro (zero lookahead, funding/notional corretos, **37 testes de regressão verdes**). Único motor que gera os artefatos oficiais. **Walk-forward completo agora em ~23s** (era 197,6s) — ver I2 na seção 4.
- **Veredito da exploração (36 configurações limpas e distintas, 4 famílias de sinal):** NENHUMA estratégia tem edge OOS estatisticamente significativo. O "edge" da V2.2 era artefato de lookahead intra-diário — corrigido em V2.3.
- **g3 (`45c0eb3c`) foi REPROVADA e não é mais candidata.** Com a régua corrigida na Fase A ela aparece pelo que é:
  - **Sharpe de trading = -0,47** (o "Sharpe 1,20" incluía o cash yield). P(Sharpe>0) = 23,8%.
  - **Expectância média = -0,049R** e **PF mediano = 0,64** (a média 1,03 era carregada por um único bloco).
  - **Perde em 3 dos 4 blocos OOS**; todo o +R$4,5k vem do OOS2 (alta do ETF). Sem o OOS2: -R$6,7k, PF 0,43.
  - **82% do retorno era o rendimento do caixa** (R$20,3k de cash yield vs R$4,5k de trading).
  - **DSR p = 0,229** (REPROVA) — antes marcava p=1e-12 por um erro de escala, ver seção 4.
- **Nenhuma das 36 configs limpas a substitui.** Com a régua corrigida: 7 têm Sharpe de trading > 0 e **zero** passam nos critérios endurecidos (seção 3). Tabela completa na seção 4.
- **Fase B item 1 (híbrido trend + swing) CONCLUÍDA e REPROVADA.** O filtro "só operar acima da EMA200 diária" **já existia** no motor — o regime bull exige `close_1d >= EMA50 E >= EMA200` (provado com trades idênticos em dados reais). A variante mais estrita (`ac35a444` — EMA50 semanal + confirmação de 7 dias) é a **primeira das 36 a passar nos 4 primeiros critérios**, mas reprova no bootstrap (P(PF>1)=58,8%) e no DSR (p=0,84); a autópsia mostra que o ganho veio de **realocação de vagas da carteira**, não do filtro. Seção 4, Fase B.
- **Recomendação vigente para dinheiro real:** INALTERADA — núcleo B&H BTC com DCA + airbag trend EMA200 (`PLANO_OPERACIONAL_REAL.md`). Fases A e B reforçam: o candidato de swing que parecia mais próximo de servir era ruído, e o filtro macro que deveria salvá-lo já estava ligado.
- **Porta macro (nova):** `build_macro_gate()` + `--macro-filter` / `--macro-confirm-days`, `off` por padrão. Desligada, o motor roda **bit a bit** como antes — invariância provada re-executando `ad61cd70`.
- **Git:** Fase A commitada em `171c7d5`, `70c1eda`, `2381146`. As mudanças da Fase B ainda **não commitadas** — sugerir commit ao usuário (ele não pede automaticamente).

---

## 2. Por Onde Começar (próximos passos sugeridos)

**Fase A (medição) — CONCLUÍDA em 24/08.** Detalhes na seção 4. Não refazer.

**Fase B item 1 (híbrido trend + swing) — CONCLUÍDA em 24/08 e REPROVADA. Não refazer.** O filtro "só operar acima da EMA200 diária" já estava no motor (o regime bull exige `close_1d >= EMA50 E >= EMA200`), e a variante mais estrita que sobrou reprova no bootstrap e no DSR. Detalhes na seção 4.

> **Ler antes de propor qualquer filtro novo (achado B5):** numa carteira de 4 vagas fixas, bloquear uma entrada libera a vaga para outra moeda mais tarde. O efeito medido de um filtro mistura o mérito dele com o sorteio de quem ocupou a vaga — na Fase B a segunda parte foi ~1,6× maior que a primeira e tinha sinal contrário. Toda mudança que altere quais posições entram exige a decomposição do critério 6 da seção 3.

**Fase B — candidatos ainda não testados**, em ordem de prioridade:

1. **Momentum cross-sectional com hedge** (long top-N / short bottom-N) — hedge nunca testado; é a única variante que muda a natureza da exposição, e **não sofre do problema B5** (não tem vagas fixas). É o candidato metodologicamente mais limpo que sobrou.
2. ~~**Medir qualidade de tendência, não posição**~~ — **DESCARTADO em 24/08: já foi testado.** A premissa ("nunca se mediu qualidade, só posição") é falsa. O parâmetro `btc_adx_min` existe no motor desde a bateria e1 e **ADX é exatamente um medidor de persistência/qualidade de tendência**, não de posição. Testado em 4 configs (3 limpas), todas reprovam:

   | hash | universo | ADX min | Sharpe trading | Trading PnL | trades |
   | :--- | :--- | ---: | ---: | ---: | ---: |
   | `a089303c` | btceth | 20 | −0,20 | −3.974 | 70 |
   | `46f23cb9` | btceth | 25 | −0,31 | −10.883 | 63 |
   | `e3572fb7` | alpha | 25 | −0,59 | −16.669 | 176 |

   Efficiency ratio é primo próximo do ADX (ambos medem deslocamento direcional contra ruído). **Este é o mesmo erro do achado B0**: uma ideia registrada como "nunca testada" que já estava no motor sob outro nome. Não refazer sem justificar o que a nova forma funcional mede que o ADX não mede.
3. **Vol-targeting** (risco inverso à volatilidade realizada) e **cap de correlação** (evitar 4 posições correlacionadas). *Atenção:* estes mudam o **tamanho** da aposta, não o **sinal**. Como a expectância por trade da g3 é negativa (-0,049R), dimensionar melhor uma aposta ruim não cria edge — reduz variância. Testar, mas sem esperar que resolvam. Sujeitos a B5.
4. **Novas features para meta-labeling** (features de mercado/cross-section em vez das de entrada — AUC foi 0.48 com as atuais).

**Pendências abertas de infraestrutura** (independentes da busca de edge — levantadas na revisão de 24/08):

| # | Pendência | Por que importa | Estado |
| :--- | :--- | :--- | :--- |
| I1 | **Teste de holdout não existe.** `HOLDOUT = ('2026-02-01','2026-08-20')` é só uma constante no motor; nenhum código o executa. | É o último portão antes do dinheiro real. Hoje ele está "intocado" por omissão, não por desenho — se uma config passar nos 6 critérios, o teste final ainda precisa ser escrito. | Não iniciado |
| I2 | ~~Motor gasta 88% do tempo em `df.iloc[]`~~ — **RESOLVIDO em 24/08.** | Walk-forward de **197,6s → 23,0s (8,6×)**, saída idêntica trade a trade em 7 configs. Ver seção 4. | **Concluído** |
| I3 | **Vesting hardcoded** (~10 moedas na função `is_vesting_cliff`) **e com bug de colisão de substring.** `'OP' in s` casa com 7 moedas do repositório — `OPUSDT` (a pretendida) mais `OPENUSDT`, `OPGUSDT`, `OPNUSDT`, `PEOPLEUSDT`, `POPCATUSDT`, `SOPHUSDT` — e todas perdem os longs do dia 24 ao fim de cada mês, em todo config de universo `alpha`. O guard `'PEPE' not in s` na mesma linha é código morto ('PEPE' não contém 'OP'). | Não é só "limitação aceita": é veto ativo e indevido sobre 6 moedas. Correção barata: casamento exato de símbolo + transformar o veto em parâmetro (`vesting_veto`) para **medir o tamanho do efeito** numa rodada. Só se for material vale procurar fonte real de unlocks. | Bug identificado, não corrigido |
| I4 | **`scripts/operador.py` não existe** — módulo operacional diário (sinais para execução manual + controle de carteira + aportes). | Só quando o usuário pedir. | Não iniciado |

**Armadilhas conhecidas (ler antes de mexer no motor):**

- `--macro-confirm-days` nos modos **semanais** equivale a **uma semana extra de atraso**, não a confirmação diária — a porta semanal só muda de valor na virada da semana. A leitura literal só vale para `ema200d`.
- `ema200w` está implementado mas **não deve ser testado** sem tratar o aquecimento (~200 semanas contra dados que começam em 09/2019). O motor avisa em `stderr`.
- Chaves opcionais de params (`long_mode`, `macro_filter`, `macro_confirm_days`) só entram no dict quando saem do padrão. **Não "normalizar" isso** — acrescentar uma chave a todas as configs mudaria os 36 `config_hash` já registrados. Travado por `test_hash_da_baseline_nao_muda_com_as_chaves_novas`.
- A porta semanal usa `shift(1)` sobre semanas e supõe série sem buracos. Verificado em 24/08: BTC diário tem 364 semanas consecutivas, zero buracos. Se a base mudar, revalidar.

**Não fazer:** re-otimizar parâmetros no período completo; operar com dinheiro real sem aprovação do protocolo; apagar experimentos marcados com `invalid_lookahead` (são evidência histórica); **julgar qualquer config pelo `sharpe_mean` — use sempre `sharpe_trading_mean`**; reimplementar o filtro "acima da EMA200 diária" — já existe dentro do regime bull (ver B0, travado por teste); **propor "medir qualidade de tendência" como ideia nova — o `btc_adx_min` já faz isso e reprovou em 3 configs limpas** (ver seção 2, item 2).

---

## 3. Protocolo de Trabalho (obrigatório)

- **Motor canônico único:** `scripts/backtest_institucional.py`. Divergência motor × `Prompt.md` = bug (corrigir ou documentar).
- **Ambiente:** `.venv\Scripts\python.exe` (Python 3.11, pandas 3.0.5, numpy 2.4.6, sklearn 1.9.0, pytest 9.1.1).
- **Comandos principais:**
  ```
  .venv\Scripts\python.exe -m pytest tests/test_engine.py            # 37 testes de regressão (sempre antes de confirmar mudanças)
  .venv\Scripts\python.exe scripts\backtest_institucional.py --mode all              # artefatos oficiais (resumo/trades/relatório por modalidade)
  .venv\Scripts\python.exe scripts\backtest_institucional.py --walkforward --no-append --<param> <valor>   # experimento isolado
  .venv\Scripts\python.exe scripts\backtest_institucional.py --walkforward --no-append --macro-filter ema50w --macro-confirm-days 7   # porta macro (Fase B)
  .venv\Scripts\python.exe scripts\batch_experiments.py              # bateria (1 carga de dados); editar CONFIGS no arquivo
  .venv\Scripts\python.exe scripts\statistical_validation.py --exp <hash>           # bootstrap + leave-one-out + Deflated Sharpe
  .venv\Scripts\python.exe scripts\meta_label.py --exp <hash>        # screening ML (AUC IS)
  .venv\Scripts\python.exe scripts\reprocess_experiments.py          # re-roda configs limpas (usar após mudar métricas do motor)
  .venv\Scripts\python.exe scripts\verify_replay.py <ref.json> --hash <hash>   # prova que uma mudança é NULA (igualdade trade a trade)
  ```
- **Toda mudança que se propõe nula** (refatoração, performance, reorganização) **deve passar pelo `verify_replay.py`** em pelo menos uma config por ramo de código tocado — não só na baseline. O ramo `short_mode=revert` não tem experimento registrado; gere a referência rodando o motor da versão anterior (`git show HEAD:./scripts/backtest_institucional.py`).
- **Critério de aceite de qualquer mudança** (endurecido na Fase A — os 3 primeiros itens são novos):
  1. **`sharpe_trading_mean` > 0.** O `sharpe_mean` inclui o cash yield e não mede edge — uma carteira 100% parada no caixa marca Sharpe > 100 nessa métrica.
  2. **Trading PnL OOS positivo em ≥3 dos 4 blocos.** Agregado positivo não basta: a g3 somava +R$4,5k perdendo em 3 de 4 blocos, com tudo concentrado na alta do ETF. Um edge que só existe num regime não é edge.
  3. **≥30 trades OOS.** Abaixo disso o bootstrap satura e devolve p-valores falsamente confiantes (a família trend marcava P(PF>1)=100% com 10 trades). O `statistical_validation.py` agora sinaliza `insufficient_sample`.
  4. Melhora em ≥3/5 métricas OOS (trading PnL, PF, **sharpe_trading**, DD, retorno) vs baseline vigente; PF OOS > 1.0; piora de DD ≤ 20% relativa.
  5. Bootstrap P(PF>1) ≥ 90% **e** Deflated Sharpe p < 0.10.
  6. **Decomposição de trades antes do bootstrap** (novo na Fase B): se a mudança altera quais posições entram, comparar a lista de trades contra a baseline separando **comuns × removidos × novos**, e reportar o agregado **sem o maior trade**. Numa carteira de vagas fixas, bloquear uma entrada libera a vaga para outra moeda — foi assim que a `ac35a444` "ganhou" R$16k num bloco onde a porta fechou em ~1% dos dias. Ver seção 4, achado B5.
  7. Registrar em `analises.md` (seção 4, formato na seção 5) com hash da config.
- **Blindagens:** zero lookahead (dados diários usam apenas o dia completo anterior); walk-forward 4 blocos OOS + holdout (`HOLDOUT = 2026-02-01 → 2026-08-20`; **atenção: é só uma constante — nenhum código o executa hoje.** Está "intocado" por omissão, não por desenho. Quando/se uma config passar nos 6 critérios, o teste final de holdout ainda precisa ser escrito); correção de múltiplos testes (DSR, na escala correta e só sobre configs limpas e distintas); experimentos em `data/experimentos/exp_{hash}.json`; configs pré-V2.3 marcadas com `invalid_lookahead` e excluídas do universo do DSR.
- **Limitações conhecidas e aceitas:** vesting hardcoded (~10 moedas), slippage fixo (adequado a R$100k), granularidade de 4h, cash yield 6% a.a. modelado.

---

## 4. Histórico Condensado

### 24/08 — I2: vetorização do screener (mudança nula, 8,6× mais rápida)

**Mudança implementada.** Os dois laços de screening (long e short) liam cada vela com `df.iloc[loc_idx - k]`, o que constrói uma Series nova por acesso — 88% do tempo do motor. Agora as colunas quentes viram arrays numpy uma vez por moeda (`_hot_arrays`, 25 colunas) e são indexadas por posição. Corrigido também o segundo gargalo: o laço que monta `btc_macro_map` refazia uma **máscara booleana sobre a série diária inteira a cada vela de 4h**; virou `searchsorted` vetorizado.

**Resultado (config `ad61cd70`, walk-forward completo, 5 janelas):**

| | antes | depois |
| :--- | ---: | ---: |
| tempo | 197,6s | **23,0s** |
| ganho | — | **8,6×** |

A config mais pesada (`9ea2dff4`, universo alpha **com** shorts) roda em **24,2s**. A estimativa de "~10 min por config" registrada em 24/08 era alta: o tempo real medido antes da mudança era 3,3 min.

**Prova de que a mudança é nula.** Criado `scripts/verify_replay.py` — compara dois artefatos de experimento campo a campo com **igualdade numérica estrita** (sem tolerância de ponto flutuante, de propósito), ignorando só `generated_at`. Protocolo executado:

1. Referência do git re-executada **antes** de qualquer edição → idêntica ao `exp_ad61cd70.json` commitado. Isso descarta desvio de ambiente e torna qualquer diferença posterior atribuível ao refactor.
2. Sete configs re-executadas **depois**, cobrindo todos os ramos tocados — `ad61cd70` (long 1d/pullback), `a1d02e0c` e `2c05c70c` (long 1d/breakout), `4cdae2fe` (long 4h + short breakout), `ac35a444` (porta macro ema50w + confirm), `9ea2dff4` (alpha + shorts), e uma config gerada para o ramo `short_mode=revert`, que **nenhum experimento existente cobria** — a referência dela foi produzida rodando o motor original extraído do git.
3. Todas: **idênticas trade a trade**. Varredura final confirmou os **46 experimentos preexistentes intactos**.

**Travado por 4 testes novos** (`TestI2Vetorizacao`, 37 no total): arrays batem com `df.iloc[i][col]` valor a valor; coluna ausente vira array de NaN (reproduzindo o `Series.get(col, np.nan)` dos campos opcionais do merge diário); `nanmin`/`nanmax` reproduzem o `skipna` do pandas na janela de 10 velas do stop; `searchsorted` devolve a mesma barra diária que a máscara booleana — um deslocamento de um dia aqui seria lookahead.

**Por que isto importa mais que conveniência.** O instrumento que falta no laboratório é o **teste de sinal nulo** (entrada aleatória, centenas de rodadas, para medir a distribuição de resultados com edge zero *neste* motor de 4 vagas). A 3,3 min por rodada, 300 rodadas eram 16 horas; a 23s são ~2 horas. O ganho de performance é pré-requisito do teste, não comodidade.

**Nota de método:** uma config selecionada para verificação (`d70b0b95`) era da família cross-sectional (`top_n/mom_days/reb_days`), não do motor de swing. Rodá-la no motor errado sobrescreveu o artefato; restaurado do backup e verificado idêntico. Registrado aqui porque **14 dos 36 experimentos limpos são de famílias alternativas** e não aceitam os params do motor canônico — qualquer script que itere sobre `exp_*.json` precisa filtrar por `'risk_pct' in config`.

### 24/08 — Fase B item 1: híbrido trend + swing (filtro macro EMA200)

Hipótese da seção 2: *"o sistema só ganha em alta confirmada — a solução é simplesmente não operar fora da alta"*, implementada como o airbag EMA200 filtrando o swing. Quatro configs pré-registradas antes de rodar. **Nenhuma passa.** Uma delas passa nos 4 primeiros critérios e é reprovada pelo 5º — e a autópsia dela é o achado mais útil da fase.

**B0. O filtro literal já estava no motor (é redundante).** O regime `bull`, único que libera compras, já exige `close_1d >= EMA50_1d` **E** `close_1d >= EMA200_1d`. "Só operar acima da EMA200 diária" não remove um único long — remove apenas os shorts, que por definição só existem abaixo da EMA200. Ou seja: é exatamente o `short_mode=none` já testado.

- **Controle em dados reais** (`macro_filter=ema200d` com shorts ligados × `short_mode=none` sem filtro): trades **idênticos, um a um, nas 5 janelas** (IS 66, OOS1 55, OOS2 86, OOS3 90, OOS4 12). Não gerou arquivo de experimento — não é tentativa, é verificação.
- Travado pelo teste `test_ema200d_e_redundante_para_longs`, para que nenhuma sessão futura reimplemente isto achando que é ideia nova.

**B1. Por que o airbag não separa o rali do chop.** % de dias com o filtro ligado:

| período | `bull` (motor) | acima da EMA200d | `bull` + semanal EMA50 |
| :--- | ---: | ---: | ---: |
| BULL 6m (out/23→mar/24) — Sharpe trading +1,99 | 92,9% | 97,8% | 92,9% |
| CHOP 6m (abr→set/24) — Sharpe trading −3,70 | **46,4%** | 78,1% | **46,4%** |
| OOS1 (2022-09→2023-09) | 40,4% | 57,1% | **26,0%** |

O chop **já era 46% filtrado** pelo regime bull e o BTC passou 78% dos dias acima da EMA200. A diferença entre o rali e o chop não é a posição em relação à média — é a **qualidade da tendência**. Um filtro de posição não enxerga isso. O único lugar onde um filtro mais lento morde de verdade é o OOS1 (40,4% → 26,0%).

**B2. O que foi construído.** `build_macro_gate()` no motor canônico — porta macro **opcional** sobre **novas entradas** (posições abertas seguem as saídas normais). Modos: `off` (padrão), `ema200d`, `ema50w`, `ema200w`; mais `--macro-confirm-days N` (condição válida por N fechamentos diários seguidos — equivalente à checagem semanal do `PLANO_OPERACIONAL_REAL.md`).

- **Zero lookahead:** a porta de um dia só é lida a partir do dia seguinte, mesma regra do regime bull/bear. Nos modos semanais só a semana **fechada** anterior decide, e a porta fica **fechada** enquanto a EMA semanal não tiver aquecimento (`span` semanas).
- **Invariância provada:** com a porta desligada, a baseline `ad61cd70` reproduziu `exp_ad61cd70.json` **idêntico trade a trade**. Chaves novas só entram no dict de params quando saem do padrão, então os hashes históricos continuam reproduzíveis pela CLI.
- **`ema200w` foi implementado mas NÃO testado:** a EMA200 semanal exige ~200 semanas de aquecimento e os dados começam em 09/2019, o que deixaria IS e OOS1 "parados por construção" e não por decisão. Testá-la sem tratar isso produziria um falso positivo de aquecimento, não um edge.

**B3. Resultados (4 configs pré-registradas, walk-forward 4 blocos OOS).**

| config | hash | trades | Trading PnL | PF med | Sharpe TRADING | blocos+ | veredito |
| :--- | :--- | ---: | ---: | ---: | ---: | :---: | :--- |
| baseline `ad61cd70` (alpha, sem short) | ad61cd70 | 243 | −13.283 | 1,05 | −0,12 | 3/4 | — |
| h1: ema200d + confirm 7d | 1a83b0e4 | 237 | −12.822 | 1,03 | −0,24 | 2/4 | REPROVA |
| h2: ema50w | 87233457 | 218 | −3.542 | 1,06 | −0,05 | 3/4 | REPROVA |
| **h3: ema50w + confirm 7d** | **ac35a444** | **216** | **+12.909** | **1,12** | **+0,10** | **3/4** | **REPROVA (ver B4)** |
| h4: g3 + ema200d + confirm 7d | e8196b0d | 44 | −655 | 0,52 | −0,72 | 1/4 | REPROVA |

**A `ac35a444` é a primeira config das 36 a passar nos 4 primeiros critérios** (Sharpe de trading > 0, ≥3/4 blocos, ≥30 trades, PF > 1). É também a primeira config de swing com Trading PnL OOS agregado positivo sem depender do cash yield. E ainda assim reprova:

- **Bootstrap: P(PF>1) = 58,8%** (exigido ≥ 90%). IC95 do PnL: [−80.053, +126.046] — atravessa o zero com folga enorme.
- **DSR: p = 0,8435** (exigido < 0,10), com 36 tentativas e piso de ruído SR0 = 0,64 contra SR observado de 0,10.
- **Leave-one-out:** sem o OOS2 o Trading PnL cai para −4.920 e o Sharpe de trading para −0,10. Todo o resultado positivo vem de um bloco.

**B4. Autópsia da `ac35a444`: o ganho não veio do filtro.** Decompondo as janelas que mudaram:

| janela | PnL baseline | PnL candidata | delta | efeito |
| :--- | ---: | ---: | ---: | :--- |
| OOS1 | −23.201 | −13.292 | **+9.909** | **genuíno** — o filtro cortou 55→32 trades no único período em que ele morde |
| OOS2 | +1.546 | +17.829 | **+16.283** | **artefato** — ver abaixo |
| OOS3 | +6.415 | +6.415 | 0 | filtro nunca fechou a porta |
| OOS4 | +1.956 | +1.956 | 0 | filtro nunca fechou a porta |

O OOS2 se decompõe assim:

- 73 trades presentes nas duas versões: **pioraram** (−15.246 → −18.967).
- 13 trades que o filtro **removeu**: somavam **+16.793** — o filtro tirou trades *vencedores*.
- 9 trades **novos**, inexistentes na baseline: **+36.796**, dominados por um único INJUSDT de **+19.988** em 15/10/2023.

Esses 9 trades não apareceram porque o filtro os aprovou — apareceram porque **bloquear uma entrada libera uma das 4 vagas da carteira**, e a vaga foi ocupada por outra moeda mais tarde. Sem esse único trade de INJ o agregado cai de +12.909 para **−7.080**, e a config perde o critério 1. Sem os 3 maiores, −31.345.

**B4b. A mesma coisa separa h2 de h3.** A única diferença entre a `87233457` (reprovada, −3.542) e a `ac35a444` (que passa nos 4 critérios, +12.909) é a confirmação de 7 dias. Decompondo:

| janela | h2 → h3 | comuns | removidos | novos |
| :--- | ---: | ---: | ---: | ---: |
| OOS1 | −14.684 → −13.292 (+1.392) | 32 | 1 | 0 |
| OOS2 | +2.771 → +17.829 (**+15.058**) | 76 | 7 | 6 |
| OOS3 / OOS4 | idênticos | 102 | 0 | 0 |

Trocar 7 trades por 6 numa janela move R$15 mil — de novo no OOS2, de novo pela mesma realocação de vagas. Ou seja: a fronteira entre "reprovada" e "passa nos 4 primeiros critérios" é um punhado de vagas sorteadas, não uma diferença de regra. Evidência independente do B5.

**Nota sobre `confirm_days` nos modos semanais:** como a porta semanal só muda de valor na virada da semana, exigir 7 dias consecutivos equivale, na prática, a **uma semana extra de atraso** — não a uma confirmação diária. Nos modos diários (`ema200d`) a leitura literal vale.

**B5. Achado metodológico (vale para toda a Fase B).** Numa carteira com **número fixo de vagas**, o efeito de qualquer filtro **não é decomponível** em "os trades ruins que ele evitou". Remover uma entrada realoca a carteira inteira dali para frente, e o resultado medido mistura duas coisas de naturezas opostas: o mérito do filtro e o sorteio de quem ocupou a vaga liberada. Aqui a segunda parte foi ~1,6× maior que a primeira e tinha sinal **contrário** à lógica do filtro — em OOS2 a porta fechou em cerca de 1% dos dias e o PnL mexeu R$16 mil.

**Consequência prática:** os itens 2, 3 e 4 da seção 2 (vol-targeting, cap de correlação, momentum com hedge) mexem em entradas ou em tamanho e sofrem do mesmo problema. Daqui em diante, todo candidato que passe nos 4 primeiros critérios precisa de uma **decomposição de trades comuns × removidos × novos** antes de ir para o bootstrap. Sem isso, um filtro sem mérito nenhum passa por sorte de realocação.

**B6. Bug corrigido de passagem.** `--long-mode` era parseado pela CLI e **descartado** — o dict de params do `__main__` não incluía a chave. Os experimentos de breakout só rodaram porque o `batch_experiments.py` monta o dict à mão. Corrigido; a chave só entra no dict quando sai do padrão, para não mudar os hashes históricos.

**Entregues:** `build_macro_gate()` + `--macro-filter` / `--macro-confirm-days` no motor; 11 testes novos (**33 no total, todos verdes**), incluindo dois de blindagem temporal da porta semanal e um que trava a redundância do `ema200d`; `batch_experiments.py` com o lote da Fase B pré-registrado.

**Veredito da fase:** a hipótese nº1 da Fase B está **testada e reprovada**. Não porque o filtro foi mal implementado, mas porque o mecanismo que ela propunha já existia no motor, e a versão mais estrita que sobrou só melhora o bloco em que remove muitos trades — sem edge estatístico. **36 configs limpas, zero aprovadas.** A recomendação de dinheiro real (`PLANO_OPERACIONAL_REAL.md`) não muda.

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
- **Só uma config chega a 3/4 blocos OOS positivos** (`ad61cd70`), e ela reprova no Sharpe de trading (-0,12) — nenhuma outra passa de 2/4. O padrão é universal: quase tudo lucra só no OOS2 (alta do ETF 2023-09→2024-09) e sangra nos outros três. *(Corrigido em revisão: a redação anterior dizia "nenhuma tem ≥3/4", o que contradizia a própria frase seguinte.)*
- **DSR na base de trading, 32 tentativas** (piso de ruído SR0 = 0,63): db8f33f6 p=0,736 | 12616cbc p=0,816 | g3 p=0,980. Todos REPROVAM.
- **O protocolo antigo acertava por sorte, não por desenho.** Reconstituindo os vereditos antigos das duas configs mais perigosas:

  | config | DSR antigo | bootstrap | verdicto antigo |
  | :--- | :--- | :--- | :--- |
  | g3 `45c0eb3c` | p=0,0000 **PASSA** | 60,5% **reprova** | barrada pelo bootstrap |
  | trend `12616cbc` | p=1,0000 **reprova** | 97,4% **passa** | barrada pelo DSR |

  Ou seja: **nenhuma das duas foi aprovada indevidamente** — mas só porque os dois filtros estavam desalinhados em direções opostas e um cobriu o buraco do outro. Um teste que discorda do outro por 10 ordens de grandeza na mesma config (p=1e-12 vs 60%) acerta por acidente, não por medir corretamente. Depois da Fase A os dois concordam (g3: DSR p=0,98 e bootstrap 60,7%; ambos reprovam), e a `12616cbc` passa a ser barrada por **três** motivos independentes — amostra (20 trades), concentração (2/4 blocos) e DSR (p=0,82) — em vez de um acaso.
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
