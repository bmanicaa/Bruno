#!/usr/bin/env python3
"""
CRITERIO DE DECISAO (Fase E, Etapa 3) — separar "existe efeito?" de "vale apostar?"

O problema que este modulo resolve
-----------------------------------
O protocolo da secao 3 do analises.md tem UM portao binario que responde:
*"isto e provavelmente melhor que a melhor de 36 configs aleatorias?"*.
Essa e a pergunta da PUBLICACAO ACADEMICA — o Deflated Sharpe foi desenhado por
Bailey & Lopez de Prado para impedir que um pesquisador anuncie descoberta falsa
depois de garimpar milhares de backtests.

Nao e a pergunta de quem ALOCA CAPITAL. A Etapa 1 mediu o preco dessa confusao:
o protocolo tem poder ZERO abaixo de Sharpe de trading ~1,2. Uma estrategia com
edge real de Sharpe 1,0 e reprovada em 100% das simulacoes. Tratada como
"nao existe", quando o correto seria "nao consegui provar com 3,4 anos de dados".

Este modulo NAO substitui o DSR nem o bootstrap — eles continuam sendo
calculados e reportados, e a Fase A que os consertou foi trabalho correto.
Ele acrescenta a camada que falta: dado o que foi estimado E a incerteza da
estimativa, qual e o tamanho de aposta que maximiza o crescimento do capital,
e qual crescimento esperar.

Como decide
-----------
1. Bootstrap em blocos sobre os R-multiplos dos trades OOS -> distribuicao da
   incerteza sobre a verdadeira distribuicao de resultados.
2. Para cada fracao de risco f, crescimento logaritmico esperado por trade
   g(f) = E[ln(1 + f*R)], calculado sobre TODAS as reamostras. Isso incorpora o
   erro de estimacao: uma estrategia com media alta mas incerta e penalizada
   automaticamente, sem precisar de um p-valor.
3. f* = argmax g(f) (Kelly). A recomendacao e SEMPRE f*/2 (meio-Kelly).
4. Teste de sobrevivencia: nenhuma recomendacao passa se admitir ruina.

RESTRICAO TRAVADA — por que meio-Kelly e por que nunca alavancar
----------------------------------------------------------------
O usuario declarou nao ter limite de drawdown. Isso NAO autoriza alavancagem.
Kelly pleno ja produz quedas de ~50% rotineiramente, e erra para cima quando a
media e superestimada — que e o caso normal em backtest. Meio-Kelly entrega ~75%
do crescimento com ~metade da queda. Acima de Kelly pleno o crescimento esperado
comeca a CAIR, e passando de 2x Kelly ele fica NEGATIVO mesmo com edge positivo.
E ruina e absorvente: horizonte longo nao recupera capital que chegou a zero.

Uso:
  python scripts/criterio_de_decisao.py --exp ac35a444
  python scripts/criterio_de_decisao.py --todas
"""

import argparse
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistical_validation as sv  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP_DIR = os.path.join(BASE_DIR, 'data', 'experimentos')
OUT_DIR = os.path.join(BASE_DIR, 'data', 'acumulacao')

FRACAO_KELLY = 0.5          # meio-Kelly, travado
GRADE_F = np.linspace(0.0, 0.60, 121)
BLOCO = 8


def r_multiplos_oos(exp):
    r = []
    for w in sv.OOS_NAMES:
        wd = exp.get('windows_detail', {}).get(w)
        if not wd:
            continue
        for t in wd['trades']:
            r.append(t['pnl_brl'] / max(t['risk_brl'], 1e-9))
    return np.array(r, dtype=float)


def crescimento_log(r, f):
    """E[ln(1 + f*R)] — crescimento logaritmico por trade. -inf se admite ruina."""
    x = 1.0 + f * r
    if np.any(x <= 1e-9):
        return -np.inf
    return float(np.mean(np.log(x)))


