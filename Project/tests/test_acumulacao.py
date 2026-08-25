"""
Testes do PROJETO B — laboratorio de acumulacao.

Travam a reproducao da Fase C dentro do repositorio (analises.md, Fase C) e as
propriedades que nao podem regredir em silencio.
"""
import datetime as dt
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.acumulacao import evidencia as ev
from scripts.acumulacao.dados import serie_diaria
from scripts.acumulacao.grid import grid_airbag, resumir
from scripts.acumulacao.indicadores import ema, media, sma
from scripts.acumulacao.motor import simular
from scripts.acumulacao.politicas import CDB, Airbag, DCAFixo, PassivoIsoExposicao

INICIO = dt.date(2020, 4, 5)
FIM = dt.date(2026, 8, 22)


@pytest.fixture(scope='module')
def btc():
    return serie_diaria('BTCUSDT')


def kw(**ex):
    base = dict(aporte=2000.0, dia_aporte=5, inicio=INICIO, fim=FIM,
                taxa=0.00075, juro_caixa_mensal=0.01, aliquota_ir=0.0)
    base.update(ex)
    return base


class TestIndicadores:

    def test_aquecimento_explicito(self):
        """Nenhuma decisao antes de a media ter `span` observacoes completas."""
        v = list(range(1, 301))
        e = ema(v, 200)
        assert all(x is None for x in e[:199]), 'EMA decidiu antes de aquecer'
        assert e[199] == pytest.approx(sum(v[:200]) / 200), 'semente deveria ser a SMA'
        assert sma(v, 200)[198] is None and sma(v, 200)[199] is not None

    def test_media_por_nome(self):
        v = [float(i) for i in range(1, 401)]
        assert media(v, 'EMA200')[250] == pytest.approx(ema(v, 200)[250])
        assert media(v, 'SMA200')[250] == pytest.approx(sma(v, 200)[250])
        with pytest.raises(ValueError):
            media(v, 'XYZ99')


class TestReproduzFaseC:
    """Os alvos da Fase C tem de reproduzir no repositorio (analises.md, E4a)."""

    def test_r1_cdb(self, btc):
        r = simular(*btc, politica=CDB(0.01), **kw())
        assert r['valor_final'] == pytest.approx(231566, rel=0.005)
        assert r['total_aportado'] == 154000.0

    def test_r2_dca_fixo_e_maxdd(self, btc):
        r = simular(*btc, politica=DCAFixo(), **kw())
        assert r['valor_final'] == pytest.approx(382177, rel=0.005)
        assert r['maxdd'] == pytest.approx(0.68, abs=0.02)

    def test_r4_airbag_ema200_domingo(self, btc):
        r = simular(*btc, politica=Airbag('EMA200', 6, 0), **kw())
        assert r['valor_final'] == pytest.approx(480754, rel=0.005)

    def test_r5_sentinela_pior_caso(self, btc):
        """A EMA200 na quarta e o pior caso das 42 — sentinela de regressao."""
        r = simular(*btc, politica=Airbag('EMA200', 2, 0), **kw())
        assert r['valor_final'] == pytest.approx(317516, rel=0.01)

    def test_r7_grid_vitorias(self, btc):
        grid = grid_airbag(*btc, **kw())
        base = simular(*btc, politica=DCAFixo(), **kw())['valor_final']
        res = resumir(grid, base)
        assert res['n'] == 42
        assert res['vitorias'] == 40, 'o alvo da Fase C e 40 de 42'

    def test_r12_pior_inicio(self, btc):
        d = simular(*btc, politica=DCAFixo(), **kw(inicio=dt.date(2021, 11, 5)))
        c = simular(*btc, politica=CDB(0.01), **kw(inicio=dt.date(2021, 11, 5)))
        assert d['valor_final'] == pytest.approx(212714, rel=0.005)
        assert c['valor_final'] == pytest.approx(157039, rel=0.005)


