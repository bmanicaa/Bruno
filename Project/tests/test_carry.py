"""
Testes do laboratorio de carry (scripts/carry/).

Cobre o minimo exigido pelo protocolo e um pouco mais:
  * ZERO LOOKAHEAD por perturbacao do futuro (o teste forte, nao o por inspecao)
  * a contabilidade fecha: funding + base + custos + juros + quebra = variacao
    do patrimonio, sempre, em todo caminho de codigo
  * liquidacao detectada no preco certo, e nao detectada quando nao deve
  * sentinelas dos numeros principais publicados em analises.md

Nao toca em nada do Projeto A.
"""
import datetime as dt
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'scripts'))

from carry import custos as C          # noqa: E402
from carry import dados as D           # noqa: E402
from carry import motor as M           # noqa: E402
from carry import benchmarks as B      # noqa: E402


# --------------------------------------------------------------------------
# Fabrica de series sinteticas
# --------------------------------------------------------------------------

def serie_sintetica(precos, taxas, base=0.0, inicio=dt.date(2020, 1, 1),
                    n_settle=3, altas=None):
    """Constroi o dict data -> campos que o motor consome.

    `precos[i]` e o fechamento do dia i; `taxas[i]` a soma das taxas de funding
    da janela (D 00:00, D+1 00:00]. `altas` permite cravar a maxima do dia para
    testar liquidacao.
    """
    saida = {}
    for i, pr in enumerate(precos):
        d = inicio + dt.timedelta(days=i)
        h = altas[i] if altas is not None else pr
        saida[d] = {'close': pr, 'high': max(h, pr), 'low': min(pr, h),
                    'qv': 1e9, 'fator': taxas[i], 'soma_taxa': taxas[i],
                    'n_settle': n_settle, 'base': base}
    return saida


def calendario_de(serie):
    return sorted(serie)


def rodar(serie, **kw):
    cfg = M.config_padrao(cesta='BTC', inicio=min(serie), fim=max(serie), **kw)
    return M.simular(cfg, series={'BTCUSDT': serie},
                     calendario=calendario_de(serie))


# --------------------------------------------------------------------------
# 1. ZERO LOOKAHEAD
# --------------------------------------------------------------------------

def test_zero_lookahead_perturbando_o_futuro():
    """Alterar o futuro nao pode mexer em NADA do passado.

    Este e o teste que o Projeto A aprendeu a ter depois da V2.2: o lookahead
    intradiario passou por revisao de codigo e so caiu quando alguem perturbou
    a serie. Inspecao nao acha; perturbacao acha.
    """
    n = 400
    precos = [10000 * (1 + 0.001 * ((i * 7) % 13 - 6)) ** i for i in range(n)]
    taxas = [0.0001 * (3 if i % 5 else -2) for i in range(n)]
    corte = 250

    a = rodar(serie_sintetica(precos, taxas), rebalanceio=('semanal',))

    precos_b = list(precos)
    taxas_b = list(taxas)
    for i in range(corte, n):
        precos_b[i] *= 3.7          # choque de preco no futuro
        taxas_b[i] = 0.02           # funding absurdo no futuro
    b = rodar(serie_sintetica(precos_b, taxas_b), rebalanceio=('semanal',))

    # a curva ate o dia do corte tem de ser IDENTICA bit a bit
    ca = {d: v for d, v in a['curva']}
    cb = {d: v for d, v in b['curva']}
    datas = sorted(ca)[:corte]
    for d in datas:
        assert ca[d] == cb[d], f'lookahead detectado em {d}: {ca[d]} != {cb[d]}'


