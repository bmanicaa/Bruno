# Plano Operacional Real — Acumulação em Bitcoin

> Versão: **24/08/2026 (revisão da Fase E)** | Baseado em medição, não em eliminação
> Objetivo: instruções simples para investir com a melhor relação retorno/risco que a evidência
> permite hoje — dizendo com honestidade o que está comprovado e o que não está.

---

## 0. O que mudou nesta revisão (leia primeiro)

A versão anterior deste documento foi escrita **por eliminação**: nada de trading funcionou, então
sobrou "comprar Bitcoin + airbag". A Fase C mediu esse plano pela primeira vez e a Fase E o submeteu
ao mesmo rigor estatístico que reprovou o motor de swing. Três coisas mudaram:

1. **A vantagem de RETORNO do airbag não está comprovada.** No histórico real ele venceu em 40 de 42
   combinações de parâmetro. Mas reamostrando o caminho de preço (block bootstrap), ele vence o DCA
   fixo em apenas **31% a 59% das vezes** — cara-ou-coroa. A vitória histórica depende de **como o
   bear de 2022 se posicionou nesta série específica**, não de uma propriedade geral da regra.
2. **A redução de queda do airbag continua real** (68% → 45%). Isso é mecânico e sobrevive a tudo.
   É o produto verdadeiro dele — proteção, não retorno.
3. **A EMA200 é a pior das 6 médias testadas.** Se você usar o airbag, use EMA250 ou EMA300.

**Consequência para você:** a escolha entre "DCA puro" e "DCA + airbag" **não é uma escolha entre
mais e menos dinheiro**. É uma escolha entre mais e menos sofrimento no caminho, com o dinheiro
final sendo estatisticamente empatado. Ver seção 3.

---

## 1. As três coisas que os testes realmente provaram

1. **Nada que testamos bateu o simples "comprar Bitcoin e segurar".** 36 configurações de trading em
   4 famílias, e nenhuma se sustenta.
2. **Mas "não provamos que funciona" ≠ "provamos que não funciona".** A Fase E mediu a própria régua
   e descobriu que ela só consegue aprovar estratégias excepcionais (Sharpe acima de ~1,2). Uma
   estratégia boa de verdade seria reprovada por falta de dados, não por falta de mérito. **Ninguém
   sabe se o trading de swing funciona neste tamanho de amostra — nem que sim, nem que não.**
3. **Não existe estratégia aprovada que garanta lucro.** Quem prometer isso está mentindo.

Portanto: **acumular Bitcoin aos poucos, por muitos anos.** O ganho vem de o Bitcoin subir. Nenhuma
regra em volta disso cria retorno onde não há.

---

## 2. O alerta matemático mais importante deste documento

Você disse não ter limite de tolerância a quedas, desde que a matemática esteja a favor. Isso é uma
postura legítima — **e não autoriza alavancagem.**

- Uma queda de **68%** já aconteceu no período testado.
- Numa queda de 68%, uma posição **alavancada em 2x é perda de 100%**.
- **Zero é absorvente.** Horizonte longo não recupera capital que chegou a zero. Não existe "esperar
  passar" depois da liquidação.

A matemática que maximiza crescimento de capital no longo prazo (critério de Kelly) **proíbe
explicitamente** os tamanhos de aposta que podem zerar — não por medo, por aritmética: acima de certo
ponto, aumentar a aposta **reduz** o crescimento esperado, e mais adiante o torna negativo mesmo com
vantagem real.

**Regra travada: nunca use alavancagem, margem ou produtos alavancados neste plano.**

---

## 3. A decisão que você precisa tomar (e os números dela)

Período medido: 05/04/2020 a 22/08/2026 · aportes de R$ 2.000 no dia 5 de cada mês ·
**R$ 154.000 aportados** · taxa 0,075% · caixa a 1% a.m.

| | **DCA puro** | **DCA + Airbag** |
| :--- | ---: | ---: |
| Valor final (sem IR) | 382.177 | 483.923 *(mediana de 42 combinações)* |
| Valor final (com IR 15%) | 347.950 | 401.466 |
| Pior queda | **68%** | **45%** |
| Tempo com a carteira abaixo do total depositado | 7% dos dias (pior sequência: **69 dias**) | menor |
| Operações em 6,4 anos | 77 compras | 77 compras + ~17 a 36 trocas |
| Eventos tributários | **nenhum** até você sacar | 12 a 14 vendas tributáveis |
| Esforço | 1 compra/mês | 1 compra/mês + 1 checagem/semana |
| **Vantagem de retorno é confiável?** | — | **não** (vence em 31–59% das histórias reamostradas) |

**Como ler isto:**

- Os **R$ 100 mil a mais** do airbag no histórico real são majoritariamente **juro do caixa (CDI)**,
  não acerto de mercado. Zerando o juro do caixa, a vantagem cai para **+1,7%** — praticamente nada.
- Isso significa que o airbag é, na prática, **um jeito de ficar no CDI ~40% do tempo** sem pagar o
  preço normal de ter menos exposição. É uma boa engenharia — mas **depende da Selic alta**, um risco
  brasileiro que não tem nada a ver com cripto.
- **A queda de 68% assusta mais do que dói.** O número que mede sofrimento de verdade é o tempo com a
  carteira valendo menos que o total depositado: **7% dos dias, no máximo 69 dias seguidos**. Porque
  você segue aportando, a carteira raramente fica "no vermelho" contra o que você pôs nela.

**Recomendação, dado o que você declarou** (sem limite de queda, sem saques, dinheiro que não é para
sustento, horizonte longo, objetivo de maximizar dinheiro):