class TestImposto:

    def test_ir_sai_do_caixa_na_venda_e_nao_so_no_resgate(self, btc):
        """Achado C6: quem realiza ganho pelo caminho perde a composicao sobre o
        imposto pago. Cobrar tudo so na liquidacao final favorece o giro — foi o
        erro da primeira versao deste motor (divergencia de +9,9% no alvo R9b)."""
        grid = grid_airbag(*btc, **kw(aliquota_ir=0.15))
        base = simular(*btc, politica=DCAFixo(), **kw(aliquota_ir=0.15))['valor_final']
        res = resumir(grid, base)
        assert base == pytest.approx(347689, rel=0.005)
        assert res['mediana'] == pytest.approx(404199, rel=0.01)
        assert res['vitorias'] == 36, 'o alvo da Fase C com IR e 36 de 42'

    def test_dca_fixo_nao_gera_evento_tributario_pelo_caminho(self, btc):
        r = simular(*btc, politica=DCAFixo(), **kw(aliquota_ir=0.15))
        assert r['vendas'] == 0
        assert r['imposto_pago_no_caminho'] == 0.0
        assert r['imposto'] > 0, 'o IR da liquidacao final ainda tem de existir'


class TestTimingIsolado:
    """O benchmark que faltava no projeto — origem da releitura do achado C5."""

    def test_airbag_sem_carry_quase_empata_com_dca(self, btc):
        """Confirma C5: sem juro no caixa a vantagem sobre o DCA some."""
        grid = grid_airbag(*btc, **kw(juro_caixa_mensal=0.0))
        dca = simular(*btc, politica=DCAFixo(), **kw(juro_caixa_mensal=0.0))['valor_final']
        res = resumir(grid, dca)
        assert -1.0 < res['vantagem_mediana_pct'] < 6.0

    def test_airbag_bate_carteira_passiva_de_mesma_exposicao(self, btc):
        """Refina C5: contra exposicao iso o timing NAO e zero. As duas coisas
        sao verdadeiras e dizem coisas diferentes — 'a vantagem e carry' nao e o
        mesmo que 'o timing nao vale nada'."""
        k = kw(juro_caixa_mensal=0.0)
        grid = grid_airbag(*btc, **k)
        import statistics
        med = statistics.median(l['valor_final'] for l in grid)
        expo = statistics.mean(l['exposicao_media'] for l in grid)
        iso = simular(*btc, politica=PassivoIsoExposicao(expo), **k)['valor_final']
        assert med > iso * 1.15, 'o timing deveria bater a exposicao iso com folga'

    def test_passivo_iso_nao_opera_fora_do_aporte(self, btc):
        """Se o passivo rebalanceasse todo dia seria outra estrategia (tem premio
        de rebalanceio) e deixaria de ser o benchmark limpo de exposicao menor."""
        r = simular(*btc, politica=PassivoIsoExposicao(0.6), **kw())
        assert r['vendas'] == 0
        assert r['operacoes'] <= 77, 'no maximo uma operacao por aporte'


class TestEvidencia:
    """Etapa 4: a mesma regua do Projeto A aplicada ao Projeto B."""

    def test_bootstrap_preserva_o_tamanho_da_serie(self, btc):
        _, precos = btc
        cam = ev.caminhos_bootstrap(precos, n_caminhos=3, bloco_dias=180, seed=1)
        assert len(cam) == 3
        assert all(len(p) == len(precos) for p in cam)

    def test_bootstrap_e_deterministico(self, btc):
        _, precos = btc
        a = ev.caminhos_bootstrap(precos, n_caminhos=2, bloco_dias=180, seed=5)
        b = ev.caminhos_bootstrap(precos, n_caminhos=2, bloco_dias=180, seed=5)
        assert a[0][:50] == b[0][:50]

    def test_vantagem_do_airbag_nao_sobrevive_a_reamostragem(self, btc):
        """O achado central da Etapa 4: no historico unico o airbag vence em
        40 de 42 (95%); em historias reamostradas vira cara-ou-coroa. A vantagem
        e especifica de COMO o bear de 2022 se posicionou nesta serie."""
        datas, precos = btc
        cam = ev.caminhos_bootstrap(precos, n_caminhos=60, bloco_dias=180, seed=42)
        v_dca = [simular(datas, p, DCAFixo(), **kw())['valor_final'] for p in cam]
        v_air = [simular(datas, p, Airbag('EMA300', 6, 0), **kw())['valor_final'] for p in cam]
        p = ev.p_supera(v_air, v_dca)
        assert p < 0.70, f'P(airbag>DCA)={p:.2f} — deveria estar longe dos 95% do historico'


