# Carry de funding — medicao completa

> Gerado por `python -m carry tudo`. Artefatos: `data/carry/grid.json`, `data/carry/evidencia.json`.

Periodo 6.95 anos | capital inicial R$ 100,000 | 750 configuracoes | base = `premium`


## 1. Tabela comparativa (mesmo periodo, mesmos custos)

| Estrategia | Patrimonio final | CAGR | Max DD | Direcional? |
|---|---:|---:|---:|---|
| Carry — melhor das 750 | R$ 245,197 | +13.78% | — | nao |
| Carry — mediana do grid | R$ 126,571 | — | — | nao |
| Carry — pior das 750 | R$ 23,590 | -18.77% | — | nao |
| **CDI 1% a.m.** | R$ 229,338 | +12.69% | 0.0% | nao |
| DCA BTC (12 parcelas) | R$ 895,414 | +37.09% | 75.9% | sim |
| BTC comprado e segurado | R$ 764,502 | +34.01% | 76.7% | sim |

Configuracoes que superam o CDI: **39 de 750 (5.2%)** — e a melhor delas o faz por 6.9% em 6.9 anos, apos ser escolhida entre 750 tentativas correlacionadas.


## 2. Decomposicao (protocolo, item 3)

Duas configuracoes: a de referencia (BTC, 1x, semanal) e a MELHOR do grid. A segunda importa porque e a que um leitor apressado citaria.

| Termo | referencia BTC 1x | melhor do grid |
|---|---:|---:|
| (a) funding recebido | +46,099 | +59,217 |
| (b) convergencia da base | -256 | +1,099 |
| (c) taxas e slippage | -3,929 | -23,911 |
| (d) juro do caixa livre (CDI) | +11,360 | +108,840 |
| (f) quebra de hedge / liquidacao | +0 | -49 |
| (e) residuo | -0 | +0 |
| **ganho total** | **+53,275** | **+145,197** |
| _memo:_ % do ganho que e (d) CDI | 21% | 75% |

A melhor configuracao do grid e `BTC_ETH / gatilho funding/7/0.0001 / 3x / semanal`. Ela fica montada em apenas **775 de 2539 dias (31% do tempo)**, com exposicao media de 19% do patrimonio. Nos outros 69% o dinheiro esta em caixa rendendo CDI — dai **75% do ganho dela ser o item (d)**. E a repeticao literal do achado C5 do `analises.md` ("~90% da vantagem e CDI, nao market timing"): a configuracao vencedora vence por operar menos, nao por colher mais.

O excesso dela sobre o CDI e de **0.97% ao ano** — contra um efeito minimo detectavel de ~8% a.a. (secao 7) — e ela e o MAXIMO de 750 tentativas correlacionadas sobre a mesma serie. Tratar esse numero como edge seria garimpo.

Capital medio imobilizado na referencia (spot + margem): R$ 124,075, que deixou de render R$ 103,002 de CDI ao longo do periodo — mais do que os R$ 46,099 de funding que a estrutura coletou. **O custo de oportunidade da margem sozinho supera a receita bruta da estrategia.**


## 3. Grid por eixo (pior / mediana / melhor / vitorias sobre CDI)


**Cesta**

| valor | n | pior | mediana | melhor | vitorias vs CDI |
|---|---:|---:|---:|---:|---:|
| BTC | 150 | R$ 101,139 | R$ 160,303 | R$ 242,901 | 21/150 |
| BTC_ETH | 150 | R$ 65,260 | R$ 151,935 | R$ 245,197 | 16/150 |
| TOP10 | 150 | R$ 26,189 | R$ 109,481 | R$ 211,866 | 0/150 |
| TOP20 | 150 | R$ 23,590 | R$ 97,967 | R$ 188,391 | 0/150 |
| TOP5 | 150 | R$ 38,481 | R$ 127,705 | R$ 234,758 | 2/150 |

**Alavancagem**

| valor | n | pior | mediana | melhor | vitorias vs CDI |
|---|---:|---:|---:|---:|---:|
| 1 | 250 | R$ 41,152 | R$ 126,867 | R$ 229,342 | 1/250 |
| 2 | 250 | R$ 28,721 | R$ 126,794 | R$ 241,133 | 17/250 |
| 3 | 250 | R$ 23,590 | R$ 126,493 | R$ 245,197 | 21/250 |

**Rebalanceio**

| valor | n | pior | mediana | melhor | vitorias vs CDI |
|---|---:|---:|---:|---:|---:|
| diario | 150 | R$ 23,590 | R$ 122,856 | R$ 243,488 | 7/150 |
| limiar/0.02 | 150 | R$ 23,601 | R$ 123,974 | R$ 244,300 | 7/150 |
| limiar/0.05 | 150 | R$ 23,642 | R$ 126,070 | R$ 244,034 | 7/150 |
| limiar/0.1 | 150 | R$ 24,005 | R$ 127,030 | R$ 243,006 | 7/150 |
| semanal | 150 | R$ 32,372 | R$ 142,719 | R$ 245,197 | 11/150 |

