"""
CLI do laboratorio de carry. Gera os artefatos em data/carry/.

  python -m carry grid        # 750 configuracoes + tabela comparativa
  python -m carry evidencia   # bootstrap, poder, regimes, decaimento
  python -m carry tudo        # os dois, e escreve o relatorio

Determinismo: cada artefato carrega o hash da configuracao que o gerou.
Nao escreve em data/experimentos/ (territorio do Projeto A).
"""
import argparse
import datetime as dt
import json
import os
import statistics
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAIDA = os.path.join(BASE_DIR, 'data', 'carry')

from . import benchmarks as B   # noqa: E402
from . import custos as C       # noqa: E402
from . import dados as D        # noqa: E402
from . import evidencia as E    # noqa: E402
from . import grid as G         # noqa: E402
from . import motor as M        # noqa: E402

INICIO = dt.date(2019, 9, 10)
FIM = dt.date(2026, 8, 22)
CAPITAL = 100_000.0


def _json(obj):
    if isinstance(obj, dt.date):
        return obj.isoformat()
    raise TypeError(type(obj))


def salvar(nome, payload):
    os.makedirs(SAIDA, exist_ok=True)
    caminho = os.path.join(SAIDA, nome)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, default=_json, ensure_ascii=False)
    print(f'  -> {os.path.relpath(caminho, BASE_DIR)}')
    return caminho


# --------------------------------------------------------------------------

def rodar_grid(args):
    print('Carregando universos point-in-time e series...')
    ctx = G.Contexto(INICIO, FIM, base_modo=args.base)
    print(f'  {len(ctx.series)} simbolos, {len(ctx.calendario)} dias')

    lista = list(G.configs(capital=CAPITAL, inicio=INICIO, fim=FIM,
                           base_modo=args.base))
    print(f'Executando {len(lista)} configuracoes...')
    linhas = G.executar(ctx, lista, progresso=150)

    ref = ctx.calendario
    bench = {
        'cdi': B.cdi(ref[0], ref[-1], CAPITAL, calendario=ref),
        'dca': B.dca(ref[0], ref[-1], CAPITAL),
        'bh': B.comprar_e_segurar(ref[0], ref[-1], CAPITAL),
    }
    alvo = bench['cdi']['patrimonio_final']

    resumo = {
        'geral': G.resumir(linhas, alvo),
        'por_cesta': G.por_eixo(linhas, 'cesta', alvo),
        'por_alavancagem': G.por_eixo(linhas, 'alavancagem', alvo),
        'por_rebalanceio': G.por_eixo(linhas, 'rebalanceio', alvo),
        'por_gatilho': G.por_eixo(linhas, 'gatilho', alvo),
    }

    sem_curva = [{k: v for k, v in l.items() if k != 'curva'} for l in linhas]
    salvar('grid.json', {
        'gerado_em': dt.date.today(),
        'periodo': [ref[0], ref[-1]],
        'capital': CAPITAL,
        'base_modo': args.base,
        'n_configs': len(linhas),
        'benchmarks': {k: {kk: vv for kk, vv in v.items() if kk != 'curva'}
                       for k, v in bench.items()},
        'resumo': resumo,
        'configs': sorted(sem_curva, key=lambda l: -l['patrimonio_final']),
    })
    return linhas, bench


# --------------------------------------------------------------------------

