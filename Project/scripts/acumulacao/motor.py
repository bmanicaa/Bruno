"""
Loop diario deterministico. Mesma config -> mesmo resultado, sempre.

Contratos (Plan.md 3.1):
  * aquecimento explicito: a politica devolve exposicao None-safe; enquanto a
    media nao aqueceu, o Airbag devolve 0.0 (fica em caixa) por decisao, e o
    inicio da simulacao e definido pelo chamador.
  * caixa e imposto sempre modelados.
  * zero lookahead: `atraso_execucao` e parametro explicito da politica.
"""
import datetime as dt

from .imposto import Livro
from .metricas import max_drawdown, tempo_submerso

DIAS_MES = 30.4375


def simular(datas, precos, politica, aporte=2000.0, dia_aporte=5,
            inicio=None, fim=None, taxa=0.00075, juro_caixa_mensal=0.01,
            aliquota_ir=0.0, tolerancia=0.0, isencao_mensal=0.0):
    """Executa a politica. Devolve dict com valor final, curva e diagnostico."""
    politica.preparar(datas, precos)
    juro_dia = (1 + juro_caixa_mensal) ** (1 / DIAS_MES) - 1 if juro_caixa_mensal > 0 else 0.0

    idx = [i for i, d in enumerate(datas)
           if (inicio is None or d >= inicio) and (fim is None or d <= fim)]
    if not idx:
        raise ValueError('janela vazia')

    livro = Livro(aliquota=aliquota_ir, isencao_mensal=isencao_mensal)
    caixa = 0.0
    curva, aportado_acum, expo_diaria = [], [], []
    total_aportado = 0.0
    operacoes = 0

    for i in idx:
        d, p = datas[i], precos[i]
        caixa *= (1 + juro_dia)
        aporte_hoje = 0.0
        if d.day == dia_aporte:
            caixa += aporte
            total_aportado += aporte
            aporte_hoje = aporte

        alvo = politica.exposicao_alvo(i, d, valor_ativo=livro.unidades * p,
                                       caixa=caixa, aporte_hoje=aporte_hoje)
        valor = livro.unidades * p + caixa
        # alvo=None significa "nao mexer hoje" — e o que separa uma carteira
        # PASSIVA (que so aloca o aporte novo) de uma de peso fixo rebalanceada
        # todo dia, que e uma estrategia diferente e tem premio de rebalanceio.
        if alvo is not None and valor > 1e-9:
            atual = (livro.unidades * p) / valor
            if abs(alvo - atual) > max(tolerancia, 1e-9):
                desejado = alvo * valor
                delta = desejado - livro.unidades * p
                if delta > 0 and caixa > 1e-9:                 # comprar
                    gasto = min(delta, caixa)
                    u = gasto * (1 - taxa) / p
                    livro.comprar(u, p, taxa=gasto * taxa)
                    caixa -= gasto
                    operacoes += 1
                elif delta < 0 and livro.unidades > 1e-12:     # vender
                    u = min(-delta / p, livro.unidades)
                    receita = u * p * (1 - taxa)
                    ganho = livro.vender(u, p, taxa=u * p * taxa, data=d)
                    ir_venda = livro.imposto_da_venda(receita, ganho, d)
                    livro.imposto_pago += ir_venda
                    caixa += receita - ir_venda   # o IR sai do caixa AGORA
                    operacoes += 1

        valor = livro.unidades * p + caixa
        curva.append(valor)
        aportado_acum.append(total_aportado)
        expo_diaria.append((livro.unidades * p) / valor if valor > 1e-9 else 0.0)

    preco_final = precos[idx[-1]]
    bruto = livro.unidades * preco_final + caixa
    ir = livro.imposto_na_liquidacao(preco_final) if aliquota_ir > 0 else 0.0
    frac_sub, maior_sub = tempo_submerso(curva, aportado_acum)

    return {
        'valor_final': bruto - ir,
        'imposto_pago_no_caminho': livro.imposto_pago,
        'valor_final_bruto': bruto,
        'imposto': ir,
        'total_aportado': total_aportado,
        'maxdd': max_drawdown(curva),
        'exposicao_media': sum(expo_diaria) / len(expo_diaria),
        'operacoes': operacoes,
        'vendas': len(livro.vendas),
        'ganho_realizado': livro.ganho_realizado,
        'tempo_submerso_frac': frac_sub,
        'tempo_submerso_max_dias': maior_sub,
        'dias': len(idx),
        'curva': curva,
    }
