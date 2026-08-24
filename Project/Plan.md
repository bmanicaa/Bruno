# Plan.md — Laboratório de Acumulação (Projeto B)

> **Versão:** 24/08/2026 · **Status:** **Etapas 1 a 4 EXECUTADAS na Fase E.** Ver seção 8.
> **Leia antes:** `analises.md` seções 1, 2, 3.1 e as entradas "Fase C" e "Fase E" da seção 4.
> **Este arquivo é a única fonte de verdade sobre o que fazer a seguir.** Se ele divergir de qualquer
> outro documento do repositório, ele vence — exceto quanto a fatos medidos, que vivem no `analises.md`.

---

## 0. Para a próxima sessão de IA — leia isto primeiro

Você está entrando num projeto que **mudou de objetivo**. O histórico é longo e a maior parte dele é
sobre uma frente que foi **congelada**. Não releia tudo; leia isto e depois a Fase C.

**O que aconteceu, em cinco linhas:**

1. O projeto nasceu para construir um motor de swing trade que batesse o mercado (**Projeto A**).
2. Após 36 configurações limpas em 4 famílias de sinal, **nenhuma teve edge estatístico**. Duas fases de
   auditoria (A e B) provaram que os resultados positivos anteriores eram bugs e artefatos de medição.
3. Em 24/08 o usuário decidiu **congelar o Projeto A** e redirecionar o esforço para o **Projeto B**: o
   fluxo de acumulação que ele vai de fato executar com dinheiro real (aporte mensal em BTC + airbag).
4. A **Fase C** mediu esse plano pela primeira vez, em sessão, com scripts standalone. Os achados estão
   no `analises.md` seção 4. **Eles não estão no repositório como código.**
5. ~~**Sua primeira tarefa é a Etapa 2 deste plano.**~~ **FEITO na Fase E (24/08).** A Fase C foi
   reimplementada em `scripts/acumulacao/`: 10 dos 13 alvos batem, os demais ficam em ~1%. A
   reprodução encontrou um **erro real de modelagem** (IR cobrado só na liquidação em vez de na
   venda) — exatamente o que a Etapa 2 existia para pegar. Ver seção 8.

6. **A Fase E também descobriu que o motivo do congelamento do Projeto A estava errado.** O protocolo
   não tem poder para aprovar nada abaixo de Sharpe de trading ~1,2. "36 configs, zero aprovadas" era
   o resultado *esperado* de uma régua cega, não evidência de que nada funciona. Isso **não
   descongela** o Projeto A (ver seção 8), mas muda o que se pode afirmar sobre ele.

**O erro mais provável que você vai cometer:** tentar "melhorar" o motor de swing
(`backtest_institucional.py`) enquanto constrói o novo laboratório. Não faça. A seção 2 explica por quê.

---

## 1. Objetivo do Projeto B

Medir, com o mesmo rigor que reprovou o Projeto A, as variantes do plano que o usuário vai executar
com dinheiro real — e corrigir o `PLANO_OPERACIONAL_REAL.md` com base em evidência, não em eliminação.

**O que o Projeto B NÃO é:** não é busca de edge, não prevê preço, não opera alavancado, não tem
posições, stops nem R-múltiplos. É um **simulador de acumulação**: aportes periódicos, uma regra
opcional de proteção, caixa remunerado, imposto, e comparação contra benchmarks (CDB e DCA fixo).

**Pergunta central, em uma frase:** *dado que o usuário vai aportar R$ X todo mês em BTC pelos
próximos 10+ anos, quais regras em volta disso melhoram o resultado e quais só parecem melhorar?*

---

## 2. Decisão sobre a modularização

O usuário propôs separar o engine em módulos para testar as modalidades sem que uma atrapalhe a outra,
e pediu meu julgamento sobre se isso traz mais benefício que problema.

### Veredito: **sim para a separação, não para refatorar o motor de swing.**