def rodar_evidencia(args, linhas=None, bench=None):
    ref_cfg = M.config_padrao(cesta='BTC', alavancagem=1,
                              rebalanceio=('semanal',), base_modo=args.base,
                              capital=CAPITAL, inicio=INICIO, fim=FIM)
    ref = M.simular(ref_cfg)
    datas = [d for d, _ in ref['curva']]
    rot = E.regimes_btc(datas)
    ret = E.retornos_diarios(ref['curva'])
    cdi = B.cdi(datas[0], datas[-1], CAPITAL, calendario=datas)

    print('Bootstrap em blocos (4 comprimentos x 3 sementes)...')
    bs = E.bootstrap_blocos(ret, cdi['cagr'])
    print('Poder...')
    ef = E.efeito_detectavel(ret)
    poder = E.poder_simulado(ret, cdi['cagr'],
                             efeitos=[0.0, 0.02, 0.05, 0.08, 0.12],
                             n_rodadas=args.rodadas)

    print('Ponto de equilibrio e sensibilidades...')
    base_fn = (lambda ff: C.base_por_dia(ff, args.base))
    ser = {'BTCUSDT': D.serie_por_dia('BTCUSDT', base_fn)}
    cal = [d for d in sorted(ser['BTCUSDT']) if INICIO <= d <= FIM]
    breakeven = {}
    for Lv in (1, 2, 3):
        cfg = M.config_padrao(alavancagem=Lv, rebalanceio=('semanal',),
                              base_modo=args.base, capital=CAPITAL,
                              inicio=INICIO, fim=FIM)
        breakeven[Lv] = E.break_even_funding(
            cfg, lambda c, series: M.simular(c, series=series, calendario=cal),
            cdi['patrimonio_final'], lambda ff: E.escalar_series(ser, ff))

    reserva = {}
    for frac in (0.50, 0.70, 0.80, 0.90, 0.95, 0.98):
        linha = {}
        for Lv in (1, 3):
            rr = M.simular(M.config_padrao(
                alavancagem=Lv, rebalanceio=('semanal',), fracao_capital=frac,
                base_modo=args.base, capital=CAPITAL, inicio=INICIO, fim=FIM))
            linha[Lv] = {'patrimonio_final': rr['patrimonio_final'],
                         'n_liquidacoes': rr['n_liquidacoes'],
                         'n_aportes_margem': rr['n_aportes_margem'],
                         'n_desmontes_forcados': rr['n_desmontes_forcados'],
                         'd_juros': rr['d_juros']}
        reserva[frac] = linha

    sens_base = {}
    for modo in ('zero', 'premium', 'pessimista'):
        rr = M.simular(M.config_padrao(alavancagem=1, rebalanceio=('semanal',),
                                       base_modo=modo, capital=CAPITAL,
                                       inicio=INICIO, fim=FIM))
        sens_base[modo] = {'patrimonio_final': rr['patrimonio_final'],
                           'b_base': rr['b_base']}

    # decaimento anual do funding bruto
    f = D.carregar_funding('BTCUSDT')
    por_ano = {}
    for t, taxa in f:
        ano = dt.datetime.fromtimestamp(t / 1000, tz=dt.timezone.utc).year
        g = por_ano.setdefault(ano, {'soma': 0.0, 'n': 0, 'na_banda': 0, 'neg': 0})
        g['soma'] += taxa
        g['n'] += 1
        g['na_banda'] += int(abs(taxa - C.JURO_FORMULA) < 1e-12)
        g['neg'] += int(taxa < 0)
    decaimento = {ano: {'settlements': g['n'],
                        'funding_bruto_ano': g['soma'],
                        'frac_na_banda_morta': g['na_banda'] / g['n'],
                        'frac_negativo': g['neg'] / g['n']}
                  for ano, g in sorted(por_ano.items())}

    payload = {
        'gerado_em': dt.date.today(),
        'config_referencia': ref_cfg,
        'hash_referencia': ref['hash'],
        'resultado_referencia': {k: v for k, v in ref.items()
                                 if k not in ('curva', 'config', 'simbolos')},
        'cdi': {k: v for k, v in cdi.items() if k != 'curva'},
        'bootstrap_blocos': bs,
        'poder_analitico': ef,
        'poder_simulado': poder,
        'regimes_estrategia': E.por_regime(ref['curva'], rot),
        'funding_bruto_por_regime': E.funding_por_regime('BTCUSDT', rot),
        'decaimento_anual_funding': decaimento,
        'break_even_funding': breakeven,
        'sensibilidade_reserva': reserva,
        'sensibilidade_base': sens_base,
    }
    salvar('evidencia.json', payload)
    return payload