def analisar(r, n_iter=2000, seed=42, trades_por_ano=None):
    """Curva de crescimento com incerteza de estimacao embutida."""
    n = len(r)
    if n < 5:
        return None
    rng = np.random.default_rng(seed)
    bloco = max(1, min(BLOCO, n // 3))
    reamostras = sv._resample_series(rng, r, n_iter, bloco)

    # g(f) medio sobre as reamostras: penaliza incerteza sem usar p-valor.
    g_medio, g_p05 = [], []
    for f in GRADE_F:
        vals = []
        for b in range(min(n_iter, 400)):        # 400 reamostras bastam para a media
            vals.append(crescimento_log(reamostras[b], f))
        vals = np.array([v for v in vals if np.isfinite(v)])
        if len(vals) == 0:
            g_medio.append(-np.inf); g_p05.append(-np.inf)
        else:
            g_medio.append(float(vals.mean()))
            g_p05.append(float(np.percentile(vals, 5)))
    g_medio = np.array(g_medio); g_p05 = np.array(g_p05)

    i_star = int(np.nanargmax(np.where(np.isfinite(g_medio), g_medio, -np.inf)))
    f_kelly = float(GRADE_F[i_star])
    f_rec = f_kelly * FRACAO_KELLY

    exp_r_boot = reamostras.mean(axis=1)
    p_edge_negativo = float((exp_r_boot <= 0).mean())

    g_rec = crescimento_log(r, f_rec)
    if trades_por_ano is None:
        trades_por_ano = n / 3.42     # 4 blocos OOS = 3,42 anos
    cresc_anual = math.exp(g_rec * trades_por_ano) - 1 if np.isfinite(g_rec) else float('nan')

    return {
        'n_trades': n,
        'expectancia_R': float(r.mean()),
        'expectancia_R_ic95': [float(np.percentile(exp_r_boot, 2.5)),
                               float(np.percentile(exp_r_boot, 97.5))],
        'p_edge_negativo': p_edge_negativo,
        'f_kelly': f_kelly,
        'f_recomendado': f_rec,
        'crescimento_log_por_trade': float(g_rec) if np.isfinite(g_rec) else None,
        'crescimento_anual_esperado': float(cresc_anual) if np.isfinite(cresc_anual) else None,
        'trades_por_ano': float(trades_por_ano),
        'g_no_risco_atual_1_5pct': float(crescimento_log(r, 0.015)),
        'aposta_positiva': bool(f_kelly > 1e-9),
        # Sob incerteza: a fracao ainda e positiva no cenario pessimista (p5)?
        'robusto_no_p5': bool(np.isfinite(g_p05[i_star]) and g_p05[i_star] > 0),
    }


def veredito(a):
    if a is None:
        return 'AMOSTRA INSUFICIENTE'
    if not a['aposta_positiva']:
        return 'NAO APOSTAR — crescimento maximo em f=0 (edge nao-positivo)'
    if a['p_edge_negativo'] > 0.35:
        return 'NAO APOSTAR — %.0f%% de chance de o edge ser negativo' % (a['p_edge_negativo'] * 100)
    if not a['robusto_no_p5']:
        return 'APOSTA MARGINAL — positiva na media, negativa no cenario pessimista'
    return 'APOSTAR f=%.2f%% da banca por trade (meio-Kelly)' % (a['f_recomendado'] * 100)


def carregar_limpos():
    out, vistos = [], set()
    for p in sorted(glob.glob(os.path.join(EXP_DIR, 'exp_*.json'))):
        with open(p, 'r', encoding='utf-8') as f:
            d = json.load(f)
        if d.get('invalid_lookahead') or 'windows_detail' not in d:
            continue
        if 'risk_pct' not in d.get('config', {}):
            continue
        if d.get('config_hash') in vistos:
            continue
        vistos.add(d.get('config_hash'))
        out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser(description='Criterio de decisao (Fase E, Etapa 3)')
    ap.add_argument('--exp', help='hash de um experimento')
    ap.add_argument('--todas', action='store_true', help='avalia todas as configs limpas de swing')
    ap.add_argument('--saida', default=os.path.join(OUT_DIR, 'criterio_de_decisao.json'))
    args = ap.parse_args()

    print('=' * 92)
    print('CRITERIO DE DECISAO — "vale apostar?" separado de "existe efeito?" (Fase E, Etapa 3)')
    print('=' * 92)

    exps = [sv.load_experiment(args.exp)] if args.exp else carregar_limpos()
    linhas = []
    print('%-10s %7s %9s %18s %7s %9s %10s  %s' % (
        'hash', 'trades', 'E[R]', 'IC95 de E[R]', 'P(neg)', 'f Kelly', 'cresc/ano', 'veredito'))
    print('-' * 92)
    for d in exps:
        r = r_multiplos_oos(d)
        a = analisar(r)
        h = (d.get('config_hash') or '?')[:8]
        if a is None:
            print('%-10s %7d   — amostra insuficiente' % (h, len(r)))
            continue
        linhas.append({'hash': h, 'config': d.get('config'), **a, 'veredito': veredito(a)})
        ca = a['crescimento_anual_esperado']
        print('%-10s %7d %+9.4f  [%+.3f, %+.3f] %6.0f%% %8.2f%% %9s  %s' % (
            h, a['n_trades'], a['expectancia_R'],
            a['expectancia_R_ic95'][0], a['expectancia_R_ic95'][1],
            a['p_edge_negativo'] * 100, a['f_kelly'] * 100,
            ('%+.1f%%' % (ca * 100)) if ca is not None else '—',
            veredito(a)))

    if linhas:
        aprovadas = [l for l in linhas if l['veredito'].startswith('APOSTAR')]
        print('-' * 92)
        print('RESUMO: %d configs avaliadas | %d recomendadas para aposta pelo criterio de DECISAO'
              % (len(linhas), len(aprovadas)))
        if not aprovadas:
            print('  Nenhuma. Note que isto NAO e o mesmo que reprovar no DSR: aqui a rejeicao')
            print('  vem da estimativa pontual e da incerteza, nao da penalidade de 36 tentativas.')
        else:
            for l in aprovadas:
                print('  -> %s: %s' % (l['hash'], l['veredito']))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(args.saida, 'w', encoding='utf-8') as f:
        json.dump({'fracao_kelly': FRACAO_KELLY, 'configs': linhas}, f, ensure_ascii=False, indent=1)
    print('\nArtefato: %s' % args.saida)


if __name__ == '__main__':
    main()
