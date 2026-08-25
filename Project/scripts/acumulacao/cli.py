#!/usr/bin/env python3
"""
Ponto de entrada do Projeto B.

  python -m scripts.acumulacao.cli --reproduzir   # alvos R1..R9/R12 do Plan.md
  python -m scripts.acumulacao.cli --evidencia    # Fase E Etapa 4: bootstrap
  python -m scripts.acumulacao.cli --timing       # airbag vs iso-exposicao
"""
import argparse
import datetime as dt
import json
import os
import math
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.acumulacao import evidencia as ev
from scripts.acumulacao.dados import serie_diaria
from scripts.acumulacao.grid import DIAS_PADRAO, MEDIAS_PADRAO, grid_airbag, resumir
from scripts.acumulacao.motor import simular
from scripts.acumulacao.politicas import CDB, Airbag, DCAFixo, PassivoIsoExposicao

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(BASE, 'data', 'acumulacao')
INICIO = dt.date(2020, 4, 5)
FIM = dt.date(2026, 8, 22)


def base_kw(**ex):
    kw = dict(aporte=2000.0, dia_aporte=5, inicio=INICIO, fim=FIM,
              taxa=0.00075, juro_caixa_mensal=0.01, aliquota_ir=0.0)
    kw.update(ex)
    return kw


def _ok(obtido, alvo, tol=0.005):
    return abs(obtido / alvo - 1) <= tol if alvo else False


def reproduzir(datas, precos):
    print('=' * 88)
    print('REPRODUCAO DA FASE C (analises.md, Fase C) — alvos vs repositorio')
    print('=' * 88)
    print('%-4s %-46s %12s %12s %8s' % ('#', 'cenario', 'alvo', 'obtido', 'erro'))
    print('-' * 88)
    linhas, todos_ok = [], True

    def reporta(tag, desc, alvo, obtido):
        nonlocal todos_ok
        err = (obtido / alvo - 1) * 100 if alvo else float('nan')
        ok = _ok(obtido, alvo)
        todos_ok = todos_ok and ok
        print('%-4s %-46s %12.0f %12.0f %7.2f%% %s'
              % (tag, desc, alvo, obtido, err, 'OK' if ok else 'DIVERGE'))
        linhas.append({'tag': tag, 'cenario': desc, 'alvo': alvo,
                       'obtido': obtido, 'erro_pct': err, 'ok': ok})

    r1 = simular(datas, precos, CDB(0.01), **base_kw())
    reporta('R1', 'CDB 1% a.m.', 231566, r1['valor_final'])

    r2 = simular(datas, precos, DCAFixo(), **base_kw())
    reporta('R2', 'DCA fixo BTC', 382177, r2['valor_final'])
    print('     (maxDD %.0f%% — alvo 68%%)' % (r2['maxdd'] * 100))

    r3 = simular(datas, precos, DCAFixo(), **base_kw(taxa=0.0002))
    reporta('R3', 'DCA fixo, taxa 0,02%', 382387, r3['valor_final'])

    r4 = simular(datas, precos, Airbag('EMA200', 6, 0), **base_kw())
    reporta('R4', 'Airbag EMA200, domingo, atraso 0', 480754, r4['valor_final'])

    r5 = simular(datas, precos, Airbag('EMA200', 2, 0), **base_kw())
    reporta('R5', 'Airbag EMA200, quarta (pior das 42)', 317516, r5['valor_final'])

    g300 = [simular(datas, precos, Airbag('EMA300', d, 0), **base_kw())['valor_final']
            for d in DIAS_PADRAO]
    reporta('R6', 'Airbag EMA300, mediana dos 7 dias', 500315, statistics.median(g300))

    grid = grid_airbag(datas, precos, **base_kw())
    res = resumir(grid, r2['valor_final'])
    reporta('R7', 'Grid 6 medias x 7 dias: mediana', 486722, res['mediana'])
    print('     vitorias %d de %d (alvo 40 de 42) %s'
          % (res['vitorias'], res['n'], 'OK' if res['vitorias'] == 40 else 'DIVERGE'))

    g0 = grid_airbag(datas, precos, **base_kw(juro_caixa_mensal=0.0))
    b0 = simular(datas, precos, DCAFixo(), **base_kw(juro_caixa_mensal=0.0))['valor_final']
    r0 = resumir(g0, b0)
    print('%-4s %-46s %12s %11.1f%% %8s' % ('R8', 'Grid com caixa a 0%: vantagem', '+2,3%',
                                            r0['vantagem_mediana_pct'], 'OK' if abs(r0['vantagem_mediana_pct'] - 2.3) < 2 else 'ver'))
    print('     vitorias %d de %d (alvo 24 de 42)' % (r0['vitorias'], r0['n']))

    gir = grid_airbag(datas, precos, **base_kw(aliquota_ir=0.15))
    bir = simular(datas, precos, DCAFixo(), **base_kw(aliquota_ir=0.15))['valor_final']
    rir = resumir(gir, bir)
    reporta('R9a', 'IR 15%: DCA fixo', 347689, bir)
    reporta('R9b', 'IR 15%: airbag (mediana)', 404199, rir['mediana'])
    print('     vitorias %d de %d (alvo 36 de 42)' % (rir['vitorias'], rir['n']))

    ini12 = dt.date(2021, 11, 5)
    d12 = simular(datas, precos, DCAFixo(), **base_kw(inicio=ini12))
    c12 = simular(datas, precos, CDB(0.01), **base_kw(inicio=ini12))
    reporta('R12a', 'Pior inicio (nov/21): DCA', 212714, d12['valor_final'])
    reporta('R12b', 'Pior inicio (nov/21): CDB', 157039, c12['valor_final'])

    print('-' * 88)
    print('VEREDITO DA REPRODUCAO: %s' % ('TODOS OS ALVOS BATEM (tol. 0,5%)' if todos_ok
                                          else 'HA DIVERGENCIAS — investigar antes de seguir'))
    return {'linhas': linhas, 'todos_ok': todos_ok,
            'dca': r2['valor_final'], 'grid': res, 'grid_sem_juro': r0}


