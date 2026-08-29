"""
Motor do cash-and-carry. Loop diario deterministico, zero lookahead.

ESTRUTURA MEDIDA
    Por simbolo: comprado q unidades no SPOT + vendido q unidades no PERPETUO.
    Contrato linear (margem em USDT), logo o delta em moeda e EXATAMENTE zero
    com quantidades casadas — nao ha deriva de delta por construcao. O que
    deriva e (i) o notional em relacao ao patrimonio, conforme o funding entra
    no caixa e o preco anda, e (ii) a razao de margem da perna vendida. E isso
    que a politica de rebalanceio administra. Rebalancear "o delta" num
    perpetuo linear seria rebalancear um numero que vale zero.

CAUSALIDADE (travada por teste em tests/test_carry.py)
    A decisao do dia D usa apenas informacao com timestamp < D 00:00:
      * precos: fechamento da vela diaria de D-1 (que E o preco as 00:00 de D);
      * funding do gatilho: settlements ate D-1 23:59:59;
      * ranking de liquidez: volume ate D-1.
    A execucao ocorre ao preco de D-1 (o preco vigente no instante da decisao).
    O funding remunerado no dia D vem da janela (D 00:00, D+1 00:00] — toda
    ela POSTERIOR aa decisao.

ORDEM DENTRO DO DIA (conservadora de proposito)
    1. decisao + execucao (taxas e slippage nas duas pernas)
    2. checagem de margem/liquidacao contra a MAXIMA do dia
    3. funding creditado apenas as posicoes que sobreviveram ao passo 2
    4. juro do caixa livre
    5. marcacao a mercado no fechamento do dia
    O passo 2 antes do 3 e pessimista: uma posicao liquidada as 10:00 perde
    todo o funding do dia, inclusive o das 08:00 que ja teria recebido.

IDENTIDADE CONTABIL (travada por teste)
    patrimonio_final - capital_inicial
        = funding + base - custos + juros
    O residuo e reportado; se nao for ~0, o motor esta errado, nao a estrategia.
"""
import datetime as dt
import hashlib
import json

from . import custos as C
from . import dados as D

CAPITAL_PADRAO = 100_000.0


# --------------------------------------------------------------------------
# Configuracao
# --------------------------------------------------------------------------

CESTAS = {'BTC': 1, 'BTC_ETH': 2, 'TOP5': 5, 'TOP10': 10, 'TOP20': 20}


def config_padrao(**kw):
    cfg = {
        'cesta': 'BTC',
        'gatilho': ('sempre',),          # ou ('funding', K_dias, limiar)
        'alavancagem': 1,
        'rebalanceio': ('semanal',),     # ('diario',) ('semanal',) ('limiar', X)
        'base_modo': 'premium',
        'politica_margem': 'aportar',    # ou 'liquidar'
        # Nivel de patrimonio isolado (em fracao da margem inicial) que dispara
        # o aporte. 0.5 = repoe quando ja perdeu metade do colchao. Esperar a
        # margem de MANUTENCAO (0,4%) seria esperar o caixao: nesse ponto o
        # aporte necessario e a margem inicial inteira, sempre maior que a
        # reserva, e o modo 'aportar' degenera em 'liquidar' — foi o que este
        # motor fez antes da correcao (zero aportes em 2.538 dias).
        'gatilho_margem': 0.5,
        # Slippage EXTRA na desmontagem forcada da perna comprada apos uma
        # liquidacao: e execucao em mercado estressado, nao em livro normal.
        'slippage_estresse': 0.0010,
        'taxa': C.TAXA_PADRAO,
        'slippage': C.SLIPPAGE_PADRAO,
        'mmr': C.MMR_PADRAO,
        'juro_mensal': 0.01,             # CDI de referencia do projeto
        'fracao_capital': 0.90,          # 10% de reserva para chamada de margem
        'capital': CAPITAL_PADRAO,
        'inicio': dt.date(2019, 9, 10),
        'fim': dt.date(2026, 8, 22),
    }
    desconhecidas = set(kw) - set(cfg)
    if desconhecidas:
        raise KeyError(f'parametros desconhecidos: {sorted(desconhecidas)}')
    cfg.update(kw)
    return cfg