Modularizar **por adição** (criar um pacote novo ao lado) é claramente certo. Modularizar **por
extração** (quebrar `backtest_institucional.py` em módulos e fazê-lo importar de uma base comum) é um
risco alto com benefício baixo, e deve ser adiado indefinidamente.

### Por que não refatorar o motor de swing

1. **Ele é o único artefato auditado do repositório.** `run_portfolio_backtest()` tem ~750 linhas
   cobertas por 33 testes de regressão, e — mais importante — sustenta a **reprodutibilidade bit-a-bit**
   de 36 experimentos em `data/experimentos/`. A Fase B provou essa invariância re-executando
   `ad61cd70` e obtendo trades **idênticos um a um**.
2. **A falha seria silenciosa.** Um refactor pode mudar a ordem de operações de ponto flutuante e
   quebrar a reprodução bit-a-bit **sem quebrar nenhum teste**. O `n_trials` do Deflated Sharpe depende
   de o universo de experimentos ser reprodutível (achado A4). Essa é exatamente a classe de bug que a
   Fase A passou uma auditoria inteira caçando.
3. **O ganho seria estético.** O Projeto A está congelado. Refatorar código que ninguém vai executar
   troca risco real por elegância que não será usada.

### Por que a separação por adição é certa

O fluxo de acumulação **não compartilha quase nada** com o motor de swing:

| dimensão | motor de swing | acumulação |
| :--- | :--- | :--- |
| granularidade | candles de 4h | fechamento diário |
| universo | ~550 moedas com screener point-in-time | 1 a 2 ativos fixos |
| posição | até 4 vagas, stop, breakeven, runner, time-stop | 100% ou 0%, sem stop |
| custos | taxa + slippage + funding (perpétuos) | taxa (spot) |
| risco | 1,5% da banca por trade, R-múltiplos | aporte fixo em reais |
| métrica de sucesso | Sharpe de trading, PF, expectância | valor final, maxDD, vs CDB |

`load_all_data()` carrega ~550 moedas em 4h (dezenas de segundos, muita RAM). O laboratório de
acumulação precisa de **duas séries diárias**. Reusá-lo seria mais lento, mais acoplado e mais frágil.

### Custo aceito desta decisão

Haverá **duplicação deliberada** de ~80 linhas: matemática de EMA/SMA e cálculo de drawdown existem nos
dois lados. **Isso é intencional e não deve ser "consertado".** Duplicar 80 linhas triviais é
incomparavelmente mais barato que arriscar invalidar o registro histórico do projeto.

> **Regra travada:** `scripts/backtest_institucional.py`, `scripts/backtest_cs_momentum.py`,
> `scripts/backtest_trend_bh.py`, `scripts/batch_experiments.py`, `scripts/meta_label.py`,
> `scripts/reprocess_experiments.py` e `tests/test_engine.py` **não devem ser modificados** por
> nenhuma etapa deste plano. Se você achar que precisa, pare e pergunte ao usuário.

### Condição única para reabrir a extração (não fazer agora)

Só considerar unificar as bases se, no futuro, o Projeto A for reativado **e** existir um teste que
reproduza bit-a-bit pelo menos 3 hashes conhecidos (`ad61cd70`, `ac35a444`, `45c0eb3c`) antes e depois
da mudança. Sem esse teste, não mexer.

---

## 3. Arquitetura alvo