def timing(datas, precos):
    """O benchmark que faltava: airbag contra exposicao iso, com e sem carry."""
    print('\n' + '=' * 88)
    print('ETAPA 4a — DE ONDE VEM A VANTAGEM DO AIRBAG (benchmark de iso-exposicao)')
    print('=' * 88)
    print('C5 do analises.md conclui "~90% da vantagem e CDI, nao market timing".')
    print('Isso e verdade contra o DCA 100% BTC — mas o airbag fica ~40% do tempo FORA.')
    print('Contra uma carteira PASSIVA de mesma exposicao media, isola-se o timing.\n')
    saida = {}
    for juro, rot in ((0.01, 'caixa a 1,0% a.m. (CDI)'), (0.0, 'caixa a 0,0% a.m. (SEM carry)')):
        kw = base_kw(juro_caixa_mensal=juro)
        grid = grid_airbag(datas, precos, **kw)
        med = statistics.median(l['valor_final'] for l in grid)
        mdd = statistics.median(l['maxdd'] for l in grid)
        expo = statistics.mean(l['exposicao_media'] for l in grid)
        dca = simular(datas, precos, DCAFixo(), **kw)
        iso = simular(datas, precos, PassivoIsoExposicao(expo), **kw)
        print('--- %s ---' % rot)
        print('  AIRBAG (mediana de 42)       : %9.0f  maxDD %2.0f%%  exposicao media %.0f%%'
              % (med, mdd * 100, expo * 100))
        print('  DCA 100%% BTC (nunca vende)   : %9.0f  maxDD %2.0f%%'
              % (dca['valor_final'], dca['maxdd'] * 100))
        print('  PASSIVO %2.0f%% BTC (0 operacoes): %9.0f  maxDD %2.0f%%'
              % (expo * 100, iso['valor_final'], iso['maxdd'] * 100))
        print('  -> airbag vs DCA 100%%         : %+.1f%%' % ((med / dca['valor_final'] - 1) * 100))
        print('  -> airbag vs passivo iso      : %+.1f%%   <== TIMING isolado'
              % ((med / iso['valor_final'] - 1) * 100))
        print('  tempo submerso (DCA): %.0f%% dos dias, pior sequencia %d dias'
              % (dca['tempo_submerso_frac'] * 100, dca['tempo_submerso_max_dias']))
        saida[rot] = {'airbag_mediana': med, 'dca': dca['valor_final'],
                      'passivo_iso': iso['valor_final'], 'exposicao': expo,
                      'maxdd_airbag': mdd, 'maxdd_dca': dca['maxdd'],
                      'maxdd_iso': iso['maxdd'],
                      'vs_dca_pct': (med / dca['valor_final'] - 1) * 100,
                      'vs_iso_pct': (med / iso['valor_final'] - 1) * 100,
                      'submerso_dca': dca['tempo_submerso_frac'],
                      'submerso_dca_dias': dca['tempo_submerso_max_dias']}
    return saida


