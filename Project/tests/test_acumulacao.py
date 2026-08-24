"""
Testes do PROJETO B — laboratorio de acumulacao.

Travam a reproducao da Fase C dentro do repositorio (Plan.md Etapa 2) e as
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
    """Plan.md Etapa 2: os alvos da secao 5 tem de reproduzir no repositorio."""

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