```
Project/
├── Plan.md                        ← este arquivo
├── analises.md                    ← registro de achados (seção 3.1 = protocolo do Projeto B)
├── PLANO_OPERACIONAL_REAL.md      ← recomendação ao usuário (corrigir na Etapa 4)
├── Prompt.md                      ← manual do Projeto A (congelado; ver Etapa 4)
├── scripts/
│   ├── backtest_institucional.py  ← PROJETO A — CONGELADO, NÃO TOCAR
│   ├── backtest_cs_momentum.py    ← PROJETO A — CONGELADO
│   ├── backtest_trend_bh.py       ← PROJETO A — CONGELADO
│   ├── batch_experiments.py       ← PROJETO A — CONGELADO
│   ├── meta_label.py              ← PROJETO A — CONGELADO
│   ├── reprocess_experiments.py   ← PROJETO A — CONGELADO
│   ├── statistical_validation.py  ← compartilhado (só lê exp_*.json; não alterar assinatura)
│   ├── legado/                    ← arquivado
│   └── acumulacao/                ← PROJETO B — NOVO
│       ├── __init__.py
│       ├── dados.py               ← carga de séries diárias de 1-2 ativos
│       ├── indicadores.py         ← EMA, SMA, com aquecimento explícito
│       ├── politicas.py           ← as regras testáveis (ver 3.2)
│       ├── motor.py               ← loop diário determinístico
│       ├── metricas.py            ← maxDD, CAGR, tempo submerso, vs benchmark
│       ├── imposto.py             ← custo-médio + IR configurável
│       ├── grid.py                ← executor do grid obrigatório (protocolo 3.1)
│       └── cli.py                 ← ponto de entrada
├── tests/
│   ├── test_engine.py             ← PROJETO A — NÃO TOCAR
│   └── test_acumulacao.py         ← PROJETO B — NOVO
├── data/
│   ├── experimentos/              ← PROJETO A — não escrever aqui
│   └── acumulacao/                ← PROJETO B — novo, artefatos com hash de config
└── reports/
    └── relatorio_acumulacao_*.md
```

### 3.1 Contratos do motor de acumulação

- **Determinismo total.** Mesma config → mesmo resultado, sempre. Hash da config no artefato, como no
  Projeto A.
- **Zero lookahead, com a convenção declarada e travada por teste.** A Fase C leu a média e executou no
  **mesmo fechamento diário** (defensável: cripto é contínuo, você observa o fechamento das 00:00 UTC e
  negocia em seguida). Isso **precisa ser um parâmetro explícito** (`--atraso-execucao 0|1`) e **os dois
  valores entram no grid**, porque a diferença medida foi material.
- **Aquecimento explícito.** Nenhuma decisão antes de a média ter `span` observações completas. A Fase C
  começou em 05/04/2020 por isso (dados começam em 08/09/2019).
- **Caixa e imposto sempre modelados**, nunca implícitos.
- **Nada de otimização.** O motor executa políticas declaradas; quem varre parâmetros é o `grid.py`, e
  o relatório é obrigado a mostrar o grid inteiro (protocolo `analises.md` 3.1, critério 1).

### 3.2 Políticas a implementar (nesta ordem)

| política | parâmetros | status na Fase C |
| :--- | :--- | :--- |
| `CDB` | taxa mensal | benchmark |
| `DCAFixo` | valor, dia do mês, taxa | benchmark |
| `Airbag` | média (tipo+span), fatia, dia da checagem, atraso | medida, 42 combos |
| `Inclinacao` | fração de reserva, escada de gatilhos | **reprovada 12/12** — implementar só para o teste de regressão que trava a reprovação |
| `DoisAtivos` | alvo BTC/ETH, rebalanceio por aporte | **reprovada** — idem |

---

## 4. Etapas, em ordem

### Etapa 1 — Esqueleto e congelamento formal

**Objetivo:** criar a estrutura sem mudar nenhum comportamento.

- Criar `scripts/acumulacao/` com os módulos vazios e `tests/test_acumulacao.py`.
- Criar `data/acumulacao/`.
- Adicionar, no topo de cada script do Projeto A, um cabeçalho de 3 linhas marcando
  `PROJETO A — CONGELADO em 24/08/2026. Ver Plan.md seção 2.` (comentário apenas — **zero mudança de
  código executável**).

**Pronto quando:** `pytest tests/test_engine.py` continua com 33 verdes e `git diff` mostra apenas
comentários e arquivos novos.

---

### Etapa 2 — Reproduzir a Fase C dentro do repositório ⭐ **comece por aqui**

**Objetivo:** transformar os números de sessão em artefatos auditáveis. Esta é a etapa mais importante
do plano; nada depende de análise nova antes dela.