class TestAlocacaoOtima:
    """Etapa 4c: qual peso em BTC maximiza o CRESCIMENTO (nao o retorno medio)."""

    def test_crescimento_log_cresce_com_exposicao_ate_a_borda(self, btc):
        """Para quem nao saca e nao alavanca, o otimo de crescimento fica em 100%
        BTC — o que valida o DCA puro pelo criterio correto (mediana, nao media).

        Se este teste inverter, a recomendacao do PLANO_OPERACIONAL_REAL muda."""
        import math
        import statistics

        from scripts.acumulacao import evidencia as ev
        datas, precos = btc
        cam = ev.caminhos_bootstrap(precos, n_caminhos=40, bloco_dias=365, seed=42)
        g = {}
        for w in (0.4, 0.7, 1.0):
            pol = DCAFixo() if w >= 1.0 else PassivoIsoExposicao(w)
            vals = [simular(datas, p, pol, **kw())['valor_final'] for p in cam]
            g[w] = statistics.mean(math.log(v / 154000.0) for v in vals if v > 0)
        assert g[1.0] > g[0.7] > g[0.4], f'crescimento log nao e monotonico: {g}'

    def test_a_cauda_ruim_piora_com_exposicao(self, btc):
        """Contrapartida obrigatoria do teste acima: o otimo de crescimento COBRA
        um preco no percentil 5. Omitir isso seria vender o resultado pela metade."""
        import statistics

        from scripts.acumulacao import evidencia as ev
        datas, precos = btc
        cam = ev.caminhos_bootstrap(precos, n_caminhos=40, bloco_dias=365, seed=42)
        p5 = {}
        for w in (0.4, 1.0):
            pol = DCAFixo() if w >= 1.0 else PassivoIsoExposicao(w)
            vals = sorted(simular(datas, p, pol, **kw())['valor_final'] for p in cam)
            p5[w] = vals[int(0.05 * len(vals))]
        assert p5[1.0] < p5[0.4], 'a cauda ruim deveria piorar com mais exposicao'


class TestDefeitosCorrigidos:
    """Travas para dois defeitos latentes encontrados em revisao adversarial."""

    def test_atraso_e_em_dias_e_nao_em_semanas(self, btc):
        """Guardar so o sinal pendente e aplica-lo na proxima checagem daria um
        atraso de uma SEMANA em vez de `atraso` dias. Os dois se parecem quando
        atraso=0, entao o bug passaria despercebido em todos os alvos da Fase C."""
        datas, precos = btc
        a0 = simular(datas, precos, Airbag('EMA200', 6, 0), **kw())['valor_final']
        a1 = simular(datas, precos, Airbag('EMA200', 6, 1), **kw())['valor_final']
        a7 = simular(datas, precos, Airbag('EMA200', 6, 7), **kw())['valor_final']
        # atraso de 1 dia tem de ficar mais perto de atraso 0 do que de atraso 7
        assert abs(a1 - a0) < abs(a1 - a7), (
            f'atraso=1 ({a1:.0f}) parece uma semana, nao um dia (a0={a0:.0f}, a7={a7:.0f})')

    def test_isencao_mensal_conta_volume_e_nao_ganho(self):
        """O limite de isencao brasileiro incide sobre o VOLUME de vendas do mes.
        Uma venda com prejuizo tambem consome o limite. Contar so as vendas com
        ganho isentaria vendas que na verdade estao acima do teto."""
        from scripts.acumulacao.imposto import Livro
        import datetime as d
        L = Livro(aliquota=0.15, isencao_mensal=35000.0)
        L.comprar(1.0, 30000.0)
        dia = d.date(2024, 5, 10)
        # venda 1: prejuizo de 30k de volume — nao paga IR, mas consome o limite
        g1 = L.vender(0.5, 25000.0, data=dia)
        assert L.imposto_da_venda(12500.0, g1, dia) == 0.0
        # venda 2: com ganho; o limite do mes ja foi consumido pela venda 1
        L.comprar(0.5, 10000.0)
        g2 = L.vender(0.5, 90000.0, data=dia)
        assert L.imposto_da_venda(45000.0, g2, dia) > 0, (
            'a segunda venda deveria ser tributada: o teto mensal ja foi ultrapassado')