**Gatilho**

| valor | n | pior | mediana | melhor | vitorias vs CDI |
|---|---:|---:|---:|---:|---:|
| funding/1/0.0 | 75 | R$ 49,565 | R$ 70,832 | R$ 127,590 | 0/75 |
| funding/1/0.0001 | 75 | R$ 34,298 | R$ 133,559 | R$ 226,031 | 0/75 |
| funding/1/5e-05 | 75 | R$ 23,590 | R$ 55,811 | R$ 123,837 | 0/75 |
| funding/3/0.0 | 75 | R$ 90,549 | R$ 118,024 | R$ 158,363 | 0/75 |
| funding/3/0.0001 | 75 | R$ 97,898 | R$ 193,567 | R$ 240,149 | 16/75 |
| funding/3/5e-05 | 75 | R$ 52,559 | R$ 97,342 | R$ 160,380 | 0/75 |
| funding/7/0.0 | 75 | R$ 119,806 | R$ 139,609 | R$ 166,657 | 0/75 |
| funding/7/0.0001 | 75 | R$ 147,030 | R$ 219,697 | R$ 245,197 | 23/75 |
| funding/7/5e-05 | 75 | R$ 87,491 | R$ 129,234 | R$ 180,954 | 0/75 |
| sempre | 75 | R$ 111,380 | R$ 133,532 | R$ 178,715 | 0/75 |

## 4. Regimes (protocolo, item 7)

| regime | dias | CAGR da estrategia | funding bruto anualizado |
|---|---:|---:|---:|
| bear | 727 | +2.03% | +2.77% |
| bull | 1006 | +10.76% | +20.47% |
| indefinido | 198 | +8.38% | +15.46% |
| lateral | 607 | +3.87% | +6.27% |

O carry e uma aposta em bull market disfarcada de posicao neutra: quem paga o funding e o comprado alavancado, e ele so aparece em alta. Nem no regime mais favoravel a estrutura entrega o CDI — em bull, com o funding bruto anualizando +20,5%, o CAGR da estrategia fica em +10,8% contra os +12,7% do CDI. Em bear ela rende +2,0%. Uma renda que so existe quando o mercado sobe nao e renda fixa; e beta com outro nome.


## 5. O funding esta secando

| ano | settlements | funding bruto | % na banda morta (0,01%) | % negativo |
|---|---:|---:|---:|---:|
| 2019 | 338 | +2.31% | 66.9% | 18.3% |
| 2020 | 1098 | +17.24% | 50.5% | 14.3% |
| 2021 | 1095 | +30.61% | 43.1% | 7.3% |
| 2022 | 1095 | +4.16% | 30.8% | 22.1% |
| 2023 | 1095 | +7.87% | 38.5% | 10.1% |
| 2024 | 1098 | +11.96% | 42.1% | 8.4% |
| 2025 | 1095 | +5.13% | 17.2% | 12.9% |
| 2026 | 702 | +1.51% | 4.7% | 29.6% |

A coluna "banda morta" e a chave do mecanismo. A formula da Binance e

```
funding = premium + clamp(juro - premium, -0,05%, +0,05%),  juro = 0,01%/8h
```

Quando o premio esta entre -0,04% e +0,06%, o funding vale exatamente a constante de juro da corretora, 0,01%. **35,4% de todos os 7.616 settlements do BTC caem nesse ponto de massa** — ou seja, um terco do "carry historico" nao e premio de mercado nenhum, e uma convencao contabil da exchange. E ela esta sumindo: 66,9% dos settlements em 2019 contra 4,7% em 2026, com o funding negativo indo de 18,3% para 29,6%.


## 6. Bootstrap em blocos (protocolo, item 6)

Varredura de bloco (90/180/365/730 dias) x 3 sementes = 12 combinacoes, sobre a serie diaria da configuracao de referencia.

| metrica | min | mediana | max |
|---|---:|---:|---:|
| CAGR mediano | 0.0614 | 0.0623 | 0.0630 |
| IC95 inferior | 0.0382 | 0.0406 | 0.0445 |
| IC95 superior | 0.0884 | 0.0962 | 0.0988 |
| P(CAGR > CDI) | 0.0000 | 0.0000 | 0.0005 |
| P(CAGR > 0) | 1.0000 | 1.0000 | 1.0000 |

O **intervalo de confianca inteiro fica abaixo do CDI** (+12.69%): o teto do IC95 e +9.88% na combinacao mais generosa. P(carry > CDI) = 0.0005 no melhor caso das 12 combinacoes. Isso nao e "nao deu significativo"; e o contrario disso.


## 7. Poder do teste (protocolo, item 5)

Vol anual da estrategia: **0.55%** (delta-neutra de verdade). Autocorrelacao rho(1) dos retornos diarios: **0.61**.