Implementar `dados.py`, `indicadores.py`, `metricas.py`, `imposto.py`, `motor.py` e as políticas `CDB`,
`DCAFixo` e `Airbag`. Rodar e comparar contra os alvos da seção 5.

**Pronto quando:** todos os alvos da seção 5 reproduzem dentro de **±0,5%**, e existe um teste
(`test_reproduz_fase_c`) que trava pelo menos 4 deles.

> **✅ CONCLUÍDA em 24/08 (Fase E).** `tests/test_acumulacao.py` trava 6 alvos (R1, R2, R4, R5, R7,
> R12) mais a modelagem de imposto. Resultado da reprodução na seção 8.

**Se não bater:** investigue e **registre a divergência no `analises.md`** antes de seguir. Os números da
Fase C vieram de scripts descartáveis e podem conter erro — reproduzir é justamente o teste disso. Uma
divergência encontrada aqui é resultado válido, não fracasso.

---

### Etapa 3 — Grid e protocolo de aceite

**Objetivo:** tornar impossível reportar um número isolado.

- `grid.py` executa o produto cartesiano dos parâmetros e devolve **pior caso, mediana, melhor caso e
  taxa de vitória** contra a baseline.
- O relatório gerado é **obrigado** a conter a decomposição da vantagem em (a) juro do caixa,
  (b) imposto realizado, (c) timing residual, mais a sensibilidade ao juro em 3 níveis
  (1,0% / 0,7% / 0,5% a.m.). Sem isso, não emite relatório.
- Implementar `Inclinacao` e `DoisAtivos` **apenas** para travar as reprovações da Fase C em teste.

**Pronto quando:** um comando único reproduz as tabelas C4, C5, C6, C7 e C8 do `analises.md`.

> **✅ PARCIALMENTE CONCLUÍDA em 24/08 (Fase E).** `grid.py` + `cli.py --tudo` entregam o grid
> obrigatório com pior/mediana/melhor/taxa de vitória, a sensibilidade ao juro (C5) e o imposto (C6).
> Falta: implementar `Inclinacao` e `DoisAtivos` para travar as reprovações C2 e C3 em teste.

---

### Etapa 4 — Corrigir a documentação de dinheiro real

**Objetivo:** o `PLANO_OPERACIONAL_REAL.md` hoje contém três afirmações que a Fase C contradiz.

1. **Trocar a EMA200 por EMA250 ou EMA300.** A EMA200 é a **pior das 6 médias testadas** e a única cujo
   pior caso ficou abaixo do DCA fixo. EMA300 fez 17 operações contra 29 da EMA200 — menos imposto,
   menos chicote.
2. **Despriorizar o tier VIP de taxas** (seção 5, item 2). Vale **R$ 210 em 6,4 anos** neste perfil de
   12 operações/ano. Não é errado, é irrelevante — e ocupa o lugar de coisas que importam.
3. **Registrar a origem da vantagem do airbag.** O documento apresenta o airbag como redutor de queda
   (correto) sem dizer que a vantagem de retorno medida é **~90% CDI** e encolhe ~40% com IR. Isso muda o
   argumento: o airbag é seguro contra queda, não gerador de retorno — e é **sensível à Selic**.
4. Corrigir a tabela da seção 4 (hoje traz "≈+400%" e "~25-35%" como estimativas) pelos números medidos.
5. No `Prompt.md`, adicionar ao aviso de status que o Projeto A está congelado e apontar para este plano.

**Pronto quando:** nenhuma afirmação numérica dos documentos de dinheiro real está sem lastro em
`analises.md` ou em artefato de `data/acumulacao/`.

> **✅ CONCLUÍDA em 24/08 (Fase E)**, e com **uma correção a mais do que este plano previa**: a
> vantagem de retorno do airbag não sobrevive ao block bootstrap do caminho de preço (vence o DCA em
> 31–59% das histórias reamostradas, contra os 40/42 = 95% do histórico único). O
> `PLANO_OPERACIONAL_REAL.md` foi reescrito e, **dado o perfil declarado pelo usuário** (sem limite
> de queda, sem saques, maximizar dinheiro), a recomendação mudou para **DCA puro sem airbag** — o
> airbag cobra imposto e atenção para entregar proteção que ele disse não precisar.