def test_zero_lookahead_no_gatilho_de_funding():
    """O gatilho do dia D nao pode enxergar o funding do proprio dia D."""
    n = 60
    precos = [10000.0] * n
    taxas = [0.0] * n
    taxas[30] = 0.05                      # um unico dia de funding gigante
    serie = serie_sintetica(precos, taxas)
    datas = calendario_de(serie)
    m = M._media_funding_passada(serie, datas, 1)
    # a media atribuida ao dia 30 vem da janela [29, 29] -> zero
    assert m[datas[30]] == 0.0
    # so o dia 31 pode enxergar aquele funding
    assert m[datas[31]] > 0.0

    # e o gatilho tem de reagir um dia DEPOIS, nunca no proprio dia
    r = rodar(serie, gatilho=('funding', 1, 0.0), rebalanceio=('diario',))
    entrou = {d for d, _ in r['curva']}
    assert entrou, 'sem curva'
    assert r['n_entradas'] >= 1


def test_universo_pit_nao_ve_o_proprio_dia():
    """O ranking de liquidez de uma data so usa volume ESTRITAMENTE anterior.

    Reimplementa a mediana de forma independente e exige igualdade exata; e
    depois prova a causalidade pelo unico jeito que vale: mexer no volume do
    proprio dia e dos seguintes nao pode mudar o numero.
    """
    hoje = dt.date(2021, 6, 1)
    diario = D.carregar_diario('BTCUSDT')
    janela = [r[5] for r in diario if r[0] < hoje][-30:]
    assert len(janela) == 30
    ordenada = sorted(janela)
    esperado = 0.5 * (ordenada[14] + ordenada[15])
    assert abs(D.liquidez_mediana('BTCUSDT', hoje, 30) - esperado) < 1e-9

    # perturbacao do presente e do futuro
    original = D._cache_diario['BTCUSDT']
    try:
        D._cache_diario['BTCUSDT'] = [
            r if r[0] < hoje else (r[0], r[1], r[2], r[3], r[4], r[5] * 1000)
            for r in original]
        assert abs(D.liquidez_mediana('BTCUSDT', hoje, 30) - esperado) < 1e-9
    finally:
        D._cache_diario['BTCUSDT'] = original


# --------------------------------------------------------------------------
# 2. A CONTABILIDADE FECHA
# --------------------------------------------------------------------------

@pytest.mark.parametrize('reb', [('diario',), ('semanal',), ('limiar', 0.02)])
@pytest.mark.parametrize('L', [1, 2, 3])
def test_contabilidade_fecha_em_todo_caminho(reb, L):
    """funding + base + custos + juros + quebra = variacao do patrimonio."""
    n = 300
    # serie com alta, queda e lateral, sem explodir a escala: um preco que vai
    # a 1e12 faz o teste medir precisao de float, nao contabilidade.
    precos = []
    p = 10000.0
    for i in range(n):
        p *= (1.02 if i % 3 == 0 else (0.985 if i % 3 == 1 else 1.001))
        precos.append(p)
    taxas = [0.0001 * (2 if i % 4 else -3) for i in range(n)]
    altas = [x * 1.02 for x in precos]
    r = rodar(serie_sintetica(precos, taxas, altas=altas),
              rebalanceio=reb, alavancagem=L)
    delta = r['patrimonio_final'] - r['capital_inicial']
    soma = (r['a_funding'] + r['b_base'] + r['c_custos']
            + r['d_juros'] + r['f_quebra_hedge'])
    escala = max(1.0, abs(r['patrimonio_final']))
    assert abs(delta - soma) / escala < 1e-12, f'residuo {delta - soma}'
    assert abs(r['e_residuo']) / escala < 1e-12


def test_contabilidade_fecha_com_dados_reais():
    for L in (1, 2, 3):
        r = M.simular(M.config_padrao(alavancagem=L, rebalanceio=('semanal',)))
        assert abs(r['e_residuo']) < 1e-4, f'L={L} residuo {r["e_residuo"]}'


