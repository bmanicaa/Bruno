"""
Executor do GRID. Um numero isolado e motivo de rejeicao do RELATORIO.

Eixos obrigatorios (5 x 10 x 3 x 5 = 750 configuracoes):
  cesta        BTC | BTC+ETH | TOP5 | TOP10 | TOP20   (top-N point-in-time)
  gatilho      sempre | funding medio de K dias > limiar, K em {1,3,7},
               limiar em {0, 0.005%, 0.01%}
  alavancagem  1x | 2x | 3x
  rebalanceio  diario | semanal | por desvio de 2% | 5% | 10%

O caro aqui e o universo point-in-time e a carga das series; ambos sao
calculados UMA vez e compartilhados por todas as configuracoes. Isso tambem
garante que duas configs que so diferem na alavancagem vejam exatamente o
mesmo universo — se cada uma recalculasse o seu, uma diferenca de ranking
poderia ser confundida com efeito de alavancagem.
"""
import itertools
import statistics

from . import custos as C
from . import dados as D
from . import motor as M

CESTAS = ['BTC', 'BTC_ETH', 'TOP5', 'TOP10', 'TOP20']
GATILHOS = ([('sempre',)] +
            [('funding', k, lim) for k in (1, 3, 7)
             for lim in (0.0, 0.00005, 0.0001)])
ALAVANCAGENS = [1, 2, 3]
REBALANCEIOS = [('diario',), ('semanal',),
                ('limiar', 0.02), ('limiar', 0.05), ('limiar', 0.10)]


class Contexto:
    """Universos e series pre-carregados, compartilhados por todo o grid."""

    def __init__(self, inicio, fim, base_modo='premium', cestas=None):
        self.base_modo = base_modo
        base_fn = (lambda f: C.base_por_dia(f, base_modo))
        btc = D.serie_por_dia('BTCUSDT', base_fn)
        self.calendario = sorted(d for d in btc if inicio <= d <= fim)
        self.universos = {}
        precisa = {'BTCUSDT', 'ETHUSDT'}
        candidatos = D.simbolos_disponiveis()
        for cesta in (cestas or CESTAS):
            if cesta in ('BTC', 'BTC_ETH'):
                continue
            n = M.CESTAS[cesta]
            u = M.universo_pit(candidatos, self.calendario, n)
            self.universos[cesta] = u
            precisa |= {s for v in u.values() for s in v}
        self.series = {s: D.serie_por_dia(s, base_fn) for s in sorted(precisa)}

    def rodar(self, cfg):
        return M.simular(cfg, series=self.series, calendario=self.calendario,
                         universo=self.universos.get(cfg['cesta']),
                         guardar_curva=True)


def configs(cestas=None, gatilhos=None, alavancagens=None, rebalanceios=None,
            **fixos):
    for cesta, gat, L, reb in itertools.product(
            cestas or CESTAS, gatilhos or GATILHOS,
            alavancagens or ALAVANCAGENS, rebalanceios or REBALANCEIOS):
        yield M.config_padrao(cesta=cesta, gatilho=gat, alavancagem=L,
                              rebalanceio=reb, **fixos)


def executar(ctx, lista_configs, progresso=None):
    linhas = []
    for i, cfg in enumerate(lista_configs):
        r = ctx.rodar(cfg)
        linhas.append({
            'hash': r['hash'],
            'cesta': cfg['cesta'],
            'gatilho': '/'.join(str(x) for x in cfg['gatilho']),
            'alavancagem': cfg['alavancagem'],
            'rebalanceio': '/'.join(str(x) for x in cfg['rebalanceio']),
            'patrimonio_final': r['patrimonio_final'],
            'cagr': r['cagr'],
            'a_funding': r['a_funding'],
            'b_base': r['b_base'],
            'c_custos': r['c_custos'],
            'd_juros': r['d_juros'],
            'f_quebra_hedge': r['f_quebra_hedge'],
            'e_residuo': r['e_residuo'],
            'custo_oportunidade_margem': r['custo_oportunidade_margem'],
            'capital_imobilizado_medio': r['capital_imobilizado_medio'],
            'n_liquidacoes': r['n_liquidacoes'],
            'n_aportes_margem': r['n_aportes_margem'],
            'n_desmontes_forcados': r['n_desmontes_forcados'],
            'n_rebalanceios': r['n_rebalanceios'],
            'exposicao_media': r['exposicao_media'],
            'dias_com_posicao': r['dias_com_posicao'],
            'curva': r['curva'],
        })
        if progresso and (i + 1) % progresso == 0:
            print(f'  ... {i + 1} configuracoes')
    return linhas


def resumir(linhas, baseline, campo='patrimonio_final'):
    """Pior caso, mediana, melhor caso e taxa de vitoria. Nunca um numero so."""
    v = sorted(l[campo] for l in linhas)
    if not v:
        return {}
    vit = sum(1 for x in v if x > baseline)
    return {
        'n': len(v),
        'pior': v[0],
        'p25': v[len(v) // 4],
        'mediana': statistics.median(v),
        'p75': v[(3 * len(v)) // 4],
        'melhor': v[-1],
        'baseline': baseline,
        'vitorias': vit,
        'taxa_vitoria': vit / len(v),
    }


def por_eixo(linhas, eixo, baseline, campo='patrimonio_final'):
    """Resumo separado por valor de um eixo — mostra QUAL escolha move o
    resultado, em vez de dar so a distribuicao agregada."""
    grupos = {}
    for l in linhas:
        grupos.setdefault(l[eixo], []).append(l)
    return {k: resumir(v, baseline, campo) for k, v in sorted(grupos.items(),
                                                             key=lambda kv: str(kv[0]))}