def hash_config(cfg):
    """Hash estavel da configuracao. Vai no artefato, como no Projeto A."""
    def norm(v):
        if isinstance(v, dt.date):
            return v.isoformat()
        if isinstance(v, (tuple, list)):
            return [norm(x) for x in v]
        return v
    payload = json.dumps({k: norm(v) for k, v in sorted(cfg.items())},
                         sort_keys=True, separators=(',', ':'))
    return hashlib.sha1(payload.encode('utf-8')).hexdigest()[:8]


# --------------------------------------------------------------------------
# Universo point-in-time
# --------------------------------------------------------------------------

def universo_pit(candidatos, datas, n, janela=30):
    """Ranking de liquidez revisto no 1o dia de cada mes, sempre com passado.

    Devolve dict data -> lista dos n simbolos vigentes naquele dia.

    Revisao MENSAL, nao diaria: um ranking diario trocaria de cesta a cada
    solavanco de volume e o resultado viraria uma medida de custo de giro. A
    janela de 30 dias e estritamente anterior ao dia da revisao, entao nenhuma
    escolha enxerga o proprio dia que vai negociar.
    """
    if not datas:
        return {}
    revisoes = []
    vista = set()
    for d in datas:
        chave = (d.year, d.month)
        if chave not in vista:
            vista.add(chave)
            revisoes.append(d)

    escolha_por_revisao = {}
    for d in revisoes:
        ranking = []
        for s in candidatos:
            v = D.liquidez_mediana(s, d, janela)
            if v > 0:
                ranking.append((v, s))
        ranking.sort(reverse=True)
        escolha_por_revisao[d] = [s for _, s in ranking[:n]]

    saida, atual = {}, []
    idx = 0
    for d in datas:
        if idx < len(revisoes) and d == revisoes[idx]:
            atual = escolha_por_revisao[revisoes[idx]]
            idx += 1
        saida[d] = atual
    return saida


def _cesta_fixa(cfg):
    if cfg['cesta'] == 'BTC':
        return ['BTCUSDT']
    if cfg['cesta'] == 'BTC_ETH':
        return ['BTCUSDT', 'ETHUSDT']
    return None


# --------------------------------------------------------------------------
# Gatilho
# --------------------------------------------------------------------------

def _media_funding_passada(serie, datas, k_dias):
    """Media da taxa por settlement nos k dias ANTERIORES a cada data.

    Implementado como soma corrida sobre dias ja fechados: o valor associado ao
    dia D usa a janela [D-k, D-1]. Nunca inclui D.
    """
    saida = {}
    acum_t = acum_n = 0.0
    fila = []
    for d in datas:
        saida[d] = (acum_t / acum_n) if acum_n > 0 else None
        v = serie.get(d)
        fila.append((v['soma_taxa'], v['n_settle']) if v else (0.0, 0))
        acum_t += fila[-1][0]
        acum_n += fila[-1][1]
        if len(fila) > k_dias:
            velho = fila.pop(0)
            acum_t -= velho[0]
            acum_n -= velho[1]
    return saida


# --------------------------------------------------------------------------
# Motor
# --------------------------------------------------------------------------

