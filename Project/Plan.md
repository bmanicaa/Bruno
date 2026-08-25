# Plan.md — O que fazer a seguir

> **Versão:** 25/08/2026 · Substitui integralmente o plano anterior (Projeto B / laboratório de
> acumulação), que foi **executado e concluído** na Fase E. O histórico dele vive no `analises.md`.
> **Este arquivo só contém trabalho ainda não feito.** Se estiver vazio, não há trabalho pendente.

---

## Onde estamos, em cinco linhas

1. O motor de swing (**Projeto A**) está **congelado**. Não por refutação: o protocolo tem poder zero
   abaixo de Sharpe ~1,2, e o lucro **bruto** da melhor configuração é **+R$311 em 3,4 anos**. Não há
   o que colher nessa família, e testar mais só piora a régua.
2. O fluxo de acumulação (**Projeto B**) foi medido, reproduzido no repositório e submetido ao mesmo
   rigor. A recomendação de dinheiro real é **DCA puro em Bitcoin**, sem airbag e sem alavancagem.
3. A vantagem de retorno do airbag **não sobrevive à reamostragem** (vence em 31–59% das histórias).
   Só a redução de queda sobrevive — e é conforto, que o usuário declarou não precisar.
4. O usuário: **sem limite de drawdown, sem saques, sem uso para sustento, horizonte longo,
   objetivo de maximizar dinheiro.** Toda priorização abaixo decorre disso.
5. **Restrição travada, não negociável: nunca alavancar.** Numa queda de 68% — que já aconteceu — o
   dobro é perda de 100%, e ruína é absorvente.

---

## Os três trabalhos pendentes, em ordem de impacto no dinheiro

### 1. O Bitcoin é o ativo certo? ⭐ comece por aqui

**O buraco.** O projeto inteiro — Projeto A e Projeto B, todas as fases — **assumiu** que o ativo é o
Bitcoin, e gastou o esforço todo em *regras em volta dele*. Ninguém nunca testou a decisão que pesa
mais: **qual ativo comprar**. Para quem maximiza crescimento, a escolha do ativo domina qualquer
regra de entrada e saída por uma ordem de grandeza.

**O que existe.** `data/raw/coins/` tem **550 moedas** com série diária, das quais **28 têm dados
desde 05/04/2020** (o início da simulação), incluindo delistadas — EOS, GTO, TCT, ONG — o que reduz o
viés de sobrevivência.

**O que medir.** Todas com aporte mensal fixo, mesmos custos, mesmo período:

| variante | descrição |
| :--- | :--- |
| `BTC` | baseline atual |
| `BTC+ETH` | pesos fixos, rebalanceio só pelo aporte (o mecanismo já validado no C3) |
| `cestaN` | N maiores por liquidez *point-in-time*, rebalanceada pelo aporte, N ∈ {3, 5, 10} |
| `cesta_igual` | peso igual entre as 28 com histórico completo |

**Protocolo obrigatório:** o da seção 3.1 do `analises.md` (grid, decomposição, imposto, sensibilidade
ao juro, regimes, maxDD, robustez de início) **mais** o bootstrap de caminho de preço da Fase E, e
**mais** o critério de crescimento logarítmico da Etapa 4c — que é o que decide para este usuário.

**Armadilhas.**
- **Viés de sobrevivência é o risco nº 1 aqui.** Uma cesta montada com as moedas que hoje existem é
  uma máquina de mentir. A seleção tem de ser *point-in-time* (só o que era negociável na data) e as
  delistadas têm de entrar e sair.
- Rebalancear **só pelo aporte**, nunca vendendo — o C3 mostrou que o mecanismo é sadio e evita
  evento tributário. Rebalanceio com venda é outra estratégia e precisa de teste próprio.
- **Não confundir "o ETH não pagou" com "diversificar não paga".** Foi o erro que o C3 quase induziu.

**Pronto quando:** existe uma tabela com pior caso / mediana / melhor caso / crescimento logarítmico
para cada variante, com IC do bootstrap, e uma frase dizendo se a recomendação de ativo muda.

