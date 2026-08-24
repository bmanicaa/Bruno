"""
As regras testaveis. Cada politica decide UMA coisa por dia: qual a exposicao
alvo ao ativo (0.0 a 1.0). O motor executa; a politica nao conhece dinheiro.

Nada de otimizacao aqui: quem varre parametros e o grid.py.
"""
from .indicadores import media


class CDB:
    """Benchmark do usuario: renda fixa a X% ao mes."""
    nome = 'CDB'

    def __init__(self, taxa_mensal=0.01):
        self.taxa_mensal = taxa_mensal

    def preparar(self, datas, precos):
        pass

    def exposicao_alvo(self, i, data, **estado):
        return 0.0


class DCAFixo:
    """Comprar e nunca vender. O benchmark que o airbag precisa bater."""
    nome = 'DCAFixo'

    def preparar(self, datas, precos):
        pass

    def exposicao_alvo(self, i, data, **estado):
        return 1.0


class Airbag:
    """Fora do ativo quando o preco fecha abaixo da media longa; dentro acima.

    Reage, nao preve. `dia_checagem` = 0..6 (segunda..domingo). `atraso` = 0
    executa no mesmo fechamento observado; 1 executa no dia seguinte.
    """
    nome = 'Airbag'

    def __init__(self, nome_media='EMA200', dia_checagem=6, atraso=0, fatia=1.0):
        self.nome_media = nome_media
        self.dia_checagem = dia_checagem
        self.atraso = atraso
        self.fatia = fatia
        self._ma = None
        self._estado = None
        self._pendente = None

    def preparar(self, datas, precos):
        self._ma = media(precos, self.nome_media)
        self._estado = None
        self._pendente = None
        self._precos = precos
        self._datas = datas

    def exposicao_alvo(self, i, data, **estado):
        ma = self._ma[i]
        if data.weekday() == self.dia_checagem and ma is not None:
            sinal = self._precos[i] > ma
            if self.atraso == 0:
                self._estado = sinal
            else:
                if self._pendente is not None:
                    self._estado = self._pendente
                self._pendente = sinal
        if self._estado is None:
            return 0.0
        return self.fatia if self._estado else (1.0 - self.fatia)


class PassivoIsoExposicao:
    """Peso FIXO no ativo, zero operacoes — o benchmark que faltava.

    Comparar o airbag apenas com 'DCA 100% BTC' confunde duas coisas: o airbag
    fica ~40% do tempo em caixa, entao parte do resultado dele e simplesmente
    ter menos exposicao (e ganhar juro). Contra uma carteira PASSIVA de mesma
    exposicao media, isola-se o que o TIMING de fato agrega.

    Sem este benchmark, a conclusao C5 do analises.md ("~90% da vantagem e CDI")
    fica indistinguivel de "o timing nao vale nada" — e as duas sao diferentes.
    """
    nome = 'PassivoIso'

    def __init__(self, peso=0.6, dia_aporte=5):
        self.peso = peso
        self.dia_aporte = dia_aporte

    def preparar(self, datas, precos):
        pass

    def exposicao_alvo(self, i, data, **estado):
        # So aloca o aporte NOVO; nunca rebalanceia o que ja esta na carteira.
        # Zero operacoes fora do dia do aporte, zero evento tributario, zero
        # premio de rebalanceio — e isso que faz dela o benchmark limpo de
        # "exposicao menor" contra o qual medir o TIMING do airbag.
        if data.day != self.dia_aporte:
            return None
        ativo = estado.get('valor_ativo', 0.0)
        aporte = estado.get('aporte_hoje', 0.0)
        valor = ativo + estado.get('caixa', 0.0)
        if valor <= 1e-9:
            return self.peso
        return (ativo + aporte * self.peso) / valor
