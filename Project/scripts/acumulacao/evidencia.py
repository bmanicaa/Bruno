"""
EVIDENCIA (Fase E, Etapa 4) — a mesma regua do Projeto A aplicada ao Projeto B.

O problema
----------
O Projeto A foi condenado com block bootstrap, correcao de multiplos testes e
Deflated Sharpe. O Projeto B foi ACEITO com "40 de 42 combinacoes vencem" e
"48 de 71 inicios batem o CDB".

Esses 42 e esses 71 nao sao observacoes independentes: sao janelas SOBREPOSTAS
de UMA unica serie de preco, que contem UM bear market grande (2022). O proprio
C7 do analises.md demonstra isso sem perceber — nas 4 janelas de queda o airbag
vence em 160/168; nas 6 de alta, perde em 164/168. O resultado agregado e funcao
de QUANTO BEAR o periodo contem, nao de habilidade preditiva.

Contar vitorias num grid correlacionado nao e evidencia; e o mesmo erro que a
Fase A passou uma auditoria inteira corrigindo do outro lado do projeto.

O que este modulo faz
---------------------
Block bootstrap ESTACIONARIO sobre os RETORNOS DIARIOS do ativo, com blocos
longos o bastante para preservar a autocorrelacao de ciclo, gerando caminhos de
preco alternativos que poderiam ter acontecido. Cada estrategia e re-executada
em cada caminho -> intervalo de confianca de verdade.

Isto NAO invalida o DCA. Muda o que se pode afirmar sobre ele.
"""
import math
import random
import statistics


def caminhos_bootstrap(precos, n_caminhos=200, bloco_dias=180, seed=42):
    """Gera caminhos de preco alternativos por block bootstrap dos log-retornos.

    bloco_dias=180 (~6 meses) preserva tendencias e regimes intra-bloco. Blocos
    curtos destruiriam a persistencia que E a caracteristica economica do ativo,
    e produziriam intervalos falsamente estreitos.
    """
    rnd = random.Random(seed)
    lr = [math.log(precos[i] / precos[i - 1]) for i in range(1, len(precos))]
    n = len(lr)
    n_blocos = (n + bloco_dias - 1) // bloco_dias
    saida = []
    for _ in range(n_caminhos):
        seq = []
        for _ in range(n_blocos):
            s = rnd.randrange(n)
            seq.extend(lr[(s + k) % n] for k in range(bloco_dias))
        seq = seq[:n]
        p = [precos[0]]
        for x in seq:
            p.append(p[-1] * math.exp(x))
        saida.append(p)
    return saida


def intervalo(valores, conf=0.95):
    v = sorted(valores)
    if not v:
        return (float('nan'),) * 3
    lo = v[int((1 - conf) / 2 * len(v))]
    hi = v[min(len(v) - 1, int((1 + conf) / 2 * len(v)))]
    return lo, statistics.median(v), hi


def p_supera(valores_a, valores_b):
    """P(estrategia A > estrategia B) nos mesmos caminhos — pareado."""
    if not valores_a:
        return float('nan')
    return sum(1 for a, b in zip(valores_a, valores_b) if a > b) / len(valores_a)
