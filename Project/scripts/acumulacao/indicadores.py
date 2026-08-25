"""Medias moveis com aquecimento EXPLICITO: None enquanto nao ha `span` observacoes."""


def ema(valores, span):
    """EMA com semente = SMA dos primeiros `span` valores, alpha = 2/(span+1)."""
    a = 2.0 / (span + 1.0)
    out = [None] * len(valores)
    if len(valores) < span:
        return out
    m = sum(valores[:span]) / span
    out[span - 1] = m
    for i in range(span, len(valores)):
        m = valores[i] * a + m * (1 - a)
        out[i] = m
    return out


def sma(valores, span):
    out = [None] * len(valores)
    acc = 0.0
    for i, v in enumerate(valores):
        acc += v
        if i >= span:
            acc -= valores[i - span]
        if i >= span - 1:
            out[i] = acc / span
    return out


def media(valores, nome):
    """'EMA200' / 'SMA200' -> serie. Aquecimento tratado dentro de ema/sma."""
    tipo, span = nome[:3].upper(), int(nome[3:])
    if tipo == 'EMA':
        return ema(valores, span)
    if tipo == 'SMA':
        return sma(valores, span)
    raise ValueError(f'media desconhecida: {nome}')
