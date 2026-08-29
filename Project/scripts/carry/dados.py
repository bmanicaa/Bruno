"""
Carga das series brutas para o motor de carry.

Duas fontes por simbolo, ambas em data/raw/:
  * funding_rates.csv  -> settlements (8h na maioria, 4h em 384 dos 542 pares)
  * klines_1d.csv      -> preco diario do PERPETUO e volume para o ranking

FATO ESTRUTURAL DA BASE DE DADOS (verificado, nao suposto): as klines vieram de
`fapi.binance.com` (ver scripts/download_raw_market_data.py linha 67). Sao velas
do PERPETUO, nao do spot. O repositorio NAO tem serie de spot. Por isso a perna
comprada e precificada como F/(1+b), com `b` (a base) estimado a partir da
propria formula de funding da Binance — ver `custos.premium_index`. Fingir que
spot == perp seria assumir base zero em silencio; aqui isso e um parametro
explicito e varrido no grid.

Tudo aqui e leitura pura e cacheada por processo: mesma entrada -> mesma saida.
"""
import bisect
import csv
import datetime as dt
import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(BASE_DIR, 'data', 'raw')
COINS = os.path.join(RAW, 'coins')
MACRO = os.path.join(RAW, 'macro')

MS_DIA = 86_400_000
MS_HORA = 3_600_000

_cache_funding = {}
_cache_diario = {}
_cache_4h = {}
_meta_serie = {}
_cache_eixos = {}


def _caminho_funding(simbolo):
    for c in (os.path.join(MACRO, f'{simbolo}_funding_rates.csv'),
              os.path.join(COINS, simbolo, 'funding_rates.csv')):
        if os.path.exists(c):
            return c
    raise FileNotFoundError(f'funding de {simbolo} nao encontrado')


def _caminho_4h(simbolo):
    for c in (os.path.join(MACRO, f'{simbolo}_4h.csv'),
              os.path.join(COINS, simbolo, 'klines_4h.csv')):
        if os.path.exists(c):
            return c
    return None


