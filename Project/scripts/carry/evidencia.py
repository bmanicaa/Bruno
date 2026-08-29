"""
Bootstrap em blocos, poder do teste e corte por regime.

REUSA o reamostrador canonico do projeto (`statistical_validation._resample_series`,
importado e nunca editado). Usar o mesmo bootstrap do Projeto A e o que permite
comparar os dois veredictos na mesma escala.

TRES CUIDADOS QUE ESTE MODULO EXISTE PARA IMPOR
1. Contar vitorias num grid correlacionado NAO e evidencia — 750 configuracoes
   sobre a mesma serie de funding sao 750 vistas do mesmo evento. A varredura
   do comprimento do bloco e das sementes existe para mostrar quanto do
   resultado e serie e quanto e escolha de reamostrador.
2. "Nao significativo" sem poder e mudo. A Fase E provou isso no Projeto A: a
   regua tinha poder ZERO abaixo de Sharpe 1,2 e o projeto leu "nada funciona".
   Todo veredito aqui sai acompanhado do efeito minimo detectavel.
3. O bootstrap em blocos EMBARALHA O TEMPO. Ele responde "e se estes 7 anos
   viessem em outra ordem", nao "e o ano que vem". Quando a serie tem
   tendencia — e a do funding tem, forte e para baixo — o intervalo devolvido
   e otimista em relacao ao futuro. Esta limitacao e reportada junto do numero,
   nao em nota de rodape.
"""
import math
import os
import statistics
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import statistical_validation as sv  # noqa: E402  (reusado, nunca editado)

from . import dados as D             # noqa: E402

DIAS_ANO = 365.25
BLOCOS_PADRAO = (90, 180, 365, 730)
SEMENTES_PADRAO = (42, 7, 2026)


def retornos_diarios(curva):
    """Retornos simples dia a dia a partir da curva de patrimonio."""
    v = [x[1] for x in curva]
    return [v[i] / v[i - 1] - 1.0 for i in range(1, len(v)) if v[i - 1] > 0]


def cagr_de(retornos):
    if not retornos:
        return 0.0
    log = sum(math.log1p(r) for r in retornos)
    return math.exp(log * DIAS_ANO / len(retornos)) - 1.0


def bootstrap_blocos(retornos, alvo_cagr, blocos=BLOCOS_PADRAO,
                     sementes=SEMENTES_PADRAO, n_iter=2000):
    """Varredura completa: cada (bloco, semente) devolve sua propria conclusao.

    `alvo_cagr` e a barra a superar (o CDI). Devolve uma linha por combinacao
    e o agregado — a dispersao ENTRE linhas e o diagnostico de quanto o
    veredito depende do reamostrador e nao dos dados.
    """
    x = np.asarray(retornos, dtype=float)
    linhas = []
    for bloco in blocos:
        if bloco >= len(x):
            continue
        for semente in sementes:
            rng = np.random.default_rng(semente)
            amostras = sv._resample_series(rng, x, n_iter, bloco)
            log = np.log1p(np.clip(amostras, -0.999999, None)).sum(axis=1)
            cagrs = np.exp(log * DIAS_ANO / x.shape[0]) - 1.0
            linhas.append({
                'bloco': bloco, 'semente': semente,
                'cagr_mediano': float(np.median(cagrs)),
                'ic95_baixo': float(np.percentile(cagrs, 2.5)),
                'ic95_alto': float(np.percentile(cagrs, 97.5)),
                'p_supera_alvo': float((cagrs > alvo_cagr).mean()),
                'p_positivo': float((cagrs > 0).mean()),
            })
    agregado = {}
    if linhas:
        for campo in ('cagr_mediano', 'ic95_baixo', 'ic95_alto',
                      'p_supera_alvo', 'p_positivo'):
            v = [l[campo] for l in linhas]
            agregado[campo] = {'min': min(v), 'mediana': statistics.median(v),
                               'max': max(v)}
    return {'linhas': linhas, 'agregado': agregado, 'alvo_cagr': alvo_cagr,
            'n_obs': len(x)}


# --------------------------------------------------------------------------
# Poder
# --------------------------------------------------------------------------