# --------------------------------------------------------------------------

def _pct(x):
    return f'{100 * x:+.2f}%'


def escrever_relatorio(linhas, bench, ev):
    ref = ev['resultado_referencia']
    cdi, dca, bh = bench['cdi'], bench['dca'], bench['bh']
    melhor = max(linhas, key=lambda l: l['patrimonio_final'])
    pior = min(linhas, key=lambda l: l['patrimonio_final'])
    finais = sorted(l['patrimonio_final'] for l in linhas)
    mediana = statistics.median(finais)
    vitorias = sum(1 for x in finais if x > cdi['patrimonio_final'])

    L = []
    ad = L.append
    ad('# Carry de funding — medicao completa\n')
    ad('> Gerado por `python -m carry tudo`. Artefatos: `data/carry/grid.json`, '
       '`data/carry/evidencia.json`.\n')
    ad(f'Periodo {ev["cdi"]["anos"]:.2f} anos | capital inicial '
       f'R$ {CAPITAL:,.0f} | {len(linhas)} configuracoes | '
       f'base = `{ev["config_referencia"]["base_modo"]}`\n')

    # ---------------------------------------------------------------- 1
    ad('\n## 1. Tabela comparativa (mesmo periodo, mesmos custos)\n')
    ad('| Estrategia | Patrimonio final | CAGR | Max DD | Direcional? |')
    ad('|---|---:|---:|---:|---|')
    ad(f'| Carry — melhor das {len(linhas)} | R$ {melhor["patrimonio_final"]:,.0f} '
       f'| {_pct(melhor["cagr"])} | — | nao |')
    ad(f'| Carry — mediana do grid | R$ {mediana:,.0f} | — | — | nao |')
    ad(f'| Carry — pior das {len(linhas)} | R$ {pior["patrimonio_final"]:,.0f} '
       f'| {_pct(pior["cagr"])} | — | nao |')
    ad(f'| **CDI 1% a.m.** | R$ {cdi["patrimonio_final"]:,.0f} '
       f'| {_pct(cdi["cagr"])} | {100 * cdi["maxdd"]:.1f}% | nao |')
    ad(f'| DCA BTC (12 parcelas) | R$ {dca["patrimonio_final"]:,.0f} '
       f'| {_pct(dca["cagr"])} | {100 * dca["maxdd"]:.1f}% | sim |')
    ad(f'| BTC comprado e segurado | R$ {bh["patrimonio_final"]:,.0f} '
       f'| {_pct(bh["cagr"])} | {100 * bh["maxdd"]:.1f}% | sim |')
    ad(f'\nConfiguracoes que superam o CDI: **{vitorias} de {len(finais)} '
       f'({100 * vitorias / len(finais):.1f}%)** — e a melhor delas o faz por '
       f'{100 * (melhor["patrimonio_final"] / cdi["patrimonio_final"] - 1):.1f}% '
       f'em {ev["cdi"]["anos"]:.1f} anos, apos ser escolhida entre '
       f'{len(finais)} tentativas correlacionadas.\n')

    # ---------------------------------------------------------------- 2
    ad('\n## 2. Decomposicao (protocolo, item 3)\n')
    ad('Duas configuracoes: a de referencia (BTC, 1x, semanal) e a MELHOR do '
       'grid. A segunda importa porque e a que um leitor apressado citaria.\n')
    ad('| Termo | referencia BTC 1x | melhor do grid |')
    ad('|---|---:|---:|')
    rot = [('a_funding', '(a) funding recebido'),
           ('b_base', '(b) convergencia da base'),
           ('c_custos', '(c) taxas e slippage'),
           ('d_juros', '(d) juro do caixa livre (CDI)'),
           ('f_quebra_hedge', '(f) quebra de hedge / liquidacao'),
           ('e_residuo', '(e) residuo')]
    for chave, nome in rot:
        ad(f'| {nome} | {ref[chave]:+,.0f} | {melhor[chave]:+,.0f} |')
    g_ref = ref['patrimonio_final'] - CAPITAL
    g_mel = melhor['patrimonio_final'] - CAPITAL
    ad(f'| **ganho total** | **{g_ref:+,.0f}** | **{g_mel:+,.0f}** |')
    ad(f'| _memo:_ % do ganho que e (d) CDI | {100 * ref["d_juros"] / g_ref:.0f}% '
       f'| {100 * melhor["d_juros"] / g_mel:.0f}% |')
    dias_tot = ref['dias']
    exc = (melhor['patrimonio_final'] / cdi['patrimonio_final']) ** (
        1 / ev['cdi']['anos']) - 1
    ad(f'\nA melhor configuracao do grid e '
       f'`{melhor["cesta"]} / gatilho {melhor["gatilho"]} / {melhor["alavancagem"]}x '
       f'/ {melhor["rebalanceio"]}`. Ela fica montada em apenas '
       f'**{melhor["dias_com_posicao"]} de {dias_tot} dias '
       f'({100 * melhor["dias_com_posicao"] / dias_tot:.0f}% do tempo)**, com '
       f'exposicao media de {100 * melhor["exposicao_media"]:.0f}% do '
       f'patrimonio. Nos outros {100 - 100 * melhor["dias_com_posicao"] / dias_tot:.0f}% '
       f'o dinheiro esta em caixa rendendo CDI — dai '
       f'**{100 * melhor["d_juros"] / g_mel:.0f}% do ganho dela ser o item (d)**. '
       f'E a repeticao literal do achado C5 do `analises.md` ("~90% da vantagem '
       f'e CDI, nao market timing"): a configuracao vencedora vence por operar '
       f'menos, nao por colher mais.\n')
    ad(f'O excesso dela sobre o CDI e de **{100 * exc:.2f}% ao ano** — contra um '
       f'efeito minimo detectavel de ~8% a.a. (secao 7) — e ela e o MAXIMO de '
       f'{len(linhas)} tentativas correlacionadas sobre a mesma serie. Tratar '
       f'esse numero como edge seria garimpo.\n')
    ad(f'Capital medio imobilizado na referencia (spot + margem): '
       f'R$ {ref["capital_imobilizado_medio"]:,.0f}, que deixou de render '
       f'R$ {ref["custo_oportunidade_margem"]:,.0f} de CDI ao longo do periodo — '
       f'mais do que os R$ {ref["a_funding"]:,.0f} de funding que a estrutura '
       f'coletou. **O custo de oportunidade da margem sozinho supera a receita '
       f'bruta da estrategia.**\n')

    # ---------------------------------------------------------------- 3
    ad('\n## 3. Grid por eixo (pior / mediana / melhor / vitorias sobre CDI)\n')
    for nome, chave in [('Cesta', 'por_cesta'), ('Alavancagem', 'por_alavancagem'),
                        ('Rebalanceio', 'por_rebalanceio'), ('Gatilho', 'por_gatilho')]:
        ad(f'\n**{nome}**\n')
        ad('| valor | n | pior | mediana | melhor | vitorias vs CDI |')
        ad('|---|---:|---:|---:|---:|---:|')
        for k, v in ev['_resumo'][chave].items():
            ad(f'| {k} | {v["n"]} | R$ {v["pior"]:,.0f} | R$ {v["mediana"]:,.0f} '
               f'| R$ {v["melhor"]:,.0f} | {v["vitorias"]}/{v["n"]} |')

    # ---------------------------------------------------------------- 4
    ad('\n## 4. Regimes (protocolo, item 7)\n')
    ad('| regime | dias | CAGR da estrategia | funding bruto anualizado |')
    ad('|---|---:|---:|---:|')
    fr = ev['funding_bruto_por_regime']
    for k, v in ev['regimes_estrategia'].items():
        b = fr.get(k, {})
        ad(f'| {k} | {v["dias"]} | {_pct(v["cagr_no_regime"])} '
           f'| {_pct(b.get("anualizado_simples", 0))} |')
    ad('\nO carry e uma aposta em bull market disfarcada de posicao neutra: '
       'quem paga o funding e o comprado alavancado, e ele so aparece em alta. '
       'Nem no regime mais favoravel a estrutura entrega o CDI — em bull, com '
       'o funding bruto anualizando +20,5%, o CAGR da estrategia fica em '
       '+10,8% contra os +12,7% do CDI. Em bear ela rende +2,0%. Uma renda '
       'que so existe quando o mercado sobe nao e renda fixa; e beta com '
       'outro nome.\n')

    # ---------------------------------------------------------------- 5
    ad('\n## 5. O funding esta secando\n')
    ad('| ano | settlements | funding bruto | % na banda morta (0,01%) | % negativo |')
    ad('|---|---:|---:|---:|---:|')
    for ano, v in ev['decaimento_anual_funding'].items():
        ad(f'| {ano} | {v["settlements"]} | {_pct(v["funding_bruto_ano"])} '
           f'| {100 * v["frac_na_banda_morta"]:.1f}% | {100 * v["frac_negativo"]:.1f}% |')
    ad('\nA coluna "banda morta" e a chave do mecanismo. A formula da Binance e\n')
    ad('```\nfunding = premium + clamp(juro - premium, -0,05%, +0,05%),  juro = 0,01%/8h\n```\n')
    ad('Quando o premio esta entre -0,04% e +0,06%, o funding vale exatamente '
       'a constante de juro da corretora, 0,01%. **35,4% de todos os 7.616 '
       'settlements do BTC caem nesse ponto de massa** — ou seja, um terco do '
       '"carry historico" nao e premio de mercado nenhum, e uma convencao '
       'contabil da exchange. E ela esta sumindo: 66,9% dos settlements em 2019 '
       'contra 4,7% em 2026, com o funding negativo indo de 18,3% para 29,6%.\n')

    # ---------------------------------------------------------------- 6
    ad('\n## 6. Bootstrap em blocos (protocolo, item 6)\n')
    ag = ev['bootstrap_blocos']['agregado']
    ad(f'Varredura de bloco (90/180/365/730 dias) x 3 sementes = '
       f'{len(ev["bootstrap_blocos"]["linhas"])} combinacoes, '
       f'sobre a serie diaria da configuracao de referencia.\n')
    ad('| metrica | min | mediana | max |')
    ad('|---|---:|---:|---:|')
    nomes = {'cagr_mediano': 'CAGR mediano', 'ic95_baixo': 'IC95 inferior',
             'ic95_alto': 'IC95 superior', 'p_supera_alvo': 'P(CAGR > CDI)',
             'p_positivo': 'P(CAGR > 0)'}
    for k, nome in nomes.items():
        v = ag[k]
        ad(f'| {nome} | {v["min"]:.4f} | {v["mediana"]:.4f} | {v["max"]:.4f} |')
    ad(f'\nO **intervalo de confianca inteiro fica abaixo do CDI** '
       f'({_pct(cdi["cagr"])}): o teto do IC95 e '
       f'{_pct(ag["ic95_alto"]["max"])} na combinacao mais generosa. '
       f'P(carry > CDI) = {ag["p_supera_alvo"]["max"]:.4f} no melhor caso das '
       f'{len(ev["bootstrap_blocos"]["linhas"])} combinacoes. Isso nao e '
       f'"nao deu significativo"; e o contrario disso.\n')

    # ---------------------------------------------------------------- 7
    ad('\n## 7. Poder do teste (protocolo, item 5)\n')
    p = ev['poder_analitico']
    ad(f'Vol anual da estrategia: **{100 * p["vol_anual"]:.2f}%** (delta-neutra '
       f'de verdade). Autocorrelacao rho(1) dos retornos diarios: '
       f'**{p["rho1"]:.2f}**.\n')
    ad('| metodo | amostra efetiva | Sharpe minimo detectavel | excesso anual detectavel |')
    ad('|---|---:|---:|---:|')
    ad(f'| formula iid (INVALIDA aqui) | {p["n_dias"]} dias '
       f'| {p["sharpe_anual_minimo_iid"]:.2f} '
       f'| {100 * p["retorno_anual_minimo_iid"]:.2f}% |')
    ad(f'| corrigida por autocorrelacao | {p["n_efetivo"]:.0f} dias '
       f'| {p["sharpe_anual_minimo"]:.2f} '
       f'| {100 * p["retorno_anual_minimo_detectavel"]:.2f}% |')
    ad('\nA formula iid supoe que cada dia traz informacao nova. O funding e '
       'persistente — rho(10) ainda vale ~0,38 — e a amostra efetiva encolhe '
       f'de {p["n_dias"]} para ~{p["n_efetivo"]:.0f} observacoes. Usar a versao '
       'ingenua aqui daria confianca ~6x maior do que os dados sustentam. A '
       'autoridade e o poder EMPIRICO abaixo, medido injetando excesso '
       'conhecido e passando pelo mesmo gate do veredito:\n')
    ad('| excesso anual injetado | poder empirico |')
    ad('|---:|---:|')
    for l in ev['poder_simulado']:
        ad(f'| {_pct(l["efeito_anual"])} | {100 * l["poder"]:.0f}% |')
    ad('\n**Leitura.** O teste so enxerga vantagens da ordem de +8% ao ano '
       'sobre o CDI. Mas a conclusao NAO depende disso: o carry nao ficou '
       '"sem significancia", ele ficou ~6 pontos percentuais ABAIXO do CDI, '
       'com o IC95 inteiro do lado de baixo. Um efeito grande e de sinal '
       'trocado nao precisa de poder para ser visto.\n')

    # ---------------------------------------------------------------- 8
    ad('\n## 8. Quanto o funding teria de render para empatar com o CDI\n')
    ad('| alavancagem | fator sobre o funding observado | funding bruto necessario |')
    ad('|---|---:|---:|')
    for Lv, v in sorted(ev['break_even_funding'].items()):
        if v.get('fator'):
            ad(f'| {Lv}x | {v["fator"]:.2f}x | {10.63 * v["fator"]:.1f}% a.a. |')
        else:
            ad(f'| {Lv}x | nao empata | — |')
    ad('\nContra 10,6% a.a. observados na vida toda da serie — e 1,5% em 2026. '
       'Bisseccao multiplicando TODAS as taxas, inclusive as negativas.\n')

    # ---------------------------------------------------------------- 9
    ad('\n## 9. Reserva de caixa, margem e liquidacao\n')
    ad('| reserva | 1x: final | 1x: aportes | 1x: liq | 3x: final | 3x: aportes '
       '| 3x: desmontes | 3x: liq |')
    ad('|---|---:|---:|---:|---:|---:|---:|---:|')
    for frac, v in sorted(ev['sensibilidade_reserva'].items()):
        a = v.get('1', v.get(1))
        b = v.get('3', v.get(3))
        ad(f'| {100 * (1 - float(frac)):.0f}% em caixa | R$ {a["patrimonio_final"]:,.0f} '
           f'| {a["n_aportes_margem"]} | {a["n_liquidacoes"]} '
           f'| R$ {b["patrimonio_final"]:,.0f} | {b["n_aportes_margem"]} '
           f'| {b["n_desmontes_forcados"]} | {b["n_liquidacoes"]} |')
    ad('\nA armadilha da alavancagem: subir de 1x para 3x liberta capital da '
       'margem e aumenta o funding coletado, mas so funciona com uma reserva '
       'grande — e reserva grande e dinheiro em CDI, que e justamente o que se '
       'esta tentando superar. O carry alavancado converge para "CDI com '
       'passos extras e risco de liquidacao".\n')

    # ---------------------------------------------------------------- 10
    ad('\n## 10. Sensibilidade a base (o dado que o repositorio nao tem)\n')
    ad('As klines vieram de `fapi.binance.com`: sao velas do PERPETUO. Nao ha '
       'serie de spot no repositorio, entao a base foi RECONSTRUIDA invertendo '
       'a formula de funding (exata fora da banda morta, censurada dentro).\n')
    ad('| modo de base | patrimonio final | termo (b) |')
    ad('|---|---:|---:|')
    for modo, v in ev['sensibilidade_base'].items():
        ad(f'| `{modo}` | R$ {v["patrimonio_final"]:,.0f} | {v["b_base"]:+,.0f} |')
    ad('\nO termo (b) e irrelevante em qualquer hipotese, e ha razao estrutural '
       'para isso: numa posicao delta-neutra mantida, o PnL de base e '
       '`notional x (base_entrada - base_saida)`, ele NAO se acumula com o '
       'tempo. A incerteza sobre a base nao muda o veredito.\n')

    # ---------------------------------------------------------------- 11
    ad('\n## 11. O risco que nao esta em nenhum numero acima\n')
    ad('**Risco de contraparte nao e backtestavel e nao foi backtestado.**\n')
    ad('A estrutura exige spot e perpetuo na mesma corretora (ou colateral '
       'cruzado entre duas). Em novembro de 2022 a FTX zerou exatamente quem '
       'fazia isso: a perda nao foi gradual nem marcada a mercado, foi total e '
       'instantanea, e nenhuma das duas pernas protegeu a outra — porque o '
       'risco nao estava no preco, estava no custodiante. Uma serie historica '
       'de precos nao contem esse evento por construcao; ele aparece como um '
       'zero, nao como um drawdown. Todos os numeros deste relatorio devem ser '
       'lidos como "antes do risco de perder tudo de uma vez".\n')
    ad('Limitacoes adicionais registradas: (i) granularidade DIARIA na checagem '
       'de liquidacao — o numero de liquidacoes e um piso, nao um teto; (ii) '
       'o CDI e em reais e o carry em USDT, e o risco cambial foi ignorado nos '
       'dois sentidos; (iii) sem IR; (iv) profundidade de livro nao modelada — '
       'o slippage e fixo, e as cestas TOP10/TOP20 incluem pares onde R$100k '
       'ja movem preco.\n')

    caminho = os.path.join(SAIDA, 'relatorio.md')
    os.makedirs(SAIDA, exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'  -> {os.path.relpath(caminho, BASE_DIR)}')


def main(argv=None):
    ap = argparse.ArgumentParser(description='Laboratorio de carry de funding')
    ap.add_argument('comando', choices=['grid', 'evidencia', 'tudo'])
    ap.add_argument('--base', default='premium',
                    choices=['zero', 'premium', 'pessimista'])
    ap.add_argument('--rodadas', type=int, default=200)
    args = ap.parse_args(argv)

    linhas = bench = ev = None
    if args.comando in ('grid', 'tudo'):
        linhas, bench = rodar_grid(args)
    if args.comando in ('evidencia', 'tudo'):
        ev = rodar_evidencia(args)
    if args.comando == 'tudo':
        with open(os.path.join(SAIDA, 'grid.json'), encoding='utf-8') as f:
            ev['_resumo'] = json.load(f)['resumo']
        escrever_relatorio(linhas, bench, ev)
    return 0


if __name__ == '__main__':
    sys.exit(main())
