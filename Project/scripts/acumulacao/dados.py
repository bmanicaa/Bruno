"""Carga de series diarias. Duas series, nao 550 moedas em 4h."""
import csv
import datetime as dt
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(BASE_DIR, 'data', 'raw')


def serie_diaria(ativo):
    """(datas, fechamentos) do ativo. Procura em macro/ e em coins/{ATIVO}/."""
    candidatos = [
        os.path.join(RAW, 'macro', f'{ativo}_1d.csv'),
        os.path.join(RAW, 'coins', ativo, 'klines_1d.csv'),
        os.path.join(RAW, 'klines_1d', f'{ativo}.csv'),
    ]
    caminho = next((c for c in candidatos if os.path.exists(c)), None)
    if caminho is None:
        # Falha explicita: o bug A5 do Projeto A era justamente descartar o ETH
        # em silencio com um `continue` mudo.
        raise FileNotFoundError(f'serie diaria de {ativo} nao encontrada em {candidatos}')
    linhas = []
    with open(caminho, 'r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            linhas.append((dt.date.fromisoformat(r['open_time_dt'][:10]), float(r['close'])))
    linhas.sort()
    return [d for d, _ in linhas], [c for _, c in linhas]