def amostra_efetiva(retornos, max_lag=250):
    """Tamanho de amostra EFETIVO, corrigido pela autocorrelacao.

        n_ef = n / (1 + 2 * soma_k rho_k)

    (Newey-West/Bartlett, somando ate a primeira autocorrelacao negativa.)

    Por que isto nao e detalhe: a serie de retornos do carry tem rho(1) = 0,61
    e ainda 0,38 no lag 10 — o funding e persistente por construcao, ele nao
    sorteia um valor novo a cada dia. Com 2.538 dias, a amostra efetiva e de
    ~74 observacoes. Qualquer formula de poder que suponha independencia
    superestima o que se enxerga em quase 6 vezes.
    """
    x = np.asarray(retornos, dtype=float)
    x = x - x.mean()
    n = len(x)
    den = float((x * x).sum())
    if den <= 0 or n < 10:
        return {'n': n, 'n_efetivo': float(n), 'soma_rho': 0.0, 'rho1': 0.0}
    soma = 0.0
    rho1 = 0.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rho = float((x[:-k] * x[k:]).sum() / den)
        if k == 1:
            rho1 = rho
        if rho < 0:
            break
        soma += rho * (1 - k / n)
    return {'n': n, 'n_efetivo': n / (1 + 2 * soma), 'soma_rho': soma,
            'rho1': rho1}


def poder_analitico(n_dias, alpha=0.05, poder=0.80):
    """Menor Sharpe ANUALIZADO detectavel com n_dias de amostra.

    SE(Sharpe diario) ~ 1/sqrt(n) sob H0. Para rejeitar a um nivel alpha
    bilateral com poder (1-beta):

        SR_diario_min = (z_{1-alpha/2} + z_{poder}) / sqrt(n)
        SR_anual_min  = SR_diario_min * sqrt(365,25) = (z1+z2)/sqrt(anos)

    Note que o resultado depende SO do numero de anos. Por isso a resposta
    "quanto eu enxergo" e a mesma para qualquer estrategia com este historico —
    o que muda de estrategia para estrategia e quanto RETORNO aquele Sharpe
    representa, e isso depende da volatilidade dela (ver `efeito_detectavel`).
    """
    z1 = sv._norm_ppf(1 - alpha / 2)
    z2 = sv._norm_ppf(poder)
    anos = n_dias / DIAS_ANO
    return {'anos': anos, 'sharpe_anual_minimo': (z1 + z2) / math.sqrt(anos)}


def efeito_detectavel(retornos, alpha=0.05, poder=0.80):
    """Traduz o Sharpe minimo detectavel em RETORNO ANUAL, com a vol observada.

    E a pergunta util: "com esta amostra, que vantagem sobre o CDI eu
    conseguiria enxergar?". Numa estrategia delta-neutra a vol e baixa, entao
    um Sharpe alto vale poucos pontos percentuais — o oposto do que acontecia
    no motor direcional do Projeto A.
    """
    x = np.asarray(retornos, dtype=float)
    vol_anual = float(np.std(x, ddof=1) * math.sqrt(DIAS_ANO))
    p = poder_analitico(len(x), alpha, poder)
    ef = amostra_efetiva(retornos)
    p_cor = poder_analitico(ef['n_efetivo'], alpha, poder)
    return {
        'n_dias': len(x),
        'anos': p['anos'],
        'vol_anual': vol_anual,
        'rho1': ef['rho1'],
        'n_efetivo': ef['n_efetivo'],
        # versao ingenua (supoe independencia) — reportada so para mostrar o
        # tamanho do erro que ela induz nesta serie
        'sharpe_anual_minimo_iid': p['sharpe_anual_minimo'],
        'retorno_anual_minimo_iid': p['sharpe_anual_minimo'] * vol_anual,
        # versao corrigida pela autocorrelacao
        'sharpe_anual_minimo': p_cor['sharpe_anual_minimo'],
        'retorno_anual_minimo_detectavel': p_cor['sharpe_anual_minimo'] * vol_anual,
    }


def poder_simulado(retornos, alvo_cagr, efeitos, n_rodadas=300, bloco=180,
                   n_iter=400, semente=11, criterio=0.90):
    """Poder EMPIRICO: injeta um excesso conhecido e mede a taxa de aprovacao.

    Mesmo desenho de `scripts/poder_do_teste.py`: gera mundos com edge
    VERDADEIRO conhecido e submete cada um ao mesmo gate usado no veredito
    (P(CAGR > CDI) >= `criterio` no bootstrap em blocos). A taxa de aprovacao
    e o poder.
    """
    x = np.asarray(retornos, dtype=float)
    n = len(x)
    rng = np.random.default_rng(semente)
    saida = []
    for efeito in efeitos:
        # excesso anual `efeito` distribuido em retorno diario
        deslocamento = (1 + efeito) ** (1 / DIAS_ANO) - 1
        aprovadas = 0
        for _ in range(n_rodadas):
            mundo = sv._resample_series(rng, x, 1, bloco)[0] + deslocamento
            r2 = np.random.default_rng(int(rng.integers(1, 2 ** 31)))
            am = sv._resample_series(r2, mundo, n_iter, bloco)
            log = np.log1p(np.clip(am, -0.999999, None)).sum(axis=1)
            cagrs = np.exp(log * DIAS_ANO / n) - 1.0
            if (cagrs > alvo_cagr).mean() >= criterio:
                aprovadas += 1
        saida.append({'efeito_anual': efeito, 'poder': aprovadas / n_rodadas,
                      'rodadas': n_rodadas})
    return saida