> ### 👉 **DCA puro em Bitcoin. Sem airbag.**
>
> O airbag cobra imposto, operações, atenção semanal e risco de chicote, para entregar uma proteção
> contra quedas que **você disse não precisar** — e uma vantagem de retorno que **não está
> comprovada**. Para o seu perfil declarado, ele é custo sem benefício correspondente.
>
> **Se em algum momento você perceber que uma queda de 60%+ te faria abandonar o plano, mude para o
> airbag imediatamente.** Um plano abandonado no fundo rende zero, e aí os 45% valem muito mais que
> os 68%. Essa é a única razão boa para usá-lo — e é uma razão sobre você, não sobre o mercado.

---

## 4. A regra que você executa

### Regra única — Compra mensal (DCA), 1x por mês, dia fixo

1. Escolha um dia do mês (ex.: dia 5) e um valor fixo em reais.
2. Nesse dia: compre Bitcoin com esse valor, **sem olhar se o preço subiu ou caiu**.
3. **Nunca venda** por queda. Só venda se precisar do dinheiro na vida real.
4. Fim. Não há regra 2.

> **Por que o aporte deve ser fixo e incondicional:** a Fase C testou 12 formas de "comprar mais
> quando está barato" (reservar parte do aporte para gastar nas quedas). **As 12 perderam** para o
> aporte fixo, de −1,4% a −6,9%, e a perda cresce junto com a fração reservada. O motivo é simples:
> com aporte total constante, comprar mais no barato exige comprar menos no caro — e num ativo com
> tendência de alta, "caro" ainda era preço lucrativo. Vale igual para o inverso: **não reduza nem
> pule o aporte porque o mercado está feio.** Os meses de medo são justamente os de preço baixo.

### Se você optar pelo airbag (checagem semanal, 2 minutos)

- Use a **EMA250 ou EMA300** — **não a EMA200**. A EMA200 é a pior das seis médias testadas e a única
  cujo pior caso ficou abaixo do DCA puro. A EMA300 fez **17 operações** contra 29 da EMA200: menos
  imposto, menos chicote.
- Checagem **sempre no mesmo dia e horário**. Se o preço fechou abaixo da média, venda; se voltou
  acima, recompre. Se nada mudou, não faça nada.
- **Ignorar a vontade de "aproveitar" movimentos do meio da semana é parte da estratégia.**

---

## 5. Configuração (uma única vez)

1. **Conta numa corretora confiável.** Complete a verificação de identidade.
2. **Defina seu valor mensal** — apenas o que você pode deixar parado por 4+ anos.
3. **Agende o lembrete mensal.** (E o semanal, só se usar o airbag.)
4. **Anote cada operação**: data, valor, preço do BTC. É o histórico real que depois comparamos com
   o simulador.
5. **Não se preocupe com o tier VIP de taxas.** A diferença entre 0,075% e 0,02% neste perfil, em 6,4
   anos, é de **R$ 210**. O conselho estava certo em percentual e é irrelevante em reais para quem
   faz 12 operações por ano — foi herdado do contexto de swing (200+ trades/ano), onde importa de
   verdade. **O imposto é ~270x mais importante que a taxa** e merece a atenção que a taxa recebia.

---

## 6. O que NÃO fazer

- ❌ **Nunca alavancar.** Ver seção 2. Esta é a única regra deste documento que não admite exceção.
- ❌ Não vender em pânico.
- ❌ Não "adiantar" a compra mensal porque "vai subir" (nem atrasar porque "vai cair").
- ❌ Não reduzir nem pular o aporte em meses de medo (reprovado 12/12 na Fase C).
- ❌ Se usar o airbag: não checar a média todo dia. A regra é semanal.
- ❌ Não operar o engine de swing com dinheiro real. Ele segue em observação no laboratório.
- ❌ Não investir dinheiro de contas, emergências ou dívidas.

---

## 7. O que ainda não sabemos (honestidade sobre os limites)

| pergunta | estado |
| :--- | :--- |
| **Câmbio BRL/USD** | **Não modelado.** Os preços estão em dólar e seu benchmark (CDB) é em reais. A desvalorização do real no período torna os números acima **conservadores** — mas o correto é medir. |
| **Regras tributárias exatas** | Usamos 15% liso como ordem de grandeza. Domicílio da corretora, isenção de R$ 35.000/mês e a Lei 14.754/2023 mudam a conta. **Confirmar com contador antes de virar recomendação.** |
| **O Bitcoin continuar subindo** | É a aposta de fundo de tudo isto, e **não é comprovável**. Reamostrando o histórico, o DCA em BTC vence o CDB em 71% a 82% das vezes — favorável, não garantido. |
| **Trading de swing funcionar** | **Indeterminado**, não refutado. Ver seção 1, item 2. |

---

## 8. Estado do laboratório

- Motor de testes **matematicamente íntegro** (V2.3.1): zero lookahead, **67 testes automáticos**,
  validação estatística com bootstrap e correção de múltiplos testes.
- **36 configurações** de 4 famílias testadas: nenhuma aprovada — mas a Fase E mostrou que **a régua
  não tinha poder para aprovar nada abaixo de Sharpe ~1,2**, então esse "nenhuma" diz menos do que
  parecia. O que trava o veredito não é o método nem as estratégias: é a **quantidade de dados**.
- A candidata que mais se aproximou (`ac35a444`) tem expectância de **+0,07R com intervalo de
  confiança de [−0,22, +0,40]** — 33% de chance de o edge verdadeiro ser negativo. Não é uma
  estratégia ruim comprovada; é uma estratégia **desconhecida**.
- Testamos usar o próprio airbag como filtro do robô de swing: **não funcionou**, e por um motivo
  instrutivo — o robô **já fazia isso**, a condição sempre esteve embutida nas regras dele.

---

## 9. Resumo de uma linha

> **Compre Bitcoin todo mês, no mesmo dia, sem olhar o preço, e não venda. Nunca alavanque.**