---

### Etapa 5 — Perguntas ainda abertas

Em ordem de valor esperado. **Cada uma passa pelo protocolo 3.1 do `analises.md`.**

> **Reordenação após a Fase E (perfil do usuário conhecido):** como ele declarou não ter limite de
> drawdown e não fazer saques, tudo que vende conforto (airbag, banda, fatia) perde prioridade, e o
> item **5 (câmbio BRL/USD)** sobe para o topo — é a única lacuna que pode mover o resultado em
> dezenas de pontos percentuais e o benchmark dele é em reais.

1. **Checagem mensal em vez de semanal.** *(mais promissora — não testada)* Reduziria operações,
   imposto e chicote, e poderia ser fundida com o dia do aporte — uma única data no mês, uma única
   rotina. A Fase C indica que médias mais lentas e menos operações se saíram melhor; isso é a versão
   extrema disso.
2. **Banda de tolerância.** Só sair se o preço fechar X% abaixo da média (ex.: 3%, 5%), em vez de no
   cruzamento exato. Ataca diretamente o chicote — o modo de falha visível na lateral de 2024 (−15%).
3. **Fatia ótima no airbag.** A Fase C testou 30/50/100% num eixo só. Falta o grid completo. Fatia
   menor = menos imposto e menos custo nas altas, com menos proteção.
4. **Aporte único vs. mensal**, para dinheiro que já está parado. *(Usuário consultado em 24/08:
   **ainda não decidido** — declarou estar "em fase de compreensão", que o dinheiro é de
   investimento, **não** para sustento, e que **não haverá saques**. Portanto: horizonte longo e sem
   necessidade de liquidez. As duas variantes seguem em aberto e ambas devem ser medidas.)*
5. **Câmbio BRL/USD.** Não modelado e **material**: os preços estão em dólar e o benchmark do usuário
   (CDB) é em reais. A desvalorização do real no período torna os resultados atuais **conservadores**,
   mas o correto é medir.
6. ~~**Tempo submerso**~~ — **MEDIDO na Fase E.** Implementado em `metricas.py::tempo_submerso`.
   Resultado que muda a leitura: no DCA puro a carteira passa **apenas 7% dos dias** valendo menos
   que o total depositado, com pior sequência de **69 dias**. A queda de 68% assusta muito mais do
   que dói, porque os aportes continuam entrando. O argumento comportamental do C8 fica bem mais
   fraco do que parecia. *(Prioridade rebaixada: pergunta respondida.)*
7. **Regras tributárias corretas** (domicílio da corretora, isenção de R$ 35k/mês, Lei 14.754/2023). A
   Fase C usou 15% liso como ordem de grandeza. **Confirmar com contador antes de virar recomendação.**

---

## 5. Números-alvo de reprodução (Etapa 2)

Setup: `data/raw/macro/BTCUSDT_1d.csv`, fechamento diário, **05/04/2020 → 22/08/2026**, 77 aportes de
**R$ 2.000** no fechamento do dia 5, total aportado **R$ 154.000**, taxa **0,075%**/operação, caixa
**1,0% a.m.**, sem imposto salvo indicação. Airbag: checagem semanal, sai abaixo da média, volta acima,
100% da fatia salvo indicação.

