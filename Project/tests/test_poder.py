"""
Testes de regressao da Fase E — instrumentos de auditoria da propria regua.

Estes testes travam DUAS coisas:
  1. As conclusoes da curva de poder (Etapa 1), para que uma mudanca futura na
     regua estatistica nao passe despercebida.
  2. A NAO-INVASIVIDADE do teste de sinal nulo (Etapa 2) sobre o motor congelado
     do Projeto A — o patch tem de ser cirurgico e reversivel.
"""

import os
import sys
import warnings

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import statistical_validation as sv
import poder_do_teste as poder

warnings.filterwarnings('ignore')


@pytest.fixture(scope='module')
def forma():
    return poder.carregar_forma_empirica()


# --------------------------------------------------------------------------
# Etapa 1 — curva de poder
# --------------------------------------------------------------------------

class TestFormaEmpirica:

    def test_forma_vem_de_trades_reais_e_tem_a_assimetria_do_trend_following(self, forma):
        """A forma sintetica precisa herdar o formato real: win rate baixo,
        perdas ancoradas em -1R e cauda direita longa. Se isso se perder, a
        curva de poder deixa de falar sobre ESTE motor."""
        R = forma['r_pool']
        assert len(R) > 2000, 'pool de trades reais pequeno demais'
        win = (R > 0).mean()
        assert 0.30 < win < 0.40, f'win rate fora do observado: {win:.3f}'
        skew = float(((R - R.mean()) ** 3).mean() / R.std() ** 3)
        assert skew > 1.5, f'a cauda direita sumiu (skew={skew:.2f})'
        assert np.percentile(R, 25) < -0.9, 'as perdas deveriam estar ancoradas perto de -1R'

    def test_n_trials_em_vigor_e_36(self, forma):
        """A penalidade de multiplos testes realmente aplicada. Se este numero
        mudar, o piso de ruido do DSR muda junto e a curva de poder se desloca."""
        assert len(forma['sharpe_trials']) == 36

    def test_amostra_oos_e_de_88_trades_em_7502_barras(self, forma):
        """O tamanho de amostra e a raiz do problema de poder. Travado para que
        fique explicito quando a base de dados crescer."""
        assert sum(forma['trades_por_janela'].values()) == 88
        assert sum(forma['barras_por_janela'].values()) == 7502


class TestCalibracao:

    def test_volatilidade_sintetica_bate_com_a_real(self, forma):
        """Se a curva sintetica ficar lisa demais, o Sharpe infla e o protocolo
        parece MAIS poderoso do que e. Este teste impede esse erro silencioso."""
        rng = np.random.default_rng(1)
        stds = []
        for _ in range(12):
            jan = poder.simular_config(rng, 0.10, forma)
            for w in poder.OOS_NAMES:
                r = sv._window_returns(jan[w]['equity_curve'], excess=True)
                stds.append(np.std(r, ddof=1))
        sintetico = float(np.mean(stds))
        real = forma['std_barra_ref']
        assert 0.7 * real < sintetico < 1.3 * real, (
            f'vol sintetica {sintetico:.6f} destoa da real {real:.6f}')

    def test_expectancia_injetada_e_recuperada(self, forma):
        """O edge injetado tem de ser o edge medido — senao a curva de poder
        esta indexada por um numero que nao existe."""
        rng = np.random.default_rng(2)
        for alvo in (0.0, 0.10, 0.30):
            obtidos = []
            for _ in range(15):
                jan = poder.simular_config(rng, alvo, forma)
                R = [t['pnl_brl'] / t['risk_brl'] for w in poder.OOS_NAMES
                     for t in jan[w]['trades']]
                obtidos.append(np.mean(R))
            assert abs(float(np.mean(obtidos)) - alvo) < 0.02


