"""
Os tres pontos de comparacao, no MESMO periodo e com os MESMOS custos.

Sem eles um CAGR de 6% parece bom. Contra o CDI de 1% a.m. (12,67% a.a.) ele
e metade do que o dinheiro renderia parado. Comparar retorno de estrategia com
zero — e nao com a alternativa obvia — foi o erro mais caro deste repositorio
(achado C5: "~90% da vantagem do airbag era CDI, nao market timing").

ATENCAO A MOEDA: o carry e o BTC sao denominados em USDT; o CDI e em reais.
Comparar os dois ignora o risco cambial BRL/USD, nos dois sentidos. O projeto
ja faz essa simplificacao no Projeto B; ela e mantida aqui por coerencia e
esta registrada como limitacao, nao como resultado.
"""
import datetime as dt

from . import custos as C
from . import dados as D


def _curva_metrica(curva, capital, inicio, fim):
    anos = (fim - inicio).days / 365.25
    final = curva[-1][1] if curva else capital
    pico, maxdd = -1e30, 0.0
    for _, v in curva:
        pico = max(pico, v)
        if pico > 0:
            maxdd = max(maxdd, 1.0 - v / pico)
    return {
        'patrimonio_final': final,
        'capital_inicial': capital,
        'retorno_total': final / capital - 1.0,
        'cagr': (final / capital) ** (1 / anos) - 1 if anos > 0 else 0.0,
        'maxdd': maxdd,
        'anos': anos,
        'curva': curva,
    }


def cdi(inicio, fim, capital=100_000.0, mensal=0.01, calendario=None):
    """Caixa remunerado a 1% a.m., composto ao dia. A regua do projeto."""
    j = C.juro_diario(mensal)
    datas = calendario or [inicio + dt.timedelta(days=i)
                           for i in range((fim - inicio).days + 1)]
    datas = [d for d in datas if inicio <= d <= fim]
    v, curva = capital, []
    for d in datas:
        v *= (1 + j)
        curva.append((d, v))
    return _curva_metrica(curva, capital, datas[0], datas[-1])


def _serie_btc(inicio, fim):
    diario = D.carregar_diario('BTCUSDT')
    return [(d, c) for d, _o, _h, _l, c, _q in diario if inicio <= d <= fim]


def comprar_e_segurar(inicio, fim, capital=100_000.0,
                      taxa=C.TAXA_PADRAO, slippage=C.SLIPPAGE_PADRAO):
    """Compra tudo no primeiro dia e nao mexe mais. Sem IR (bruto)."""
    serie = _serie_btc(inicio, fim)
    if not serie:
        raise ValueError('janela sem dados de BTC')
    p0 = serie[0][1]
    unidades = capital * (1 - taxa - slippage) / p0
    curva = [(d, unidades * p) for d, p in serie]
    return _curva_metrica(curva, capital, serie[0][0], serie[-1][0])


def dca(inicio, fim, capital=100_000.0, meses=12, dia=5,
        taxa=C.TAXA_PADRAO, slippage=C.SLIPPAGE_PADRAO, juro_mensal=0.01):
    """DCA: divide o capital em `meses` parcelas iguais; o que ainda nao foi
    aplicado rende CDI.

    E a comparacao justa contra o carry: mesmo capital, mesma data de largada,
    mesmo periodo. Um DCA com aportes NOVOS ao longo do tempo teria mais
    dinheiro trabalhando e nao seria comparavel.
    """
    serie = _serie_btc(inicio, fim)
    if not serie:
        raise ValueError('janela sem dados de BTC')
    j = C.juro_diario(juro_mensal)
    parcela = capital / meses
    caixa, unidades, curva, feitos = capital, 0.0, [], 0
    ultimo_mes = None
    for d, p in serie:
        caixa *= (1 + j)
        mes = (d.year, d.month)
        if feitos < meses and d.day >= dia and mes != ultimo_mes:
            gasto = min(parcela, caixa)
            unidades += gasto * (1 - taxa - slippage) / p
            caixa -= gasto
            feitos += 1
            ultimo_mes = mes
        curva.append((d, caixa + unidades * p))
    r = _curva_metrica(curva, capital, serie[0][0], serie[-1][0])
    r['parcelas'] = feitos
    return r
