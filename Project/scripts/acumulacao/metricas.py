"""Metricas de acumulacao. maxDD e tempo submerso sao de primeira classe."""


def max_drawdown(curva):
    pico, mdd = 0.0, 0.0
    for v in curva:
        pico = max(pico, v)
        if pico > 0:
            mdd = max(mdd, 1 - v / pico)
    return mdd


def tempo_submerso(curva, aportado_acumulado):
    """Fracao do tempo com a carteira valendo MENOS que o total ja depositado.

    Pergunta aberta ate a Fase E: provavelmente mais decisivo para a desistencia do
    investidor que a profundidade da queda — e nunca foi medido no projeto.
    """
    if not curva:
        return 0.0, 0
    sub = [1 if v < a else 0 for v, a in zip(curva, aportado_acumulado)]
    maior, atual = 0, 0
    for s in sub:
        atual = atual + 1 if s else 0
        maior = max(maior, atual)
    return sum(sub) / len(sub), maior


def cagr(valor_final, aportes, dias):
    """Nao e CAGR classico (ha aportes); usa o multiplo sobre o total aportado."""
    total = sum(a for _, a in aportes) if aportes else 0.0
    if total <= 0 or dias <= 0:
        return 0.0
    return (valor_final / total) ** (365.25 / dias) - 1
