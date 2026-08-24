"""Custo medio + IR. Sempre modelado, nunca implicito (protocolo 3.1, item 3)."""


class Livro:
    """Controle de custo medio para apurar ganho realizado."""

    def __init__(self, aliquota=0.15, isencao_mensal=0.0):
        self.unidades = 0.0
        self.custo_total = 0.0
        self.ganho_realizado = 0.0
        self.aliquota = aliquota
        self.isencao_mensal = isencao_mensal
        self.vendas = []
        self.imposto_pago = 0.0
        self._volume_mes = {}

    def comprar(self, unidades, preco, taxa=0.0):
        self.unidades += unidades
        self.custo_total += unidades * preco + taxa

    def vender(self, unidades, preco, taxa=0.0, data=None):
        if self.unidades <= 1e-12:
            return 0.0
        medio = self.custo_total / self.unidades
        unidades = min(unidades, self.unidades)
        receita = unidades * preco - taxa
        ganho = receita - unidades * medio
        self.ganho_realizado += ganho
        self.custo_total -= unidades * medio
        self.unidades -= unidades
        self.vendas.append({'data': data, 'valor': receita, 'ganho': ganho})
        return ganho

    def imposto_da_venda(self, receita, ganho, data):
        """IR devido NO MOMENTO da venda.

        Cobrar o imposto so na liquidacao final subestima o custo do giro: quem
        realiza ganho pelo caminho perde a composicao sobre o imposto pago. Era
        exatamente o alerta do achado C6 do analises.md, e a primeira versao
        deste motor caiu nele (divergencia de +9,9% no alvo R9b).

        `isencao_mensal` implementa o limite de isencao por mes (R$ 35.000 na
        regra brasileira para pessoa fisica). Com 0.0 vale "15% liso", que e a
        ordem de grandeza usada na Fase C.
        """
        if self.aliquota <= 0 or ganho <= 0:
            return 0.0
        if self.isencao_mensal > 0 and data is not None:
            chave = (data.year, data.month)
            vol = self._volume_mes.get(chave, 0.0) + receita
            self._volume_mes[chave] = vol
            if vol <= self.isencao_mensal:
                return 0.0
        return ganho * self.aliquota

    def imposto_devido(self):
        return max(0.0, self.ganho_realizado) * self.aliquota

    def imposto_na_liquidacao(self, preco_final):
        """IR que falta pagar no resgate: so o ganho AINDA NAO realizado.

        O imposto das vendas do caminho ja saiu do caixa em `imposto_da_venda`.
        """
        if self.aliquota <= 0 or self.unidades <= 1e-12:
            return 0.0
        medio = self.custo_total / self.unidades
        ganho_final = self.unidades * (preco_final - medio)
        return max(0.0, ganho_final) * self.aliquota