| # | cenário | alvo |
| :--- | :--- | ---: |
| R1 | CDB 1% a.m. | **231.566** |
| R2 | DCA fixo BTC | **382.177** (maxDD 68%) |
| R3 | DCA fixo, taxa 0,02% | **382.387** |
| R4 | Airbag EMA200, domingo, atraso 0 | **480.754** |
| R5 | Airbag EMA200, quarta, atraso 0 | **317.516** *(pior das 42 — sentinela de regressão)* |
| R6 | Airbag EMA300, mediana dos 7 dias | **500.315** |
| R7 | Grid 6 médias × 7 dias: mediana / vitórias | **486.722** / **40 de 42** |
| R8 | Grid com caixa a 0% a.m.: vantagem / vitórias | **+2,3%** / **24 de 42** |
| R9 | Grid com IR 15% e liquidação final: DCA / airbag mediana | **347.689** / **404.199** |
| R10 | Inclinação, reserva 20%, escada 0,85/1,00 | **367.789** *(deve perder para R2)* |
| R11 | BTC/ETH 80/20, rebalanceio por aporte | **361.307** *(deve perder para R2)* |
| R12 | Pior início (05/11/2021 → fim), DCA / CDB | **212.714** / **157.039** |
| R13 | 71 inícios possíveis: vitórias do DCA sobre o CDB | **48 de 71**, mediana **1,29x** |

Médias móveis do grid: EMA100, EMA150, EMA200, EMA250, EMA300, SMA200. EMA com semente = SMA dos
primeiros `span` valores, `alpha = 2/(span+1)`. Caixa capitalizado diariamente a
`(1+taxa_mensal)^(1/30,4375) − 1`.

---

## 6. O que NÃO fazer

- ❌ **Não modificar os scripts do Projeto A** nem `tests/test_engine.py` (seção 2).
- ❌ **Não escrever em `data/experimentos/`** — é o registro do Projeto A. Use `data/acumulacao/`.
- ❌ **Não reabrir as ideias reprovadas na Fase C** (inclinação de aporte, bloqueio de aporte por
  pessimismo, BTC+ETH 80/20) sem hipótese nova e mecanismo diferente. As três têm causa identificada.
- ❌ **Não julgar nenhuma variante por um único conjunto de parâmetros.** É o erro que a Fase C cometeu
  e corrigiu (achado C10).
- ❌ **Não apresentar vantagem de retorno sem decompor juro / imposto / timing** (achado C5).
- ❌ **Não usar os critérios de aceite da seção 3 do `analises.md`** (Sharpe de trading, blocos OOS, DSR)
  para acumulação — foram desenhados para edge de trading. Use a seção **3.1**.
- ❌ **Não prometer retorno.** O ganho vem de o BTC subir. O laboratório mede regras em volta disso; não
  cria retorno onde não há.

---

## 7. Glossário mínimo

- **DCA / aporte fixo:** comprar um valor fixo em data fixa, sem olhar preço.
- **Airbag:** vender a fatia protegida quando o preço fecha abaixo de uma média longa; recomprar quando
  volta acima. Reage, não prevê.
- **maxDD (queda máxima):** maior queda percentual do patrimônio acumulado desde um topo.
- **Chicote (whipsaw):** preço cruza a média para os dois lados sem tendência; a regra vende barato e
  recompra caro repetidamente.
- **Carry:** retorno que vem de manter o dinheiro num ativo remunerado (aqui, o CDI do caixa), não de
  acertar o movimento do mercado.
- **Grid:** varredura do produto cartesiano dos parâmetros, usada para separar mecanismo de sorte.

---

## 8. Resultado da execução (Fase E, 24/08/2026)

### Reprodução da Fase C — 10 de 13 alvos batem exatamente

| # | cenário | alvo | obtido | erro |
| :--- | :--- | ---: | ---: | ---: |
| R1 | CDB 1% a.m. | 231.566 | **231.566** | 0,00% |
| R2 | DCA fixo BTC (maxDD 68%) | 382.177 | **382.177** | 0,00% |
| R3 | DCA fixo, taxa 0,02% | 382.387 | **382.387** | 0,00% |
| R4 | Airbag EMA200, domingo | 480.754 | **480.754** | 0,00% |
| R5 | Airbag EMA200, quarta *(sentinela)* | 317.516 | 316.214 | −0,41% |
| R6 | Airbag EMA300, mediana dos 7 dias | 500.315 | 494.484 | −1,17% |
| R7 | Grid 42: mediana / **vitórias** | 486.722 / 40 de 42 | 483.923 / **40 de 42** | −0,57% |
| R8 | Grid caixa 0%: vantagem / vitórias | +2,3% / 24 de 42 | +1,7% / 23 de 42 | — |
| R9a | IR 15%: DCA fixo | 347.689 | **347.950** | +0,08% |
| R9b | IR 15%: airbag / **vitórias** | 404.199 / 36 de 42 | 401.466 / **36 de 42** | −0,68% |
| R12 | Pior início (nov/21): DCA / CDB | 212.714 / 157.039 | **212.714** / **157.039** | 0,00% |

