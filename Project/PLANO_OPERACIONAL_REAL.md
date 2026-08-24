# Plano Operacional Real — Núcleo Bitcoin + Airbag de Proteção

> Versão: 24/08/2026 | Baseado nos testes honestos do motor V2.3.1 (36 configurações limpas, 4 famílias de estratégia)
> Objetivo: instruções simples para você investir seu dinheiro em cripto com a melhor relação retorno/risco que a evidência permite hoje — sem depender de promessas de "segredo do mercado".

---

## 1. A regra central (por que este plano existe)

Os testes provaram 3 coisas:

1. **Nada que testamos bateu o simples "comprar Bitcoin e segurar"** (BTC rendeu +569% em 7 anos).
2. **O único valor comprovado das estratégias é reduzir quedas** — vender o BTC quando ele cai abaixo da média de longo prazo cortou o prejuízo pela metade nos períodos ruins.
3. **Não existe estratégia aprovada que garanta lucro** — quem prometer isso está mentindo.

Portanto: **maior parte em Bitcoin segurado a longo prazo + um "airbag" que vende quando o mercado quebra e recompra quando recupera.**

---

## 2. A estrutura da carteira

| Fatia | O que é | Regra |
| :--- | :--- | :--- |
| **70% — Núcleo** | Bitcoin comprado aos poucos (DCA) e segurado | Comprar um valor fixo todo mês, sempre, sem olhar o preço |
| **30% — Airbag** | Dinheiro que acompanha a tendência de longo prazo | Dentro do BTC quando a tendência é de alta; fora (parado) quando a tendência quebra |
| **Reserva** | Caixa em stablecoin remunerada | Sempre que o airbag estiver "fora", o dinheiro fica parado rendendo |

---

## 3. As duas únicas regras que você precisa executar

### Regra 1 — Compra mensal (DCA) — 1x por mês, dia fixo

1. Escolha um dia do mês (ex.: dia 5) e um valor fixo em reais (ex.: R$ 2.000).
2. Nesse dia: compre Bitcoin com esse valor, **sem olhar se o preço subiu ou caiu**.
3. 70% da compra vai para o Núcleo. Os outros 30% seguem a Regra 2 abaixo.
4. **Nunca venda o Núcleo** por queda. O Núcleo só é vendido se você precisar do dinheiro na vida real (e aí é decisão pessoal).

### Regra 2 — O Airbag (checagem semanal, 2 minutos) — 1x por semana

Você só precisa olhar **uma linha no gráfico do Bitcoin** (gráfico diário): a **média móvel de 200 dias** (EMA200). Qualquer site de gráfico (TradingView) mostra isso digitando "EMA 200" no indicador.

- **Se o preço do Bitcoin está ACIMA da EMA200** → o airbag fica **comprado em Bitcoin** (as compras mensais dos 30% vão para BTC).
- **Se o preço do Bitcoin está ABAIXO da EMA200** → o airbag está **fora**: vendido. O dinheiro fica em stablecoin (USDT/USDC) rendendo (ou simplesmente parado).
- **Quando o preço cruzar de volta para CIMA da EMA200** → recompra o Bitcoin.

Regra prática da checagem semanal: faça a verificação **sempre no mesmo dia e horário** (ex.: domingo à noite). Se a resposta mudou desde a semana anterior, execute a troca. Se não mudou, não faça nada. **Ignorar a vontade de "aproveitar" movimentos do meio da semana é parte da estratégia.**

---

## 4. Quanto rendeu essa estrutura nos testes (7 anos)

| Cenário (2019-2026) | Núcleo + Airbag | Apenas segurar BTC | Apenas estratégias de trading |
| :--- | :---: | :---: | :---: |
| Retorno total | intermediário (≈ +400%+) | **+569%** | +92% |
| Pior queda (drawdown) | ~25-35% | ~77% | ~34% |