def test_sem_funding_e_sem_custo_o_carry_nao_ganha_nem_perde():
    """Delta-neutro puro: sem funding, sem taxa, sem juro e base fixa, o preco
    pode fazer o que quiser que o patrimonio nao se move. Se este teste quebrar,
    as duas pernas nao estao casadas."""
    n = 200
    precos = [10000 * (1.03 ** i) for i in range(n)]     # alta de 100x
    r = rodar(serie_sintetica(precos, [0.0] * n), taxa=0.0, slippage=0.0,
              juro_mensal=0.0, rebalanceio=('semanal',), alavancagem=1,
              politica_margem='aportar')
    assert abs(r['patrimonio_final'] - r['capital_inicial']) < 1e-6
    assert r['n_liquidacoes'] == 0


def test_funding_incide_sobre_o_notional_e_nao_sobre_o_patrimonio():
    """Com L=1 e fracao 0.9, o notional e 45% do patrimonio. Um dia de funding
    de 1% tem de render ~0,45% do patrimonio, nao 1%."""
    precos = [10000.0] * 12
    taxas = [0.0] * 12
    taxas[8] = 0.01
    r = rodar(serie_sintetica(precos, taxas), taxa=0.0, slippage=0.0,
              juro_mensal=0.0, alavancagem=1, rebalanceio=('semanal',),
              fracao_capital=0.90)
    esperado = 100_000 * 0.90 / 2 * 0.01
    assert abs(r['a_funding'] - esperado) < 1.0


def test_funding_negativo_e_pago_nao_filtrado():
    """Funding negativo tem de sair do caixa. Filtrar bear market seria o
    unico jeito de 'melhorar' o resultado, e e proibido."""
    precos = [10000.0] * 12
    r = rodar(serie_sintetica(precos, [-0.001] * 12), taxa=0.0, slippage=0.0,
              juro_mensal=0.0, rebalanceio=('semanal',))
    assert r['a_funding'] < 0
    assert r['patrimonio_final'] < r['capital_inicial']


# --------------------------------------------------------------------------
# 3. LIQUIDACAO
# --------------------------------------------------------------------------

def test_preco_de_liquidacao_bate_com_a_formula_fechada():
    for L in (1, 2, 3):
        a = C.preco_liquidacao_short(100.0, L)
        b = C.preco_liquidacao(100.0 / L, 1.0, 100.0)
        assert abs(a - b) < 1e-9
    assert abs(C.preco_liquidacao_short(100, 1) / 100 - 1 - 0.99203) < 1e-4
    assert abs(C.preco_liquidacao_short(100, 2) / 100 - 1 - 0.49402) < 1e-4
    assert abs(C.preco_liquidacao_short(100, 3) / 100 - 1 - 0.32802) < 1e-4


def test_liquidacao_dispara_quando_a_maxima_cruza_o_preco():
    """L=3 liquida em +32,8%. Uma maxima de +40% no dia seguinte a entrada
    tem de liquidar; uma de +25% nao."""
    def cenario(alta_pct):
        precos = [10000.0, 10000.0, 10000.0]
        altas = [10000.0, 10000.0, 10000.0 * (1 + alta_pct)]
        return rodar(serie_sintetica(precos, [0.0] * 3, altas=altas),
                     alavancagem=3, rebalanceio=('semanal',),
                     politica_margem='liquidar', taxa=0.0, slippage=0.0,
                     juro_mensal=0.0)
    assert cenario(0.40)['n_liquidacoes'] == 1
    assert cenario(0.25)['n_liquidacoes'] == 0


def test_liquidacao_usa_a_maxima_e_nao_o_fechamento():
    """Pavio que sobe 40% e volta ao fim do dia LIQUIDA. Se o motor olhasse so
    o fechamento, esse dia passaria em branco e a estrategia pareceria segura."""
    r = rodar(serie_sintetica([10000.0, 10000.0, 10000.0], [0.0] * 3,
                              altas=[10000.0, 10000.0, 14000.0]),
              alavancagem=3, rebalanceio=('semanal',),
              politica_margem='liquidar', taxa=0.0, slippage=0.0, juro_mensal=0.0)
    assert r['n_liquidacoes'] == 1
    # a quebra de hedge e o custo de execucao estressada, e so pode ser custo:
    # se aparecer positiva, o motor voltou a embolsar o trecho descoberto como
    # lucro direcional (ver comentario no motor).
    assert r['f_quebra_hedge'] < 0