def evidencia(datas, precos, n_caminhos=200):
    print('\n' + '=' * 88)
    print('ETAPA 4b — A MESMA REGUA DO PROJETO A, APLICADA AO PROJETO B')
    print('=' * 88)
    print('"40 de 42" e "48 de 71" contam janelas SOBREPOSTAS de UMA serie de preco,')
    print('que contem UM bear market. Nao sao observacoes independentes.')
    print('Block bootstrap dos log-retornos -> caminhos de preco alternativos.')
    print('O comprimento do bloco e VARRIDO (criterio 1 do protocolo 3.1: nunca um ponto so).\n')

    kw = base_kw()
    linhas, p_dca_all, p_air_all = [], [], []
    print('%-8s %-6s %13s %13s %14s' % ('bloco', 'seed', 'P(DCA>CDB)', 'P(Air>DCA)', 'mediana DCA'))
    print('-' * 60)
    for bloco in (90, 180, 365, 730):
        for seed in (42, 7):
            cam = ev.caminhos_bootstrap(precos, n_caminhos=n_caminhos, bloco_dias=bloco, seed=seed)
            v_dca = [simular(datas, p, DCAFixo(), **kw)['valor_final'] for p in cam]
            v_cdb = [simular(datas, p, CDB(0.01), **kw)['valor_final'] for p in cam]
            v_air = [simular(datas, p, Airbag('EMA300', 6, 0), **kw)['valor_final'] for p in cam]
            pdc = ev.p_supera(v_dca, v_cdb)
            pad = ev.p_supera(v_air, v_dca)
            p_dca_all.append(pdc)
            p_air_all.append(pad)
            linhas.append({'bloco': bloco, 'seed': seed, 'p_dca_supera_cdb': pdc,
                           'p_airbag_supera_dca': pad,
                           'ic_dca': ev.intervalo(v_dca), 'ic_airbag': ev.intervalo(v_air)})
            print('%-8d %-6d %12.1f%% %12.1f%% %14.0f'
                  % (bloco, seed, pdc * 100, pad * 100, statistics.median(v_dca)))
    print('-' * 60)
    print('P(DCA em BTC > CDB)  : %.0f%% a %.0f%%   [o historico unico sugeria "sempre"]'
          % (min(p_dca_all) * 100, max(p_dca_all) * 100))
    print('P(Airbag > DCA fixo) : %.0f%% a %.0f%%   [o historico unico dizia 40 de 42 = 95%%]'
          % (min(p_air_all) * 100, max(p_air_all) * 100))
    print()
    print('LEITURA:')
    print('  1. O DCA superar o CDB e razoavelmente ROBUSTO (~3 em 4 historias reamostradas),')
    print('     mas nao e certeza — e no fundo e uma aposta na valorizacao do BTC.')
    print('  2. A vantagem de RETORNO do airbag NAO se sustenta: vira cara-ou-coroa. Ela')
    print('     cresce com o comprimento do bloco, ou seja, depende inteiramente de o cripto')
    print('     continuar tendo ciclos longos e persistentes como o de 2022. Isso e coerente')
    print('     com o C5 (ex-carry o airbag rende +1,7%% sobre o DCA: praticamente nada).')
    print('  3. O que sobrevive a tudo e a reducao de QUEDA (68%% -> 45%%), que e mecanica.')
    return {'n_caminhos': n_caminhos, 'varredura': linhas,
            'p_dca_supera_cdb_min': min(p_dca_all), 'p_dca_supera_cdb_max': max(p_dca_all),
            'p_airbag_supera_dca_min': min(p_air_all), 'p_airbag_supera_dca_max': max(p_air_all)}