**As contagens de vitória batem exatamente** (40/42, 36/42) e os benchmarks-chave batem a zero. As
três divergências residuais ficam em ~1% e não movem nenhuma conclusão — registradas aqui em vez de
perseguidas, conforme a orientação da Etapa 2.

### A divergência que valeu a etapa inteira

A primeira versão do motor errava o alvo R9b em **+9,9%** e marcava 40/42 vitórias em vez de 36/42.
Causa: cobrava o IR **só na liquidação final**, em vez de **na venda**. Cobrar tudo no fim subestima o
custo do giro — quem realiza ganho pelo caminho perde a composição sobre o imposto pago. **É
literalmente o alerta do achado C6, e a implementação nova caiu nele.** Corrigido em
`imposto.py::imposto_da_venda`, o erro caiu para −0,68% e as vitórias bateram exatamente.

Isso é o que a Etapa 2 existia para pegar. Travado por `test_ir_sai_do_caixa_na_venda_e_nao_so_no_resgate`.

### Achado novo: o benchmark que faltava (releitura do C5)

O C5 conclui que "~90% da vantagem do airbag é CDI, não market timing". É verdade **contra o DCA
100% BTC** — mas o airbag fica ~40% do tempo fora do mercado. Contra uma carteira **passiva de mesma
exposição média** (`PassivoIsoExposicao`, zero operações):

| comparação | com CDI 1% a.m. | **sem carry (caixa 0%)** |
| :--- | ---: | ---: |
| airbag vs DCA 100% BTC | +26,6% | **+1,7%** |
| airbag vs passivo 60/40 iso-exposição | +50,2% | **+33,4%** |

O timing do airbag **não é bom o bastante para bater exposição total**, mas **é bom o bastante para
tornar a fatia em caixa quase gratuita**. *"A vantagem é carry"* e *"o timing não vale nada"* são
afirmações diferentes, e só a primeira é verdadeira.

### Achado novo: a vantagem do airbag não sobrevive à reamostragem

Block bootstrap dos log-retornos do BTC, varrendo blocos de 90/180/365/730 dias × 2 sementes
(o próprio critério 1 do protocolo 3.1: nunca julgar por um ponto só):

| | histórico único | reamostrado |
| :--- | :--- | ---: |
| P(DCA em BTC > CDB) | "48 de 71 = sempre com ≥4 anos" | **71% a 82%** |
| P(Airbag > DCA fixo) | "40 de 42 = 95%" | **31% a 59%** |

P(Airbag > DCA) **cresce com o comprimento do bloco** — ou seja, a vantagem depende inteiramente de o
cripto continuar tendo ciclos longos e persistentes como o de 2022. Coerente com o C5.

**O que sobrevive:** a redução de queda (68% → 45%), que é mecânica.

### Como rodar

```
python -m scripts.acumulacao.cli --reproduzir   # alvos R1..R12
python -m scripts.acumulacao.cli --timing       # airbag vs iso-exposição
python -m scripts.acumulacao.cli --evidencia    # block bootstrap
python -m scripts.acumulacao.cli --tudo
pytest tests/test_acumulacao.py                 # 16 testes
```

### O que NÃO foi feito

- `Inclinacao` e `DoisAtivos` (Etapa 3): faltam os testes que travam as reprovações C2 e C3.
- Câmbio BRL/USD (Etapa 5, item 5): **prioridade nº 1 agora.**
- Banda de tolerância e fatia ótima do airbag: despriorizadas — vendem conforto que o usuário
  declarou não precisar.