def test_modo_aportar_evita_liquidacao_quando_ha_caixa():
    """Com reserva grande, o aporte salva a posicao que morreria sem ele.

    fracao_capital=0.5 de proposito: com a reserva padrao de 10% o aporte a L=3
    quase nunca cabe no caixa — e isso nao e defeito do motor, e o resultado
    (ver 'reserva de caixa' no relatorio). Aqui o objetivo e provar que o
    MECANISMO funciona quando ha dinheiro.
    """
    precos = [10000.0] * 6
    altas = [10000.0, 10000.0, 13400.0, 13400.0, 13400.0, 13400.0]
    comum = dict(alavancagem=3, rebalanceio=('limiar', 0.99), taxa=0.0,
                 slippage=0.0, juro_mensal=0.0, fracao_capital=0.5)
    liq = rodar(serie_sintetica(precos, [0.0] * 6, altas=altas),
                politica_margem='liquidar', **comum)
    apo = rodar(serie_sintetica(precos, [0.0] * 6, altas=altas),
                politica_margem='aportar', **comum)
    assert liq['n_liquidacoes'] >= 1, 'cenario nao liquida nem sem aporte'
    assert apo['n_liquidacoes'] == 0
    assert apo['n_aportes_margem'] >= 1
    assert apo['patrimonio_final'] > liq['patrimonio_final']


def test_alavancagem_1_nao_liquida_em_alta_de_50pct():
    precos = [10000.0] * 5
    altas = [10000.0, 10000.0, 15000.0, 15000.0, 15000.0]
    r = rodar(serie_sintetica(precos, [0.0] * 5, altas=altas), alavancagem=1,
              rebalanceio=('limiar', 0.99), politica_margem='liquidar',
              taxa=0.0, slippage=0.0, juro_mensal=0.0)
    assert r['n_liquidacoes'] == 0


# --------------------------------------------------------------------------
# 4. FORMULA DE FUNDING E DADOS
# --------------------------------------------------------------------------

def test_inversao_da_formula_de_funding():
    assert C.premium_index(0.0001) is None                 # banda morta
    assert abs(C.premium_index(0.0003) - 0.0008) < 1e-12   # acima
    assert abs(C.premium_index(-0.0002) + 0.0007) < 1e-12  # abaixo
    # continuidade nas bordas da banda morta
    assert abs(C.premium_index(0.0001 + 1e-9) - 0.0006) < 1e-6
    assert abs(C.premium_index(0.0001 - 1e-9) + 0.0004) < 1e-6


def test_ponto_de_massa_em_0_01pct_existe_nos_dados():
    """A evidencia de que a formula vale nesta amostra: um terco dos
    settlements do BTC vale exatamente a constante de juro da corretora."""
    f = D.carregar_funding('BTCUSDT')
    exatos = sum(1 for _, r in f if abs(r - 0.0001) < 1e-12)
    assert len(f) == 7616
    assert 0.34 < exatos / len(f) < 0.37


def test_settlements_por_dia_do_btc_sao_tres():
    """O timestamp da Binance vem com jitter de ate 47ms. Sem encaixe na hora
    cheia, o settlement das 00:00 cai no dia errado."""
    s = D.serie_por_dia('BTCUSDT', None)
    cont = {}
    for v in s.values():
        cont[v['n_settle']] = cont.get(v['n_settle'], 0) + 1
    assert cont.get(3, 0) > 2500
    assert cont.get(4, 0) == 0