---

### 2. Câmbio BRL/USD

**O buraco.** Os preços de todo o repositório estão em **dólar**; o benchmark do usuário (CDB) está em
**reais**. O câmbio **nunca foi modelado** — está registrado como limitação desde a Fase C e nunca foi
medido.

**Por que importa.** Muda todos os números da comparação contra o CDB. A direção esperada é
**favorável** (o real desvalorizou no período), o que tornaria os resultados atuais conservadores —
mas "esperado" não é medido, e é justamente esse tipo de suposição que este projeto existe para matar.

**O que fazer.** Obter a série diária BRL/USD do período (05/04/2020 → hoje), converter a série de
preços, e **re-rodar tudo**: R1, R2, os benchmarks e a alocação ótima. Reportar lado a lado com os
números em dólar.

**Armadilha.** O aporte é em reais e fixo em reais. Converter o resultado final no fim é **errado**:
cada aporte compra a uma taxa de câmbio diferente. A conversão tem de entrar **no dia do aporte**.

**Pronto quando:** todas as tabelas do `PLANO_OPERACIONAL_REAL.md` têm versão em reais, e a linha
"câmbio não modelado" sai da seção 7 daquele documento.

---

### 3. Aporte único vs. aporte mensal

**O buraco.** O `Plan.md` anterior marcou isto como pendente e mandou perguntar ao usuário. Ele
respondeu em 24/08 que **ainda não decidiu** o tamanho nem a forma, e que o dinheiro é de
investimento, sem saques. Portanto as duas variantes seguem abertas e **ambas precisam ser medidas** —
são perguntas matematicamente diferentes.

**O que medir.** Para um montante que já existe: entrar de uma vez **vs** parcelar em 3, 6, 12, 24
meses. Todos os meses de início possíveis, reportando taxa de vitória e mediana (critério 7 da
seção 3.1) — nunca um início escolhido.

**Armadilha.** A intuição diz "parcelar é mais seguro", e no agregado histórico normalmente **perde**
para a entrada única, pelo mesmo mecanismo de arrasto de caixa que reprovou o C2 (12/12). Medir sem
supor, e **decompor a diferença em juro do caixa vs timing**, como manda o critério 2.

**Pronto quando:** existe uma recomendação com números para o caso "tenho R$ X parado agora".

---

## O que NÃO fazer

- ❌ **Mais configurações de swing.** Poder zero e bruto zero. Testar mais só aumenta `n_trials` e
  piora a régua para todos os testes futuros.
- ❌ **Cortar custo do swing achando que resolve.** Retirado em 25/08: o bruto é +R$311; corretagem
  zero também dá zero. Ver `analises.md`, Fase E, E2a.
- ❌ **Variações do airbag** (banda de tolerância, fatia ótima, checagem mensal). Vendem redução de
  queda, que o usuário declarou não precisar, e cuja vantagem de retorno já se mostrou cara-ou-coroa.
- ❌ **O teste de holdout** (`HOLDOUT = 2026-02-01 → 2026-08-20`). Só faz sentido se algo passar nos
  portões anteriores. Nada passa. É cerimônia.
- ❌ **Corrigir o bug de vesting** (`'OP' in s` casa com 7 moedas). É bug real, mas só afeta o Projeto A,
  que está congelado.
- ❌ **Reabrir as ideias já reprovadas com mecanismo identificado:** aporte com inclinação, bloqueio de
  aporte por pessimismo, BTC+ETH 80/20 na forma testada.
- ❌ **Modificar os scripts congelados do Projeto A.** Lista em `README.md`. Se achar que precisa,
  pare e pergunte.

---

## O limite que nenhum teste vence

Sete anos de cripto contêm essencialmente **um ciclo grande**. Quase toda pergunta feita a estes dados
volta como *"favorável, mas não comprovado"*, porque a resposta depende de um ciclo só. Os três
trabalhos acima valem a pena porque **mexem em decisões concretas** — não porque vão produzir certeza.

Qualquer sessão futura que prometa certeza a partir desta base está errada.