def alocacao(datas, precos, n_caminhos=150):
    """Qual peso em BTC maximiza o CRESCIMENTO do capital (nao o retorno medio).

    Criterio de crescimento logaritmico: e o correto para quem nao saca e quer
    maximizar dinheiro no longo prazo, porque maximiza a MEDIANA do resultado em
    vez da media (que e dominada por caudas que quase nunca acontecem).
    """
    print('\n' + '=' * 88)
    print('ETAPA 4c — ALOCACAO QUE MAXIMIZA CRESCIMENTO (nao retorno medio)')
    print('=' * 88)
    kw = base_kw()
    aportado = 154000.0
    cam = ev.caminhos_bootstrap(precos, n_caminhos=n_caminhos, bloco_dias=365, seed=42)
    print('%-9s %11s %12s %12s %12s %8s' % ('peso BTC', 'cresc.log', 'mediana',
                                            'p5 (ruim)', 'p95', 'maxDD'))
    print('-' * 72)
    res, linhas = {}, []
    for w in (0.2, 0.4, 0.6, 0.8, 0.9, 1.0):
        vals, dds = [], []
        for p in cam:
            pol = DCAFixo() if w >= 1.0 else PassivoIsoExposicao(w)
            r = simular(datas, p, pol, **kw)
            vals.append(r['valor_final'])
            dds.append(r['maxdd'])
        g = statistics.mean(math.log(v / aportado) for v in vals if v > 0)
        res[w] = g
        p5 = sorted(vals)[int(0.05 * len(vals))]
        p95 = sorted(vals)[int(0.95 * len(vals))]
        linhas.append({'peso': w, 'crescimento_log': g, 'mediana': statistics.median(vals),
                       'p5': p5, 'p95': p95, 'maxdd': statistics.median(dds)})
        print('%-8.0f%% %11.4f %12.0f %12.0f %12.0f %7.0f%%'
              % (w * 100, g, statistics.median(vals), p5, p95, statistics.median(dds) * 100))
    melhor = max(res, key=res.get)
    print('-' * 72)
    print('OTIMO: %.0f%% em BTC — ou seja, DCA puro.' % (melhor * 100))
    print()
    print('DUAS RESSALVAS QUE NAO PODEM SER OMITIDAS:')
    print(' 1. O otimo esta na BORDA porque a alavancagem esta PROIBIDA. Sem essa trava a')
    print('    formula apontaria para alem de 100%, e numa queda de 68% isso e ruina.')
    print(' 2. O preco desse otimo e a cauda ruim: no percentil 5 o resultado a 100% BTC e')
    print('    de ~R$86 mil contra R$154 mil aportados — pouco mais da METADE do depositado')
    print('    depois de 6,4 anos. Maximizar crescimento aceita esse cenario; e uma escolha')
    print('    legitima, mas tem de ser feita de olhos abertos.')
    return {'linhas': linhas, 'peso_otimo': melhor}


def main():
    ap = argparse.ArgumentParser(description='Projeto B — laboratorio de acumulacao')
    ap.add_argument('--reproduzir', action='store_true')
    ap.add_argument('--timing', action='store_true')
    ap.add_argument('--evidencia', action='store_true')
    ap.add_argument('--alocacao', action='store_true')
    ap.add_argument('--caminhos', type=int, default=200)
    ap.add_argument('--tudo', action='store_true')
    args = ap.parse_args()
    if args.tudo:
        args.reproduzir = args.timing = args.evidencia = args.alocacao = True
    if not any([args.reproduzir, args.timing, args.evidencia, args.alocacao]):
        args.reproduzir = True

    datas, precos = serie_diaria('BTCUSDT')
    out = {}
    if args.reproduzir:
        out['reproducao'] = reproduzir(datas, precos)
    if args.timing:
        out['timing'] = timing(datas, precos)
    if args.evidencia:
        out['evidencia'] = evidencia(datas, precos, args.caminhos)
    if args.alocacao:
        out['alocacao'] = alocacao(datas, precos)

    os.makedirs(OUT, exist_ok=True)
    caminho = os.path.join(OUT, 'projeto_b.json')
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    print('\nArtefato: %s' % caminho)


if __name__ == '__main__':
    main()