def simular(cfg, series=None, calendario=None, universo=None,
            guardar_curva=True):
    """Executa uma configuracao. Devolve dict com patrimonio, decomposicao e eventos."""
    cfg = dict(cfg)
    L = cfg['alavancagem']
    taxa, slip, mmr = cfg['taxa'], cfg['slippage'], cfg['mmr']
    juro_dia = C.juro_diario(cfg['juro_mensal'])
    custo_ida = taxa + slip                      # por perna, por lado

    base_fn = (lambda f: C.base_por_dia(f, cfg['base_modo']))
    fixa = _cesta_fixa(cfg)

    # ---- calendario mestre: dias em que o BTC negociou ----
    if calendario is None:
        btc = D.serie_por_dia('BTCUSDT', base_fn)
        calendario = sorted(d for d in btc if cfg['inicio'] <= d <= cfg['fim'])
    datas = [d for d in calendario if cfg['inicio'] <= d <= cfg['fim']]
    if len(datas) < 2:
        raise ValueError('janela curta demais')

    # ---- universo ----
    if fixa is not None:
        simbolos = list(fixa)
        universo = {d: simbolos for d in datas}
    elif universo is None:
        n = CESTAS[cfg['cesta']]
        universo = universo_pit(D.simbolos_disponiveis(), datas, n)
        simbolos = sorted({s for v in universo.values() for s in v})
    else:
        simbolos = sorted({s for v in universo.values() for s in v})

    if series is None:
        series = {s: D.serie_por_dia(s, base_fn) for s in simbolos}
    else:
        series = {s: series[s] for s in simbolos if s in series}
        simbolos = [s for s in simbolos if s in series]

    # ---- gatilho pre-computado (so passado) ----
    gat = cfg['gatilho']
    if gat[0] == 'sempre':
        media_passada = None
        limiar = None
    else:
        _, k_dias, limiar = gat
        media_passada = {s: _media_funding_passada(series[s], datas, k_dias)
                         for s in simbolos}

    # ---- estado ----
    caixa = cfg['capital']
    capital_inicial = cfg['capital']
    pos = {}          # sym -> dict(q, F_ent, S_ent, margem)
    funding_acum = 0.0
    base_realizada = 0.0
    custos_acum = 0.0
    juros_acum = 0.0

    n_entradas = n_saidas = n_rebal = 0
    n_aportes = 0
    valor_aportes = 0.0
    n_desmontes = 0
    quebra_hedge = 0.0
    n_liquidacoes = 0
    perda_liquidacao = 0.0
    dias_com_posicao = 0
    notional_dia = []
    imobilizado_dia = 0.0
    curva = []
    reb = cfg['rebalanceio']
    ultimo_rebal = None

    def preco(s, d):
        v = series[s].get(d)
        return None if v is None else v['close']

    def base(s, d):
        v = series[s].get(d)
        return 0.0 if v is None else v['base']

    def fechar(s, F, S):
        """Desmonta as duas pernas ao preco de execucao dado."""
        nonlocal caixa, custos_acum, base_realizada, n_saidas
        p = pos.pop(s)
        q = p['q']
        # perna comprada: vende spot
        caixa += q * S
        custos_acum += q * S * custo_ida
        caixa -= q * S * custo_ida
        # perna vendida: recompra perpetuo, devolve margem + PnL
        pnl_perp = q * (p['F_ent'] - F)
        caixa += p['margem'] + pnl_perp
        custos_acum += q * F * custo_ida
        caixa -= q * F * custo_ida
        base_realizada += q * (S - p['S_ent']) + pnl_perp
        n_saidas += 1

    def abrir(s, F, S, notional_alvo):
        """Monta as duas pernas. notional_alvo e o tamanho da perna comprada."""
        nonlocal caixa, custos_acum, n_entradas
        if notional_alvo <= 0 or F <= 0 or S <= 0:
            return
        # Capital consumido por unidade de notional comprado: o spot (1), a
        # margem da perna vendida (F/S/L) e o custo de montar as duas pernas.
        por_notional = 1.0 + (F / S) / L + custo_ida * (1.0 + F / S)
        notional = min(notional_alvo, max(0.0, caixa / por_notional))
        if notional <= 1e-9:
            return
        q = notional / S
        margem = C.margem_requerida(q * F, L)
        c = q * S * custo_ida + q * F * custo_ida
        caixa -= notional + margem + c
        custos_acum += c
        pos[s] = {'q': q, 'F_ent': F, 'S_ent': S, 'margem': margem}
        n_entradas += 1

    def ajustar(s, F, S, notional_alvo):
        """Leva a posicao ao notional alvo negociando SO A DIFERENCA.

        Fechar e reabrir a posicao inteira a cada rebalanceio custaria 4 pernas
        de taxa+slippage por evento. Num carry que colhe ~1 bp por settlement,
        essa escolha de implementacao sozinha decide o veredito: media a
        estrategia errada e a reprova por um custo que ninguem pagaria.
        Um operador negocia o delta. O motor tambem.
        """
        nonlocal caixa, custos_acum, base_realizada, n_saidas
        p = pos[s]
        q_alvo = max(0.0, notional_alvo / S)
        dq = q_alvo - p['q']

        if dq > 0:
            # limita o aumento ao caixa disponivel
            por_q = S + (F / L) + custo_ida * (S + F)
            dq = min(dq, max(0.0, caixa / por_q)) if por_q > 0 else 0.0
            if dq * S > 1e-9:
                c = dq * S * custo_ida + dq * F * custo_ida
                caixa -= dq * S + c
                custos_acum += c
                p['F_ent'] = (p['q'] * p['F_ent'] + dq * F) / (p['q'] + dq)
                p['S_ent'] = (p['q'] * p['S_ent'] + dq * S) / (p['q'] + dq)
                p['q'] += dq
        elif dq < 0:
            f = min(-dq, p['q'])
            if f * S > 1e-9:
                pnl_perp = f * (p['F_ent'] - F)
                c = f * S * custo_ida + f * F * custo_ida
                caixa += f * S + pnl_perp + p['margem'] * (f / p['q']) - c
                custos_acum += c
                base_realizada += f * (S - p['S_ent']) + pnl_perp
                p['margem'] -= p['margem'] * (f / p['q'])
                p['q'] -= f
                if p['q'] * S <= 1e-9:
                    caixa += p['margem']
                    pos.pop(s)
                    n_saidas += 1
                    return
        # Margem levada ao alvo. O alvo e o PATRIMONIO ISOLADO da perna
        # vendida, nao a margem bruta:
        #
        #     eq_isolado = margem + q*(F_ent - F)
        #
        # Um short aberto a 12k com o preco em 47k carrega prejuizo nao
        # realizado de q*35k; mirar "margem = q*F/L" deixaria esse buraco
        # descoberto e a posicao seria liquidada com margem tres vezes maior
        # que o notional — foi exatamente o que este motor fez antes da
        # correcao. E a mesma regra do passo 2 (aporte), e ter as duas
        # divergindo era o defeito.
        #
        # Consequencia economica, que e o ponto: numa alta forte a perna
        # vendida SUGA caixa continuamente, enquanto o ganho equivalente da
        # perna comprada so vira dinheiro quando o spot e vendido. Carry em
        # bull market e uma maquina de consumir margem.
        eq_iso = p['margem'] + p['q'] * (p['F_ent'] - F)
        delta_m = C.margem_requerida(p['q'] * F, L) - eq_iso
        if delta_m > 0:
            delta_m = min(delta_m, max(0.0, caixa))
        caixa -= delta_m
        p['margem'] += delta_m

    for i, d in enumerate(datas):
        d_ant = datas[i - 1] if i > 0 else None

        # ================= 1. DECISAO (informacao < d 00:00) =================
        # Precos de execucao: fechamento de d-1, que E o preco as 00:00 de d.
        if d_ant is not None:
            alvo = set(universo.get(d, []))
            if media_passada is not None:
                alvo = {s for s in alvo
                        if media_passada[s].get(d) is not None
                        and media_passada[s][d] > limiar}
            alvo = {s for s in alvo
                    if preco(s, d_ant) is not None and preco(s, d) is not None}

            # -- saidas: fora do universo/gatilho, ou serie encerrada --
            for s in list(pos):
                F_ex = preco(s, d_ant)
                if F_ex is None:
                    ult = max((x for x in series[s] if x < d), default=None)
                    if ult is None:
                        caixa += pos.pop(s)['margem']
                        continue
                    v = series[s][ult]
                    fechar(s, v['close'], C.preco_spot(v['close'], v['base']))
                elif s not in alvo:
                    fechar(s, F_ex, C.preco_spot(F_ex, base(s, d_ant)))

            patrimonio = _patrimonio(caixa, pos, series, d_ant)
            n_alvo = len(alvo)
            notional_alvo = (patrimonio * cfg['fracao_capital'] /
                             (n_alvo * (1.0 + 1.0 / L))) if n_alvo else 0.0

            # Mudanca de composicao forca rebalanceio: entrar num simbolo novo
            # sem encolher os outros estouraria a alocacao.
            composicao_mudou = (alvo != set(pos))
            if reb[0] == 'diario':
                toca = True
            elif reb[0] == 'semanal':
                toca = (ultimo_rebal is None or (d - ultimo_rebal).days >= 7)
            else:
                desvios = [abs(pos[s]['q'] * C.preco_spot(preco(s, d_ant),
                                                          base(s, d_ant))
                               / notional_alvo - 1.0)
                           for s in pos] if notional_alvo > 0 else []
                toca = (ultimo_rebal is None or
                        (bool(desvios) and max(desvios) > reb[1]))
            toca = toca or composicao_mudou

            if toca and n_alvo:
                for s in sorted(alvo):
                    F = preco(s, d_ant)
                    S = C.preco_spot(F, base(s, d_ant))
                    if s in pos:
                        ajustar(s, F, S, notional_alvo)
                    else:
                        abrir(s, F, S, notional_alvo)
                n_rebal += 1
                ultimo_rebal = d

        # ================= 2. MARGEM E LIQUIDACAO (maxima de d) =============
        # Testada contra a MAXIMA do dia, nao contra o fechamento: a liquidacao
        # e intrabar. Ainda assim esta e uma granularidade DIARIA — um pavio
        # intradiario que sobe e volta dentro do mesmo dia e capturado, mas a
        # ordem dos eventos dentro do dia nao. O numero de liquidacoes aqui e
        # um PISO, nao um teto.
        for s in list(pos):
            v = series[s].get(d)
            if v is None:
                continue
            p = pos[s]
            H = v['high']
            eq_h = p['margem'] + p['q'] * (p['F_ent'] - H)   # patrimonio isolado
            manut = C.margem_de_manutencao(p['q'] * H, mmr)
            alvo_m = p['q'] * H / L

            if cfg['politica_margem'] == 'aportar':
                if eq_h > cfg['gatilho_margem'] * alvo_m:
                    continue
                falta = alvo_m - eq_h
                if falta <= caixa:
                    caixa -= falta
                    p['margem'] += falta
                    n_aportes += 1
                    valor_aportes += falta
                    continue
                if eq_h > manut:
                    # Sem caixa para o aporte, mas ainda vivo: desmonta a
                    # estrutura INTEIRA no fechamento, com o hedge intacto.
                    # E o que um operador que acompanha a posicao faz — e o
                    # custo disso e so taxa+slippage, nao a perda do colchao.
                    F_d = v['close']
                    fechar(s, F_d, C.preco_spot(F_d, v['base']))
                    n_desmontes += 1
                    continue
            elif eq_h > manut:
                continue

            # ---- liquidacao: o colchao acabou ----
            P_liq = C.preco_liquidacao(p['margem'], p['q'], p['F_ent'], mmr)
            q = p['q']
            S_liq = C.preco_spot(P_liq, v['base'])
            # ate P_liq o hedge estava intacto: isso e base, como qualquer
            # outro fechamento.
            base_realizada += q * (S_liq - p['S_ent']) + q * (p['F_ent'] - P_liq)
            # o que sobra da margem a corretora retem como taxa de liquidacao
            custos_acum += max(0.0, p['margem'] + q * (p['F_ent'] - P_liq))
            perda_liquidacao += p['margem']
            n_liquidacoes += 1
            # DEPOIS de P_liq a perna comprada fica descoberta. Modelamos o
            # operador refazendo a neutralidade NO PROPRIO preco de liquidacao,
            # com slippage de estresse — nao carregando o spot descoberto ate o
            # fechamento do dia.
            #
            # POR QUE ISSO IMPORTA MAIS DO QUE PARECE. A versao anterior deste
            # motor desmontava o spot no fechamento do dia, e o resultado foi
            # que as 8 melhores configuracoes do grid tiravam ~91% do lucro
            # desse trecho: liquidava a perna vendida numa alta, ficava
            # comprada em BTC sem hedge e o preco seguia subindo. R$1,36 milhao
            # de R$1,49 milhao vinham dali. Isso nao e carry — e uma posicao
            # direcional adquirida por acidente, exatamente o que a tarefa
            # exclui, e enviesada para cima porque liquidacao so acontece em
            # alta forte. Fechar em P_liq elimina o vies pela raiz: o custo da
            # liquidacao passa a ser o que ele de fato e (o colchao perdido
            # mais a execucao ruim), sem premio direcional nenhum embutido.
            custo_estresse = q * S_liq * (custo_ida + cfg['slippage_estresse'])
            caixa += q * S_liq - custo_estresse
            custos_acum += q * S_liq * custo_ida
            quebra_hedge -= q * S_liq * cfg['slippage_estresse']
            pos.pop(s)
            n_saidas += 1

        # ================= 3. FUNDING (janela (d 00:00, d+1 00:00]) =========
        for s, p in pos.items():
            v = series[s].get(d)
            if v is None or not v['n_settle']:
                continue
            F_ref = series[s][d_ant]['close'] if (d_ant and d_ant in series[s]) \
                else v['close']
            recebido = p['q'] * F_ref * v['fator']   # short recebe se taxa > 0
            caixa += recebido
            funding_acum += recebido

        # ---- capital imobilizado hoje (spot + margem): nao rende NADA ----
        # Nao entra na identidade contabil; e o diagnostico do item (d) do
        # protocolo. O que rende CDI e so o caixa livre; tudo que esta preso
        # em spot e em margem esta deixando de render, e essa e a conta que
        # separa "carry" de "CDI com passos extras".
        imobilizado_dia += sum(
            p['q'] * (series[s][d]['close'] if d in series[s] else p['F_ent'])
            / (1.0 + (series[s][d]['base'] if d in series[s] else 0.0))
            + p['margem'] for s, p in pos.items())

        # ================= 4. JURO DO CAIXA LIVRE ===========================
        j = caixa * juro_dia
        caixa += j
        juros_acum += j

        # ================= 5. MARCACAO A MERCADO ============================
        eq = _patrimonio(caixa, pos, series, d)
        if guardar_curva:
            curva.append((d, eq))
        if pos:
            dias_com_posicao += 1
            notional_dia.append(sum(p['q'] * (series[s][d]['close']
                                              if d in series[s] else p['F_ent'])
                                    for s, p in pos.items()) / eq if eq > 0 else 0.0)
        else:
            notional_dia.append(0.0)

    # ---- fechamento final ----
    d_fim = datas[-1]
    for s in list(pos):
        v = series[s].get(d_fim)
        if v is None:
            pos.pop(s)
            continue
        fechar(s, v['close'], C.preco_spot(v['close'], v['base']))
    patrimonio_final = caixa

    base_acum = base_realizada
    residuo = (patrimonio_final - capital_inicial
               - (funding_acum + base_acum - custos_acum + juros_acum
                  + quebra_hedge))

    anos = (datas[-1] - datas[0]).days / 365.25
    cagr = (patrimonio_final / capital_inicial) ** (1 / anos) - 1 if anos > 0 else 0.0

    return {
        'hash': hash_config(cfg),
        'config': cfg,
        'patrimonio_final': patrimonio_final,
        'capital_inicial': capital_inicial,
        'retorno_total': patrimonio_final / capital_inicial - 1.0,
        'cagr': cagr,
        'anos': anos,
        'dias': len(datas),
        'inicio': datas[0], 'fim': datas[-1],
        # --- decomposicao (protocolo, item 3) ---
        'a_funding': funding_acum,
        'b_base': base_acum,
        'c_custos': -custos_acum,
        'd_juros': juros_acum,
        'f_quebra_hedge': quebra_hedge,
        # CDI que o capital preso em spot+margem deixou de render. Diagnostico,
        # nao termo da identidade: e o custo de oportunidade do item (d).
        'custo_oportunidade_margem': imobilizado_dia * juro_dia,
        'capital_imobilizado_medio': imobilizado_dia / len(datas),
        'e_residuo': residuo,
        # --- eventos ---
        'n_entradas': n_entradas, 'n_saidas': n_saidas, 'n_rebalanceios': n_rebal,
        'n_aportes_margem': n_aportes, 'valor_aportes_margem': valor_aportes,
        'n_liquidacoes': n_liquidacoes, 'perda_em_liquidacao': perda_liquidacao,
        'n_desmontes_forcados': n_desmontes,
        'dias_com_posicao': dias_com_posicao,
        'exposicao_media': (sum(notional_dia) / len(notional_dia)) if notional_dia else 0.0,
        'simbolos': simbolos,
        'curva': curva,
    }


def _patrimonio(caixa, pos, series, d):
    """caixa + spot marcado + margem + PnL nao realizado da perna vendida."""
    eq = caixa
    for s, p in pos.items():
        v = series[s].get(d)
        if v is None:
            eq += p['q'] * p['S_ent'] + p['margem']
            continue
        F = v['close']
        eq += p['q'] * C.preco_spot(F, v['base']) + p['margem'] + p['q'] * (p['F_ent'] - F)
    return eq