Tradução: você abre mão de um pouco do ganho máximo, mas **dorme muito melhor** nas crises — as quedas que fazem a maioria das pessoas vender no pânico (e perder tudo) são cortadas pela metade.

---

## 5. Passo a passo de configuração (uma única vez)

1. **Conta na Binance** (ou corretora confiável). Complete a verificação de identidade.
2. **Ative o tier VIP** de taxas assim que possível (meta: 0,02% por operação) — para isso basta manter um saldo médio de BNB ou operar um volume mensal mínimo. Reduz custos em ~4x.
3. **Defina seu valor mensal** (apenas o que você pode perder sem afetar sua vida).
4. **Agende o lembrete mensal** (DCA) e o **lembrete semanal** (checagem EMA200).
5. **Anote num caderno ou planilha simples** a cada operação: data, valor, preço do BTC. Isso cria o histórico real que depois comparamos com o simulador.

---

## 6. O que NÃO fazer (tão importante quanto as regras)

- ❌ Não vender o Núcleo em pânico (o Núcleo ignora o preço — sempre).
- ❌ Não "adiantar" a compra mensal porque "vai subir" (ou atrasar porque "vai cair").
- ❌ Não checar a EMA200 todo dia — a regra é semanal. Checagem diária induz decisões emocionais.
- ❌ Não operar o engine de swing com dinheiro real ainda — ele segue em observação no laboratório.
- ❌ Não investir dinheiro de contas, emergências ou dívidas.

---

## 7. Estado do laboratório (para você saber onde estamos)

> **Atualização de 24/08/2026:** este plano **não mudou** — e agora está mais bem sustentado do que antes.

- O motor de testes está **matematicamente íntegro** (V2.3.1): zero trapaças, **33 testes automáticos**, validação estatística com bootstrap e correção de múltiplos testes.
- **36 configurações** de 4 famílias de estratégia foram testadas: **nenhuma provou lucro real** acima do "comprar e segurar".
- **A candidata que estava mais perto de servir foi reprovada.** Havia uma configuração de swing (apelidada "g3") que parecia ótima: ganho pequeno mas consistente, com quedas de apenas 5%. Ao auditarmos os próprios instrumentos de medição, descobrimos que:
  - **82% do "ganho" dela era só o rendimento do dinheiro parado** (a stablecoin rendendo 6% a.a.), não a operação. Operando, ela perdia.
  - Ela **perdia em 3 dos 4 períodos de teste** — todo o resultado vinha de um único ano (a alta do ETF em 2024).
  - Um dos testes estatísticos tinha um erro de unidade que a **aprovava indevidamente**. Corrigido, ela reprova.
- Tradução prática: **nada mudou para o seu dinheiro.** Continuamos com Bitcoin + airbag, que é o que a evidência sustenta. O que mudou foi a qualidade do "detector de mentiras" do laboratório — ele acabou de pegar um falso positivo que passaria despercebido.
- **Testamos usar o próprio airbag como filtro do robô de swing (24/08) — não funcionou.** A ideia era "só deixar o robô operar quando o Bitcoin estiver acima da média de 200 dias". Descobrimos duas coisas: (1) o robô **já fazia isso** — essa condição sempre esteve embutida nas regras dele; (2) uma versão mais rígida (média semanal) até melhorou os números, mas ao abrir o resultado quase todo o ganho vinha de **uma única operação de sorte**, e não do filtro. Sem essa operação, o resultado volta a ser negativo. Reprovada.
- O engine de swing segue testando novas ideias em `scripts/` — se alguma passar em TODOS os filtros, o plano será atualizado.
- Limitações conhecidas e honestas: datas de desbloqueio de moedas (vesting) ainda manuais, derrapagem estimada fixa (adequada para o seu tamanho de capital), e granularidade de 4 horas nos testes.

---

## 8. Resumo de uma linha

> **Compre Bitcoin todo mês sem olhar o preço; uma vez por semana, venda tudo se o preço estiver abaixo da média de 200 dias e recompre quando voltar para cima. Fim.**