class TestCurvaDePoder:
    """As duas sentinelas da Etapa 1. Sao o achado central da Fase E."""

    @pytest.mark.parametrize('expectancia,poder_max', [(0.05, 0.05), (0.10, 0.05)])
    def test_edge_real_porem_modesto_e_reprovado(self, forma, expectancia, poder_max):
        """Uma estrategia que GANHA DINHEIRO de verdade (E[R] positivo, Sharpe de
        trading entre 0,2 e 0,5) e reprovada quase sempre pelo protocolo vigente.

        Este e o achado que sustenta a Fase E: 'nenhuma das 36 configs tem edge'
        nao e evidencia de que nada funciona — e o resultado esperado de uma
        regua que so enxerga efeitos gigantes."""
        linhas = poder.curva_de_poder(forma, [expectancia], rodadas=60, n_iter=500)
        assert linhas[0]['poder'] <= poder_max, (
            f"poder {linhas[0]['poder']:.3f} alto demais para E[R]={expectancia}")
        assert linhas[0]['sharpe_trading_medio'] > 0, 'o edge injetado deveria ser positivo'

    def test_edge_grande_e_aprovado(self, forma):
        """Contraprova: a regua NAO esta cega. Um edge realmente grande passa.
        Sem este teste, a conclusao 'a regua reprova tudo' poderia ser apenas um
        bug no gerador sintetico."""
        linhas = poder.curva_de_poder(forma, [0.50], rodadas=60, n_iter=500)
        assert linhas[0]['poder'] > 0.50, (
            f"poder {linhas[0]['poder']:.3f} baixo demais para um edge grande")

    def test_gate_estatistico_e_o_gargalo_e_nao_os_demais(self, forma):
        """Diagnostico: com E[R]=+0.10 os criterios 1-4 passam quase sempre e o
        criterio 5 (bootstrap + DSR) reprova. Localiza o gargalo no lugar certo,
        para que ninguem 'conserte' o criterio errado."""
        l = poder.curva_de_poder(forma, [0.10], rodadas=60, n_iter=500)[0]
        assert l['g1'] > 0.9 and l['g2'] > 0.9 and l['g3'] > 0.9 and l['g4'] > 0.9
        assert l['g5'] < 0.10, 'o criterio 5 deveria ser o gargalo'

    def test_sob_o_nulo_o_protocolo_nao_aprova(self, forma):
        """Falso positivo: com edge ZERO o protocolo tem de reprovar praticamente
        sempre. Se este teste falhar, a regua ficou permissiva."""
        l = poder.curva_de_poder(forma, [0.0], rodadas=60, n_iter=500)[0]
        assert l['poder'] < 0.05


# --------------------------------------------------------------------------
# Etapa 2 — nao-invasividade do sinal nulo
# --------------------------------------------------------------------------

class TestSinalNuloNaoInvade:

    def test_patch_e_reversivel(self):
        """O motor congelado tem de voltar exatamente ao que era."""
        import backtest_institucional as eng
        import sinal_nulo as nulo
        original = eng._hot_arrays
        nulo.ativar_nulo(seed=1)
        assert eng._hot_arrays is not original
        nulo.desativar_nulo()
        assert eng._hot_arrays is original

    def test_colunas_de_execucao_nunca_sao_rotacionadas(self):
        """Preco de entrada e STOP sao calculados na triagem com open/low/atr14.
        Se o nulo mexesse neles, os trades nulos teriam stops irreais e a
        distribuicao nula nao serviria de comparacao."""
        import pandas as pd
        import sinal_nulo as nulo
        n = 400
        df = pd.DataFrame({c: np.arange(n, dtype=float)
                           for c in nulo.eng._HOT_COLS_4H})
        nulo.ativar_nulo(seed=3)
        try:
            saida = nulo._hot_arrays_nulo(df)
        finally:
            nulo.desativar_nulo()
        for c in nulo.COLUNAS_PRESERVADAS:
            assert np.array_equal(saida[c], np.arange(n, dtype=float)), (
                f'coluna de execucao {c} foi alterada pelo nulo')

    def test_colunas_de_sinal_sao_de_fato_destruidas(self):
        """Contraprova: o nulo precisa realmente aleatorizar o sinal, senao o
        'teste nulo' seria apenas o motor normal com outro nome."""
        import pandas as pd
        import sinal_nulo as nulo
        n = 400
        df = pd.DataFrame({c: np.arange(n, dtype=float)
                           for c in nulo.eng._HOT_COLS_4H})
        nulo.ativar_nulo(seed=4)
        try:
            saida = nulo._hot_arrays_nulo(df)
        finally:
            nulo.desativar_nulo()
        mudou = [c for c in nulo.COLUNAS_DE_SINAL
                 if not np.array_equal(saida[c], np.arange(n, dtype=float))]
        assert len(mudou) == len(nulo.COLUNAS_DE_SINAL), 'algum sinal nao foi rotacionado'

    def test_rotacao_preserva_a_distribuicao_do_sinal(self):
        """A rotacao circular tem de manter a distribuicao marginal intacta — e
        isso que mantem a TAXA de entradas realista no nulo. Um embaralhamento
        que mudasse a distribuicao produziria um nulo com numero de trades
        incomparavel com o real."""
        import pandas as pd
        import sinal_nulo as nulo
        n = 500
        rng = np.random.default_rng(9)
        base = rng.standard_normal(n)
        df = pd.DataFrame({c: base.copy() for c in nulo.eng._HOT_COLS_4H})
        nulo.ativar_nulo(seed=5)
        try:
            saida = nulo._hot_arrays_nulo(df)
        finally:
            nulo.desativar_nulo()
        for c in ('rsi14_1d', 'cvd', 'ema20_1d'):
            assert np.allclose(np.sort(saida[c]), np.sort(base)), (
                f'{c}: a rotacao alterou a distribuicao')
