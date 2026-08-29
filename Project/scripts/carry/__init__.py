"""
Laboratorio de CASH-AND-CARRY de funding (Projeto C).

Mede o outro lado do funding rate: ate aqui o repositorio tratou funding
exclusivamente como CUSTO da perna comprada. Quem esta do outro lado recebe
aquele fluxo sem prever preco nenhum.

Estrutura delta-neutra medida: comprado no spot + vendido no perpetuo, mesma
quantidade. Nao ha aposta direcional; o retorno vem do funding, da base e do
juro do caixa, menos taxas, slippage e o custo de oportunidade da margem.

Nada aqui importa ou altera o motor do Projeto A. So le dados de data/raw/.
"""

__all__ = ['dados', 'custos', 'motor', 'grid', 'benchmarks', 'evidencia', 'cli']
