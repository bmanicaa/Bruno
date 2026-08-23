"""
Script de Download de Alta Performance para Mercado Total da Binance (~536 Pares USDT + Delistados)
Baixa ~7 anos completos de dados históricos (Setembro/2019 a Agosto/2026):
- Velas 4h (até 15.300 candles)
- Velas 1D (até 2.600 candles)
- Funding Rates 8h (até 7.700 registros)
- Fear & Greed Index (até 3.650 dias)

Redução de Viés de Sobrevivência: além dos pares listados hoje, baixa uma lista
curada de ativos DELISTADOS da Binance Futures (LUNA, FTT, SRM, ANC, MIR, DODO, EOS,
YFII, BZRX, BTS, COCOS, GTO...) cujos dados históricos ainda são servidos pela API.
A data final de cada série delimita naturalmente o delisting (point-in-time).

Organizado de forma modular por moeda em data/raw/coins/{SYMBOL}/ e macro em data/raw/macro/
"""

import os
import sys
import json
import time
import datetime
import urllib.request
import urllib.parse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
COINS_DIR = os.path.join(RAW_DIR, 'coins')
MACRO_DIR = os.path.join(RAW_DIR, 'macro')

for d in [RAW_DIR, COINS_DIR, MACRO_DIR]:
    os.makedirs(d, exist_ok=True)

TARGET_4H = 15300
TARGET_1D = 2600
TARGET_FUNDING = 7700
FNG_LIMIT = 3650

DELISTED_SYMBOLS = [
    'LUNAUSDT', 'FTTUSDT', 'ANCUSDT', 'MIRUSDT', 'SRMUSDT', 'DODOUSDT',
    'EOSUSDT', 'YFIIUSDT', 'BZRXUSDT', 'BTSUSDT', 'COCOSUSDT', 'GTOUSDT',
    'TORNUSDT', 'VGXUSDT', 'TCTUSDT', 'REPUSDT'
]

def fetch_json(url, params=None, retries=4):
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2.5 * (attempt + 1))
            elif e.code in [400, 404]:
                return None
            else:
                time.sleep(0.8 * (attempt + 1))
        except Exception:
            time.sleep(0.8 * (attempt + 1))
    return None

def fetch_klines_paginated(symbol, interval='4h', total_target=TARGET_4H):
    fut_url = 'https://fapi.binance.com/fapi/v1/klines'
    all_candles = []
    end_time = None

    while len(all_candles) < total_target:
        limit = min(1000, total_target - len(all_candles))
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        if end_time:
            params['endTime'] = end_time

        data = fetch_json(fut_url, params)
        if not data or not isinstance(data, list) or len(data) == 0:
            # Fallback para Spot se não encontrar em futuros
            spot_url = 'https://api.binance.com/api/v3/klines'
            spot_sym = symbol.replace('1000', '')
            data = fetch_json(spot_url, {'symbol': spot_sym, 'interval': interval, 'limit': limit, **({'endTime': end_time} if end_time else {})})
            if not data or not isinstance(data, list) or len(data) == 0:
                break

        all_candles = data + all_candles
        end_time = data[0][0] - 1
        if len(data) < limit:
            break
        time.sleep(0.015)

    seen = set()
    unique_candles = []
    for c in all_candles:
        if c[0] not in seen:
            seen.add(c[0])
            unique_candles.append(c)
    unique_candles.sort(key=lambda x: x[0])
    return unique_candles