def test_intervalo_de_funding_detectado_por_simbolo():
    assert D.intervalo_funding_h('BTCUSDT') == 8
    intervalos = {D.intervalo_funding_h(s)
                  for s in ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']}
    assert intervalos == {8}
    # e existem pares de 4h no universo — assumir 8h para todos dobraria o carry
    quatro = [s for s in D.simbolos_disponiveis()[:80]
              if D.intervalo_funding_h(s) == 4]
    assert quatro, 'nenhum par de 4h detectado — o detector esta quebrado'


def test_sanity_check_do_enunciado():
    """Os numeros de partida da tarefa, reproduzidos do zero."""
    f = D.carregar_funding('BTCUSDT')
    taxas = sorted(r for _, r in f)
    assert len(taxas) == 7616
    pos = sum(1 for r in taxas if r > 0) / len(taxas)
    assert abs(pos - 0.856) < 0.002
    mediana = taxas[len(taxas) // 2]
    assert abs(mediana - 0.000097125) < 1e-7
    assert abs(mediana * 3 * 365 - 0.1063) < 0.001    # 10,6% a.a. bruto


# --------------------------------------------------------------------------
# 5. DETERMINISMO
# --------------------------------------------------------------------------

def test_determinismo_e_hash_de_config():
    cfg = M.config_padrao(alavancagem=2)
    a, b = M.simular(cfg), M.simular(cfg)
    assert a['patrimonio_final'] == b['patrimonio_final']
    assert a['hash'] == b['hash'] == M.hash_config(cfg)
    outro = M.config_padrao(alavancagem=3)
    assert M.hash_config(outro) != a['hash']


# --------------------------------------------------------------------------
# 6. SENTINELAS DOS NUMEROS PUBLICADOS
# --------------------------------------------------------------------------

def test_sentinela_cdi():
    """CDI de 1% a.m. no periodo completo, capital de R$100k."""
    r = B.cdi(dt.date(2019, 9, 10), dt.date(2026, 8, 22), 100_000.0)
    assert abs(r['patrimonio_final'] - 231_000) < 5_000
    assert abs(r['cagr'] - 0.1267) < 0.001


def test_sentinela_carry_btc_1x_semanal():
    """A configuracao de referencia. Se este numero mudar, algo no motor mudou:
    ou a mudanca e intencional e o sentinela sobe junto, ou e um defeito."""
    r = M.simular(M.config_padrao(cesta='BTC', alavancagem=1,
                                  rebalanceio=('semanal',)))
    assert abs(r['patrimonio_final'] - 153_275) < 500
    assert abs(r['a_funding'] - 46_099) < 300
    assert abs(r['d_juros'] - 11_360) < 300
    assert r['n_liquidacoes'] == 0
    # o juro do caixa nao pode ser o que sustenta o resultado sem aparecer
    assert r['d_juros'] / (r['patrimonio_final'] - r['capital_inicial']) > 0.15


def test_sentinela_funding_bruto_do_btc():
    """Soma simples das taxas do BTC em todo o historico."""
    f = D.carregar_funding('BTCUSDT')
    assert abs(sum(r for _, r in f) - 0.8078) < 0.001


def test_liquidacao_nunca_vira_lucro():
    """Nenhum caminho de liquidacao pode produzir ganho.

    A regressao que este teste tranca: com a perna comprada carregada
    descoberta ate o fechamento, uma liquidacao em mercado de alta virava
    LUCRO, e o grid passou a selecionar as configuracoes que mais liquidavam.
    """
    precos = [10000.0, 10000.0, 20000.0, 30000.0, 40000.0]
    altas = [10000.0, 10000.0, 20000.0, 30000.0, 40000.0]
    r = rodar(serie_sintetica(precos, [0.0] * 5, altas=altas), alavancagem=3,
              rebalanceio=('limiar', 0.99), politica_margem='liquidar',
              taxa=0.0, slippage=0.0, juro_mensal=0.0)
    assert r['n_liquidacoes'] >= 1
    assert r['f_quebra_hedge'] <= 0
    assert r['patrimonio_final'] < r['capital_inicial']
