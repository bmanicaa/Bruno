"""
Custos, base e margem. Nada implicito: cada centavo tem uma linha.

Tres coisas moram aqui, e todas as tres foram motivo de erro caro em algum
lugar deste repositorio ou do mercado:

1. TAXAS E SLIPPAGE NAS DUAS PERNAS. Carry e a estrategia com a maior razao
   custo/retorno que existe: colhe ~1 bp por settlement e paga ~15 bps para
   montar. Cobrar so uma perna dobraria o resultado.

2. A BASE (perp/spot - 1). Nao ha serie de spot no repositorio (as klines sao
   do perpetuo, ver dados.py). Em vez de assumir base zero em silencio, ela e
   RECONSTRUIDA da propria formula de funding da Binance, que e inversivel.

3. MARGEM E LIQUIDACAO. A perna vendida e isolada: mesmo com o conjunto
   delta-neutro no azul, o short sozinho pode ser liquidado numa alta forte.
"""
import datetime as dt

DIAS_MES = 30.4375

# --- custos de execucao ---------------------------------------------------
# Mesma escala do motor do Projeto A (backtest_institucional.py linhas 67-69),
# para que a comparacao carry x swing seja feita com a mesma regua.
TAXA_PADRAO = 0.00075       # 0,075% por perna, por lado (taker)
SLIPPAGE_PADRAO = 0.0005    # 5 bps

# --- margem ---------------------------------------------------------------
# Taxa de margem de manutencao do primeiro tier de BTCUSDT na Binance.
MMR_PADRAO = 0.004

# --- formula de funding da Binance ---------------------------------------
# funding = premium + clamp(juro - premium, -0.05%, +0.05%),  juro = 0.01%/8h
JURO_FORMULA = 0.0001
CLAMP_FORMULA = 0.0005


def premium_index(taxa):
    """Inverte a formula de funding da Binance para recuperar o premium index.

    A formula publicada e:

        funding = premium + clamp(juro - premium, -0.05%, +0.05%)

    com juro = 0.01% por 8h. Ela e continua e linear por partes:

        premium < -0.04%          -> funding = premium + 0.05%
        -0.04% <= premium <= 0.06% -> funding = 0.01%   (banda morta)
        premium > 0.06%           -> funding = premium - 0.05%

    Logo a inversao e exata FORA da banda morta e CENSURADA dentro dela.
    Devolve None quando censurada — quem chama decide o que fazer com a
    incerteza, e o grid varre essa escolha.

    Evidencia de que a formula vale nesta amostra: 35,4% dos 7.616 settlements
    do BTCUSDT valem EXATAMENTE +0,010000%. Um ponto de massa desse tamanho num
    valor especifico so existe por causa da banda morta. Ou seja: um terco do
    "carry" do BTC nao e premio de mercado nenhum — e a constante de juro da
    formula da corretora.
    """
    if abs(taxa - JURO_FORMULA) < 1e-12:
        return None
    if taxa > JURO_FORMULA:
        return taxa + CLAMP_FORMULA
    return taxa - CLAMP_FORMULA


def base_por_dia(fund, modo='premium', ms_hora=3_600_000):
    """Serie diaria da base (perp/spot - 1) a partir dos settlements.

    modos:
      'zero'      base sempre 0 — spot e perp negociam no mesmo preco.
                  E a hipotese otimista: zera o termo (b) da decomposicao.
      'premium'   base = premium index invertido; censurado -> 0 (centro
                  aproximado da banda morta [-0,04%, +0,06%]).
      'pessimista' censurado -> +0,06%: sempre a ponta da banda que MAIS
                  machuca quem monta o carry (entra pagando premio cheio).

    A base de um dia usa o ULTIMO settlement daquele dia, que e o premio
    vigente quando o dia fecha — e o preco pelo qual a posicao e marcada.
    """
    if modo not in ('zero', 'premium', 'pessimista'):
        raise ValueError(f'modo de base desconhecido: {modo}')
    if modo == 'zero':
        return {}
    censurado = 0.0 if modo == 'premium' else 0.0006
    saida = {}
    for t, taxa in fund:
        d = dt.datetime.fromtimestamp((round(t / ms_hora) * ms_hora - 1) / 1000,
                                      tz=dt.timezone.utc).date()
        p = premium_index(taxa)
        saida[d] = censurado if p is None else p
    return saida


def preco_spot(preco_perp, base):
    """Spot implicito: F = S(1+b) => S = F/(1+b)."""
    return preco_perp / (1.0 + base)


def juro_diario(mensal=0.01):
    """CDI ao dia. Mesma convencao de scripts/acumulacao/motor.py (DIAS_MES)."""
    return (1.0 + mensal) ** (1.0 / DIAS_MES) - 1.0 if mensal > 0 else 0.0


def preco_liquidacao(margem, q, preco_entrada, mmr=MMR_PADRAO):
    """Preco de liquidacao da perna vendida a partir da margem REALMENTE postada.

    A perna vendida morre quando o patrimonio isolado dela cai ate a margem de
    manutencao:

        margem + q(Pe - P) <= mmr * q * P
        =>  P >= (margem + q*Pe) / (q * (1 + mmr))

    Esta e a forma que o motor usa, porque a margem muda ao longo da vida da
    posicao (rebalanceio e aporte). `preco_liquidacao_short` abaixo e o caso
    particular margem = q*Pe/L, util para documentar e testar.
    """
    if q <= 0:
        return float('inf')
    return (margem + q * preco_entrada) / (q * (1.0 + mmr))


def preco_liquidacao_short(preco_entrada, alavancagem, mmr=MMR_PADRAO):
    """Preco em que a perna vendida ISOLADA e liquidada.

    Margem inicial = N/L. O short perde q(P - Pe). Liquida quando

        N/L - q(P - Pe) <= mmr * q * P

    Dividindo por q e isolando P:

        P >= Pe * (1 + 1/L) / (1 + mmr)

    L=1 -> +99,2% | L=2 -> +49,4% | L=3 -> +32,8% acima da entrada.

    Por que ISOLADA e a hipotese certa aqui: a perna comprada esta no SPOT. Se
    o spot estiver em outra corretora — ou em custodia propria, que e a unica
    forma de nao repetir a FTX — ele nao serve de garantia para o perpetuo. O
    conjunto pode estar no azul e o short morrer sozinho.
    """
    if alavancagem <= 0:
        raise ValueError('alavancagem deve ser > 0')
    return preco_entrada * (1.0 + 1.0 / alavancagem) / (1.0 + mmr)


def margem_requerida(notional, alavancagem):
    return notional / alavancagem


def margem_de_manutencao(notional_atual, mmr=MMR_PADRAO):
    return notional_atual * mmr