# --------------------------------------------------------------------------
# Regimes
# --------------------------------------------------------------------------

def regimes_btc(datas, sma=200, janela_ret=90, limiar=0.10):
    """Rotula cada dia como bull, bear ou lateral, so com passado.

    bull    : BTC acima da media de `sma` dias E retorno de `janela_ret` > +10%
    bear    : abaixo da media E retorno de `janela_ret` < -10%
    lateral : o resto

    O rotulo do dia D usa fechamentos ate D-1. Nao e uma decisao de trading
    (e corte de relatorio), mas fazer o corte com dado futuro produziria
    "carry rende mais em bull" por construcao.
    """
    diario = D.carregar_diario('BTCUSDT')
    seq = [(r[0], r[4]) for r in diario]
    idx = {d: i for i, (d, _) in enumerate(seq)}
    fech = [p for _, p in seq]
    saida = {}
    for d in datas:
        i = idx.get(d)
        if i is None or i < max(sma, janela_ret) + 1:
            saida[d] = 'indefinido'
            continue
        j = i - 1                                   # ultimo dia fechado
        media = sum(fech[j - sma + 1:j + 1]) / sma
        ret = fech[j] / fech[j - janela_ret] - 1.0
        if fech[j] > media and ret > limiar:
            saida[d] = 'bull'
        elif fech[j] < media and ret < -limiar:
            saida[d] = 'bear'
        else:
            saida[d] = 'lateral'
    return saida


def por_regime(curva, rotulos):
    """Retorno anualizado da estrategia dentro de cada regime."""
    grupos = {}
    v = [(d, x) for d, x in curva]
    for i in range(1, len(v)):
        d, atual = v[i]
        anterior = v[i - 1][1]
        if anterior <= 0:
            continue
        grupos.setdefault(rotulos.get(d, 'indefinido'), []).append(atual / anterior - 1)
    return {k: {'dias': len(r), 'cagr_no_regime': cagr_de(r),
                'retorno_total': math.exp(sum(math.log1p(x) for x in r)) - 1}
            for k, r in sorted(grupos.items())}


def funding_por_regime(simbolo, rotulos):
    """A taxa de funding BRUTA em cada regime — o mecanismo por tras do
    resultado da estrategia, sem custo nenhum no meio."""
    serie = D.serie_por_dia(simbolo, None)
    grupos = {}
    for d, v in serie.items():
        if d not in rotulos or not v['n_settle']:
            continue
        g = grupos.setdefault(rotulos[d], {'taxa': 0.0, 'n': 0, 'dias': 0})
        g['taxa'] += v['soma_taxa']
        g['n'] += v['n_settle']
        g['dias'] += 1
    return {k: {'dias': g['dias'], 'settlements': g['n'],
                'taxa_media_por_settlement': g['taxa'] / g['n'] if g['n'] else 0.0,
                'anualizado_simples': (g['taxa'] / g['dias'] * 365) if g['dias'] else 0.0}
            for k, g in sorted(grupos.items())}


# --------------------------------------------------------------------------
# Ponto de equilibrio
# --------------------------------------------------------------------------

def break_even_funding(cfg_base, simular, alvo_patrimonio, series_fn,
                       lo=0.5, hi=20.0, iteracoes=24):
    """Por quantas vezes o funding observado teria de ser multiplicado para o
    carry empatar com o CDI.

    Responde a pergunta que a decomposicao levanta: nao "quanto rendeu", mas
    "quanto teria de render". Bisseccao sobre um fator que multiplica TODAS as
    taxas da serie — inclusive as negativas, que sao multiplicadas junto; nada
    de melhorar o resultado filtrando bear market.
    """
    def patrimonio(fator):
        return simular(cfg_base, series=series_fn(fator))['patrimonio_final']

    if patrimonio(hi) < alvo_patrimonio:
        return {'fator': None, 'nota': 'nem multiplicando por %g empata' % hi}
    for _ in range(iteracoes):
        meio = 0.5 * (lo + hi)
        if patrimonio(meio) < alvo_patrimonio:
            lo = meio
        else:
            hi = meio
    return {'fator': 0.5 * (lo + hi)}


def escalar_series(series, fator):
    """Copia das series com todas as taxas de funding multiplicadas."""
    saida = {}
    for s, serie in series.items():
        saida[s] = {d: dict(v, fator=v['fator'] * fator,
                            soma_taxa=v['soma_taxa'] * fator)
                    for d, v in serie.items()}
    return saida