def save_klines_csv(candles, filepath):
    headers = [
        'open_time', 'open_time_dt', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'close_time_dt', 'quote_volume', 'trades_count',
        'taker_buy_base', 'taker_buy_quote'
    ]
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for c in candles:
            open_dt = datetime.datetime.utcfromtimestamp(c[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            close_dt = datetime.datetime.utcfromtimestamp(c[6] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([
                c[0], open_dt, c[1], c[2], c[3], c[4], c[5],
                c[6], close_dt, c[7], c[8], c[9], c[10]
            ])

def fetch_and_save_funding(symbol, filepath, total_target=TARGET_FUNDING):
    url = 'https://fapi.binance.com/fapi/v1/fundingRate'
    all_funding = []
    end_time = None
    page_size = 500  # A API da Binance capa funding em 500 registros por request

    while len(all_funding) < total_target:
        params = {'symbol': symbol, 'limit': page_size}
        if end_time:
            params['endTime'] = end_time

        data = fetch_json(url, params)
        if not data or not isinstance(data, list) or len(data) == 0:
            break

        all_funding = data + all_funding
        end_time = data[0]['fundingTime'] - 1
        if len(data) < page_size:
            break
        time.sleep(0.015)

    seen = set()
    unique_funding = []
    for item in all_funding:
        t = item['fundingTime']
        if t not in seen:
            seen.add(t)
            unique_funding.append(item)
    unique_funding.sort(key=lambda x: x['fundingTime'])

    headers = ['fundingTime', 'fundingTime_dt', 'fundingRate', 'markPrice']
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for item in unique_funding:
            f_time = int(item.get('fundingTime', 0))
            f_dt = datetime.datetime.utcfromtimestamp(f_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
            f_rate = item.get('fundingRate', '0.0')
            m_price = item.get('markPrice', '0.0')
            writer.writerow([f_time, f_dt, f_rate, m_price])
    return len(unique_funding)

def fetch_and_save_fear_and_greed(filepath, limit=FNG_LIMIT):
    url = f'https://api.alternative.me/fng/?limit={limit}'
    try:
        res = fetch_json(url)
        if res:
            data = res.get('data', [])
            headers = ['timestamp', 'date', 'value', 'value_classification']
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for item in reversed(data):
                    ts = int(item.get('timestamp', 0))
                    dt_str = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
                    val = item.get('value', '')
                    val_class = item.get('value_classification', '')
                    writer.writerow([ts, dt_str, val, val_class])
    except Exception as e:
        print(f"  [Aviso] Falha ao baixar Fear & Greed: {e}")

def get_all_binance_usdt_futures():
    url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
    data = fetch_json(url)
    if not data or 'symbols' not in data:
        raise RuntimeError("Falha ao obter exchangeInfo da Binance Futures")

    stables = {'USDCUSDT', 'FDUSDUSDT', 'TUSDUSDT', 'BUSDUSDT', 'EURUSDT', 'DAIUSDT', 'USDPUSDT', 'AEURUSDT', 'PAXGUSDT'}
    symbols = []
    for s in data['symbols']:
        sym = s['symbol']
        if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING' and s['contractType'] == 'PERPETUAL':
            if sym not in stables:
                symbols.append(sym)
    return symbols

def process_single_coin(symbol, target_4h=TARGET_4H, target_1d=TARGET_1D, target_funding=TARGET_FUNDING):
    coin_folder = os.path.join(COINS_DIR, symbol)
    os.makedirs(coin_folder, exist_ok=True)

    k4h_path = os.path.join(coin_folder, 'klines_4h.csv')
    k1d_path = os.path.join(coin_folder, 'klines_1d.csv')
    fr_path = os.path.join(coin_folder, 'funding_rates.csv')

    # 4h (até 15.300 velas)
    candles_4h = fetch_klines_paginated(symbol, interval='4h', total_target=target_4h)
    if not candles_4h:
        return symbol, False, "Sem candles 4h", None
    save_klines_csv(candles_4h, k4h_path)

    # 1D (até 2.600 velas)
    candles_1d = fetch_klines_paginated(symbol, interval='1d', total_target=target_1d)
    if candles_1d:
        save_klines_csv(candles_1d, k1d_path)

    # Funding (até 7.700 registros)
    funding_count = fetch_and_save_funding(symbol, fr_path, total_target=target_funding)

    coverage = {
        'first_4h': datetime.datetime.utcfromtimestamp(candles_4h[0][0] / 1000).strftime('%Y-%m-%d'),
        'last_4h': datetime.datetime.utcfromtimestamp(candles_4h[-1][0] / 1000).strftime('%Y-%m-%d'),
        'candles_4h': len(candles_4h),
        'candles_1d': len(candles_1d),
        'funding_count': funding_count
    }

    return symbol, True, f"4h: {len(candles_4h)} | 1D: {len(candles_1d)} | FR: {funding_count}", coverage

def main():
    print("=" * 85)
    print("DOWNLOAD DE DADOS BRUTOS — ~7 ANOS HISTÓRICOS (2019 A 2026 / BINANCE TOTAL + DELISTADOS)")
    print(f"Diretório Raiz: {RAW_DIR}")
    print("=" * 85)

    # 1. Macro
    print("\n1. Baixando Dados Macro (~7 Anos | Fear & Greed + BTC)...")
    fng_path = os.path.join(MACRO_DIR, 'fear_and_greed.csv')
    fetch_and_save_fear_and_greed(fng_path, limit=FNG_LIMIT)
    print(f"   [OK] Fear & Greed Index: {fng_path}")

    btc_4h = fetch_klines_paginated('BTCUSDT', interval='4h', total_target=TARGET_4H)
    btc_4h_path = os.path.join(MACRO_DIR, 'BTCUSDT_4h.csv')
    save_klines_csv(btc_4h, btc_4h_path)
    print(f"   [OK] BTCUSDT 4h Benchmark: {len(btc_4h)} candles -> {btc_4h_path}")

    btc_1d = fetch_klines_paginated('BTCUSDT', interval='1d', total_target=TARGET_1D)
    btc_1d_path = os.path.join(MACRO_DIR, 'BTCUSDT_1d.csv')
    save_klines_csv(btc_1d, btc_1d_path)
    print(f"   [OK] BTCUSDT 1D Benchmark: {len(btc_1d)} candles -> {btc_1d_path}")

    # 2. Obter Todos os Pares USDT Ativos + Delistados
    print("\n2. Identificando Pares Perpétuos USDT da Binance (Ativos + Delistados)...")
    symbols = get_all_binance_usdt_futures()
    for ds in DELISTED_SYMBOLS:
        if ds not in symbols:
            symbols.append(ds)
    print(f"   Total de Ativos a Baixar: {len(symbols)} moedas (inclui {len(DELISTED_SYMBOLS)} delistados curados)")

    # 3. Download Paralelo Multi-Thread (15 Threads Concorrentes)
    print(f"\n3. Iniciando Download Paralelo (15 Threads) para {len(symbols)} Ativos (Até ~7 Anos cada)...")
    start_time = time.time()

    success_count = 0
    failed_symbols = []
    successful_symbols = []
    coverage_map = {}

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(process_single_coin, sym): sym for sym in symbols}

        for idx, future in enumerate(as_completed(futures), 1):
            sym = futures[future]
            try:
                symbol, success, msg, coverage = future.result()
                if success:
                    success_count += 1
                    successful_symbols.append(symbol)
                    coverage_map[symbol] = coverage
                    if idx % 25 == 0 or idx == len(symbols):
                        elapsed = time.time() - start_time
                        print(f"   [{idx}/{len(symbols)}] ({idx/len(symbols)*100:.1f}%) Processado: {symbol} ({msg}) - Tempo: {elapsed:.1f}s")
                else:
                    failed_symbols.append(symbol)
                    print(f"   [AVISO] {symbol}: {msg}")
            except Exception as e:
                failed_symbols.append(sym)
                print(f"   [ERRO] {sym}: {e}")

    elapsed_total = time.time() - start_time

    metadata = {
        'download_timestamp': datetime.datetime.utcnow().isoformat(),
        'period_start': '2019-09-01',
        'period_years': 7,
        'target_candles_4h': TARGET_4H,
        'target_candles_1d': TARGET_1D,
        'target_funding': TARGET_FUNDING,
        'total_found': len(symbols),
        'coins_count': len(successful_symbols),
        'delisted_included': [s for s in DELISTED_SYMBOLS if s in successful_symbols],
        'symbols': sorted(successful_symbols),
        'failed_symbols': failed_symbols,
        'coverage': coverage_map
    }

    with open(os.path.join(RAW_DIR, 'universe_metadata.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)

    print("\n" + "=" * 85)
    print(f"DOWNLOAD DE ~7 ANOS CONCLUÍDO EM {elapsed_total:.1f} SEGUNDOS!")
    print(f"Moedas Estruturadas: {len(successful_symbols)} / {len(symbols)}")
    print(f"Delistados incluídos: {len([s for s in DELISTED_SYMBOLS if s in successful_symbols])}")
    if failed_symbols:
        print(f"Falhas ({len(failed_symbols)}): {failed_symbols[:10]}{'...' if len(failed_symbols) > 10 else ''}")
    print(f"Metadados Salvos em: {os.path.join(RAW_DIR, 'universe_metadata.json')}")
    print(f"Pastas Modulares em: {COINS_DIR}")
    print("=" * 85)

if __name__ == '__main__':
    main()