def carregar_4h(simbolo):
    """dict close_time_arredondado_para_hora -> fechamento da vela de 4h.

    Serve so para um proposito: o preco NO INSTANTE do settlement. O funding
    incide sobre o notional naquele instante; usar o fechamento do dia inteiro
    embutiria ate 24h de deriva de preco no notional.
    """
    if simbolo in _cache_4h:
        return _cache_4h[simbolo]
    caminho = _caminho_4h(simbolo)
    saida = {}
    if caminho:
        with open(caminho, 'r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                try:
                    c = float(r['close'])
                    if c <= 0:
                        continue
                    # close_time e 23:59:59.999; a vela FECHA na hora cheia
                    # seguinte, que e onde o settlement acontece.
                    saida[round(int(r['close_time']) / MS_HORA) * MS_HORA] = c
                except (ValueError, KeyError, TypeError):
                    continue
    _cache_4h[simbolo] = saida
    return saida


def _caminho_diario(simbolo):
    for c in (os.path.join(MACRO, f'{simbolo}_1d.csv'),
              os.path.join(COINS, simbolo, 'klines_1d.csv')):
        if os.path.exists(c):
            return c
    raise FileNotFoundError(f'klines diarias de {simbolo} nao encontradas')


def simbolos_disponiveis():
    """Todo simbolo com as duas series presentes. Inclui delistados de proposito."""
    saida = []
    for s in sorted(os.listdir(COINS)):
        d = os.path.join(COINS, s)
        if (os.path.isdir(d) and os.path.exists(os.path.join(d, 'funding_rates.csv'))
                and os.path.exists(os.path.join(d, 'klines_1d.csv'))):
            saida.append(s)
    return saida


def carregar_funding(simbolo):
    """[(timestamp_ms, taxa)] ordenado. O timestamp e o instante do settlement."""
    if simbolo in _cache_funding:
        return _cache_funding[simbolo]
    linhas = []
    with open(_caminho_funding(simbolo), 'r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                linhas.append((int(r['fundingTime']), float(r['fundingRate'])))
            except (ValueError, KeyError, TypeError):
                continue
    linhas.sort()
    # Duplicatas existem em algumas series (paginacao sobreposta na coleta).
    unicas, visto = [], set()
    for t, taxa in linhas:
        # O timestamp vem com jitter de ate 47ms (ex.: 2021-01-20 00:00:00.012).
        # Sem encaixar na hora cheia, o settlement das 00:00 cai no dia errado e
        # o BTC passa a exibir 4 settlements num dia e 2 no seguinte.
        t = round(t / MS_HORA) * MS_HORA
        if t not in visto:
            visto.add(t)
            unicas.append((t, taxa))
    _cache_funding[simbolo] = unicas
    return unicas


def intervalo_funding_h(simbolo):
    """Intervalo modal entre settlements, em horas.

    Obrigatorio detectar por simbolo: 384 dos 542 pares liquidam a cada 4h e
    154 a cada 8h. Assumir 8h para todos inflaria o carry dos alts em 2x.
    """
    t = [x[0] for x in carregar_funding(simbolo)]
    if len(t) < 3:
        return 8
    g = Counter(round((t[i + 1] - t[i]) / 3_600_000) for i in range(len(t) - 1))
    return max(1, g.most_common(1)[0][0])


def carregar_diario(simbolo):
    """[(data, open, high, low, close, quote_volume)] ordenado por data."""
    if simbolo in _cache_diario:
        return _cache_diario[simbolo]
    linhas = []
    with open(_caminho_diario(simbolo), 'r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                d = dt.date.fromisoformat(r['open_time_dt'][:10])
                c = float(r['close'])
                if c <= 0:
                    continue
                linhas.append((d, float(r['open']), float(r['high']),
                               float(r['low']), c, float(r['quote_volume'] or 0.0)))
            except (ValueError, KeyError, TypeError):
                continue
    linhas.sort(key=lambda x: x[0])
    _cache_diario[simbolo] = linhas
    return linhas


def _ms_da_data(d):
    return int(dt.datetime(d.year, d.month, d.day,
                           tzinfo=dt.timezone.utc).timestamp() * 1000)


def serie_por_dia(simbolo, base_fn):
    """Agrega funding e preco por DIA UTC, no formato que o motor consome.

    Devolve dict data -> {
        'close', 'high', 'low', 'qv',        # da vela diaria do perpetuo
        'fator', 'soma_taxa', 'n_settle',    # funding do dia
        'base',                              # base (perp/spot - 1) no fim do dia
    }

    `fator` e a chave de desempenho e de correcao ao mesmo tempo. O caixa de
    funding do dia e:

        caixa += notional_no_inicio_do_dia * fator

    porque o funding de cada settlement incide sobre o notional NAQUELE
    instante, nao sobre o do inicio do dia:

        q * P_i * taxa_i = (q * P_ref) * taxa_i * (P_i / P_ref)

    Logo `fator = sum(taxa_i * P_i / P_ref)`, com P_ref = fechamento do dia
    ANTERIOR (o preco vigente quando a posicao do dia foi dimensionada). Sem o
    termo P_i/P_ref o funding fica errado exatamente na direcao que favorece a
    estrategia num mercado em alta — o vies que o achado "notional short" da
    V2.3 ja tinha custado uma vez a este repositorio.

    JANELA DO DIA: (D 00:00, D+1 00:00]. O settlement das 00:00 de D pertence ao
    dia D-1. Isso mantem a decisao do dia D — tomada com a informacao disponivel
    aas 00:00 de D — estritamente anterior a todo fluxo que ela remunera.
    """
    diario = carregar_diario(simbolo)
    if not diario:
        return {}
    fund = carregar_funding(simbolo)

    # preco de referencia por dia = fechamento do dia anterior
    fechamento = {r[0]: r[4] for r in diario}
    datas = [r[0] for r in diario]
    ref = {}
    for i, d in enumerate(datas):
        ref[d] = fechamento[datas[i - 1]] if i > 0 else fechamento[d]

    # Preco NO INSTANTE do settlement, vindo da vela de 4h que fecha ali.
    # Quando falta a vela (buraco na serie), cai para o fechamento do dia.
    velas4h = carregar_4h(simbolo)
    acum = {}
    faltantes = 0
    for t, taxa in fund:
        # (D 00:00, D+1 00:00] -> um settlement exatamente as 00:00 cai em D-1
        d = dt.datetime.fromtimestamp((t - 1) / 1000, tz=dt.timezone.utc).date()
        if d not in fechamento:
            continue
        p_ref = ref[d]
        if p_ref <= 0:
            continue
        p_settle = velas4h.get(t)
        if p_settle is None:
            p_settle = fechamento[d]
            faltantes += 1
        a = acum.setdefault(d, [0.0, 0.0, 0])
        a[0] += taxa * (p_settle / p_ref)
        a[1] += taxa
        a[2] += 1

    base_por_dia = base_fn(fund) if base_fn is not None else {}

    saida = {}
    for d, o, h, lo, c, qv in diario:
        a = acum.get(d, (0.0, 0.0, 0))
        saida[d] = {'close': c, 'high': h, 'low': lo, 'qv': qv,
                    'fator': a[0], 'soma_taxa': a[1], 'n_settle': a[2],
                    'base': base_por_dia.get(d, 0.0)}
    _meta_serie[simbolo] = {'settle_sem_vela_4h': faltantes,
                            'settle_total': len(fund),
                            'dias': len(saida)}
    return saida


def meta_serie(simbolo):
    """Diagnostico de cobertura da ultima carga: quantos settlements ficaram sem
    vela de 4h e tiveram de usar o fechamento diario como preco de notional."""
    return dict(_meta_serie.get(simbolo, {}))


def _eixos(simbolo):
    """(datas, volumes) alinhados, para busca binaria no ranking de liquidez."""
    if simbolo in _cache_eixos:
        return _cache_eixos[simbolo]
    diario = carregar_diario(simbolo)
    par = ([r[0] for r in diario], [r[5] for r in diario])
    _cache_eixos[simbolo] = par
    return par


def liquidez_mediana(simbolo, ate, janela=30):
    """Volume em USDT mediano dos `janela` dias ESTRITAMENTE anteriores a `ate`.

    Point-in-time por construcao: o corte `< ate` e o que impede o ranking de
    liquidez de enxergar o proprio dia que vai negociar. O grid chama isto
    dezenas de milhares de vezes, dai a busca binaria em vez de varrer a serie.
    """
    datas, vols = _eixos(simbolo)
    j = bisect.bisect_left(datas, ate)
    if j < janela:
        return 0.0
    bloco = sorted(vols[j - janela:j])
    n = len(bloco)
    return bloco[n // 2] if n % 2 else 0.5 * (bloco[n // 2 - 1] + bloco[n // 2])


def limpar_cache():
    _cache_funding.clear()
    _cache_diario.clear()
    _cache_4h.clear()
    _meta_serie.clear()
    _cache_eixos.clear()