| metodo | amostra efetiva | Sharpe minimo detectavel | excesso anual detectavel |
|---|---:|---:|---:|
| formula iid (INVALIDA aqui) | 2538 dias | 1.06 | 0.59% |
| corrigida por autocorrelacao | 56 dias | 7.17 | 3.97% |

A formula iid supoe que cada dia traz informacao nova. O funding e persistente — rho(10) ainda vale ~0,38 — e a amostra efetiva encolhe de 2538 para ~56 observacoes. Usar a versao ingenua aqui daria confianca ~6x maior do que os dados sustentam. A autoridade e o poder EMPIRICO abaixo, medido injetando excesso conhecido e passando pelo mesmo gate do veredito:

| excesso anual injetado | poder empirico |
|---:|---:|
| +0.00% | 0% |
| +2.00% | 0% |
| +5.00% | 1% |
| +8.00% | 77% |
| +12.00% | 100% |

**Leitura.** O teste so enxerga vantagens da ordem de +8% ao ano sobre o CDI. Mas a conclusao NAO depende disso: o carry nao ficou "sem significancia", ele ficou ~6 pontos percentuais ABAIXO do CDI, com o IC95 inteiro do lado de baixo. Um efeito grande e de sinal trocado nao precisa de poder para ser visto.


## 8. Quanto o funding teria de render para empatar com o CDI

| alavancagem | fator sobre o funding observado | funding bruto necessario |
|---|---:|---:|
| 1x | 2.08x | 22.1% a.a. |
| 2x | 1.73x | 18.4% a.a. |
| 3x | 1.75x | 18.6% a.a. |

Contra 10,6% a.a. observados na vida toda da serie — e 1,5% em 2026. Bisseccao multiplicando TODAS as taxas, inclusive as negativas.


## 9. Reserva de caixa, margem e liquidacao

| reserva | 1x: final | 1x: aportes | 1x: liq | 3x: final | 3x: aportes | 3x: desmontes | 3x: liq |
|---|---:|---:|---:|---:|---:|---:|---:|
| 50% em caixa | R$ 183,775 | 2 | 0 | R$ 201,644 | 41 | 0 | 0 |
| 30% em caixa | R$ 167,768 | 1 | 0 | R$ 190,057 | 40 | 0 | 1 |
| 20% em caixa | R$ 159,839 | 0 | 0 | R$ 183,375 | 38 | 3 | 1 |
| 10% em caixa | R$ 153,275 | 0 | 0 | R$ 154,858 | 2 | 39 | 1 |
| 5% em caixa | R$ 150,772 | 0 | 0 | R$ 152,476 | 2 | 39 | 1 |
| 2% em caixa | R$ 149,838 | 0 | 0 | R$ 151,502 | 2 | 39 | 1 |

A armadilha da alavancagem: subir de 1x para 3x liberta capital da margem e aumenta o funding coletado, mas so funciona com uma reserva grande — e reserva grande e dinheiro em CDI, que e justamente o que se esta tentando superar. O carry alavancado converge para "CDI com passos extras e risco de liquidacao".


## 10. Sensibilidade a base (o dado que o repositorio nao tem)

As klines vieram de `fapi.binance.com`: sao velas do PERPETUO. Nao ha serie de spot no repositorio, entao a base foi RECONSTRUIDA invertendo a formula de funding (exata fora da banda morta, censurada dentro).

| modo de base | patrimonio final | termo (b) |
|---|---:|---:|
| `zero` | R$ 153,579 | +0 |
| `premium` | R$ 153,275 | -256 |
| `pessimista` | R$ 153,209 | -323 |

O termo (b) e irrelevante em qualquer hipotese, e ha razao estrutural para isso: numa posicao delta-neutra mantida, o PnL de base e `notional x (base_entrada - base_saida)`, ele NAO se acumula com o tempo. A incerteza sobre a base nao muda o veredito.


## 11. O risco que nao esta em nenhum numero acima

**Risco de contraparte nao e backtestavel e nao foi backtestado.**

A estrutura exige spot e perpetuo na mesma corretora (ou colateral cruzado entre duas). Em novembro de 2022 a FTX zerou exatamente quem fazia isso: a perda nao foi gradual nem marcada a mercado, foi total e instantanea, e nenhuma das duas pernas protegeu a outra — porque o risco nao estava no preco, estava no custodiante. Uma serie historica de precos nao contem esse evento por construcao; ele aparece como um zero, nao como um drawdown. Todos os numeros deste relatorio devem ser lidos como "antes do risco de perder tudo de uma vez".

Limitacoes adicionais registradas: (i) granularidade DIARIA na checagem de liquidacao — o numero de liquidacoes e um piso, nao um teto; (ii) o CDI e em reais e o carry em USDT, e o risco cambial foi ignorado nos dois sentidos; (iii) sem IR; (iv) profundidade de livro nao modelada — o slippage e fixo, e as cestas TOP10/TOP20 incluem pares onde R$100k ja movem preco.

