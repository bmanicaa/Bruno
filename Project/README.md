# Sistema Quantitativo de Criptoativos — Índice do Projeto

> **Este arquivo é um mapa, não um relatório.** Ele não repete números: cada fato medido vive em
> **um** lugar só, e este documento diz qual. Se você encontrar um número aqui, é bug.

---

## Qual arquivo ler, para quê

| você quer... | leia |
| :--- | :--- |
| **investir seu dinheiro** | [`PLANO_OPERACIONAL_REAL.md`](PLANO_OPERACIONAL_REAL.md) — o passo a passo, em linguagem simples |
| **saber o que fazer a seguir** | [`Plan.md`](Plan.md) — só trabalho pendente; se estiver vazio, não há |
| **conferir qualquer número** | [`analises.md`](analises.md) — **fonte única de todos os fatos medidos** |
| **entender o motor de swing** | [`Prompt.md`](Prompt.md) — manual do Projeto A (**congelado**) |

**Entrando agora numa sessão nova?** Leia `analises.md` seções 1 a 3, depois `Plan.md`. Nada mais.

---

## Estado em uma tela

- **Projeto A — motor de swing: CONGELADO.** Não por refutação. O protocolo de aceite não tem poder
  estatístico para aprovar nada realista, e o lucro **bruto** da melhor configuração é praticamente
  zero. Testar mais configurações piora a régua sem produzir resposta. *(Fase E)*
- **Projeto B — acumulação: MEDIDO E CONCLUÍDO.** Reproduzido no repositório, com testes. A
  recomendação de dinheiro real é **DCA puro em Bitcoin, sem airbag e sem alavancagem**.
- **Pendente:** três perguntas em `Plan.md` — qual ativo, câmbio BRL/USD, aporte único vs. mensal.

---

## Estrutura

```
Project/
├── PLANO_OPERACIONAL_REAL.md   # dinheiro real
├── Plan.md                     # trabalho pendente
├── analises.md                 # fonte única dos fatos medidos
├── Prompt.md                   # manual do Projeto A (congelado)
├── data/
│   ├── raw/                    # dados brutos imutáveis (2019-09 → hoje, Binance, 550 moedas)
│   ├── experimentos/           # PROJETO A — registro histórico, não escrever
│   └── acumulacao/             # PROJETO B + Fase E — artefatos
├── reports/                    # relatórios executivos por modalidade
├── scripts/
│   ├── backtest_institucional.py   # ⛔ PROJETO A — CONGELADO
│   ├── backtest_cs_momentum.py     # ⛔ CONGELADO
│   ├── backtest_trend_bh.py        # ⛔ CONGELADO
│   ├── batch_experiments.py        # ⛔ CONGELADO
│   ├── meta_label.py               # ⛔ CONGELADO
│   ├── reprocess_experiments.py    # ⛔ CONGELADO
│   ├── statistical_validation.py   # compartilhado — importar, nunca editar
│   ├── verify_replay.py            # prova que uma mudança é NULA (igualdade trade a trade)
│   ├── poder_do_teste.py           # Fase E — a régua consegue aprovar algo?
│   ├── sinal_nulo.py               # Fase E — o que entradas aleatórias fazem neste motor
│   ├── criterio_de_decisao.py      # Fase E — "vale apostar?" separado de "existe efeito?"
│   ├── acumulacao/                 # PROJETO B — pacote do laboratório de acumulação
│   └── legado/                     # arquivado, não usar
└── tests/
    ├── test_engine.py          # ⛔ PROJETO A — NÃO TOCAR
    ├── test_poder.py           # Fase E
    └── test_acumulacao.py      # Projeto B
```

> **⛔ Regra de congelamento.** Os arquivos marcados sustentam a reprodutibilidade bit-a-bit de 36
> experimentos registrados. Um refactor pode quebrá-la **sem quebrar nenhum teste**. Não modifique —
> se achar que precisa, pare e pergunte. Detalhes e a única condição para reabrir: `analises.md`.

---

## Como rodar

```bash
# Projeto B — acumulação (a frente viva)
python -m scripts.acumulacao.cli --tudo          # reprodução + timing + evidência + alocação

# Fase E — auditoria da régua
python scripts/poder_do_teste.py --varrer-amostra
python scripts/sinal_nulo.py --rodadas 300 --incluir-bull
python scripts/criterio_de_decisao.py --todas

# Projeto A — congelado, só para reproduzir o histórico
python scripts/backtest_institucional.py --mode all
python scripts/backtest_institucional.py --walkforward

# Sempre antes de confirmar qualquer mudança
pytest tests/
```

Ambiente: Python 3.11, pandas 3.0.5, numpy 2.4.6, pytest.

---

## As três regras de trabalho que não se negociam

1. **Todo fato medido entra no `analises.md`**, no formato da seção 5, com o hash da configuração.
   Número que não está lá não existe.
2. **Toda mudança que se propõe nula** (refatoração, performance) passa por `verify_replay.py`, em ao
   menos uma configuração por ramo de código tocado.
3. **Nenhuma recomendação de dinheiro real sem lastro** em `analises.md` ou em artefato de
   `data/acumulacao/`.
