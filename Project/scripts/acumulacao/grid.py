"""
Executor do GRID OBRIGATORIO (protocolo analises.md 3.1, criterio 1).

Um numero isolado e motivo de rejeicao do RELATORIO, nao da estrategia: a
leitura inicial errada do airbag (achado C10) veio de variar um eixo so, com um
valor de media que era, por acaso, o pior do conjunto.

Reporta sempre: pior caso, mediana, melhor caso e taxa de vitoria.
"""
import itertools
import statistics

from .motor import simular
from .politicas import Airbag

MEDIAS_PADRAO = ['EMA100', 'EMA150', 'EMA200', 'EMA250', 'EMA300', 'SMA200']
DIAS_PADRAO = list(range(7))


def grid_airbag(datas, precos, medias=None, dias=None, atrasos=(0,), fatias=(1.0,), **kw):
    medias = medias or MEDIAS_PADRAO
    dias = dias if dias is not None else DIAS_PADRAO
    linhas = []
    for m, wd, at, fa in itertools.product(medias, dias, atrasos, fatias):
        r = simular(datas, precos, Airbag(m, wd, at, fa), **kw)
        linhas.append({'media': m, 'dia': wd, 'atraso': at, 'fatia': fa,
                       'valor_final': r['valor_final'], 'maxdd': r['maxdd'],
                       'operacoes': r['operacoes'],
                       'exposicao_media': r['exposicao_media'],
                       'tempo_submerso_frac': r['tempo_submerso_frac']})
    return linhas


def resumir(linhas, baseline, campo='valor_final'):
    """Pior caso, mediana, melhor caso e taxa de vitoria — nunca um numero so."""
    v = sorted(l[campo] for l in linhas)
    vit = sum(1 for x in v if x > baseline)
    return {
        'n': len(v),
        'pior': v[0],
        'mediana': statistics.median(v),
        'melhor': v[-1],
        'baseline': baseline,
        'vitorias': vit,
        'taxa_vitoria': vit / len(v) if v else 0.0,
        'vantagem_mediana_pct': (statistics.median(v) / baseline - 1) * 100 if baseline else 0.0,
    }
