"""
Script de Download de Alta Performance para Mercado Total da Binance (~527 Pares USDT)
Baixa 2 anos completos (2024 - 2026) de:
- Velas 4h (4.500 candles)
- Velas 1D (800 candles)
- Funding Rates 8h (2.200 registros)

Estrutura organizada por moeda em data/raw/coins/{SYMBOL}/ e metadados em data/raw/universe_metadata.json
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
DIR_4H = os.path.join(RAW_DIR, 'klines_4h')
DIR_1D = os.path.join(RAW_DIR, 'klines_1d')
DIR_FUNDING = os.path.join(RAW_DIR, 'funding_rates')

for d in [RAW_DIR, COINS_DIR, MACRO_DIR, DIR_4H, DIR_1D, DIR_FUNDING]:
    os.makedirs(d, exist_ok=True)

def fetch_json(url, params=None, retries=3):
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2.0 * (attempt + 1))
            elif e.code == 400 or e.code == 404:
                return None
            else:
                time.sleep(0.5 * (attempt + 1))
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None

def fetch_klines_paginated(symbol, interval='4h', total_target=4500):
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
            spot_url = 'https://api.binance.com/api/v3/klines'
            spot_sym = symbol.replace('1000', '')
            data = fetch_json(spot_url, {'symbol': spot_sym, 'interval': interval, 'limit': limit, **({'endTime': end_time} if end_time else {})})
            if not data or not isinstance(data, list) or len(data) == 0:
                break
                
        all_candles = data + all_candles
        end_time = data[0][0] - 1
        if len(data) < limit:
            break
        time.sleep(0.02)

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

def fetch_and_save_funding(symbol, filepath, total_target=2200):
    url = 'https://fapi.binance.com/fapi/v1/fundingRate'
    all_funding = []
    end_time = None
    
    while len(all_funding) < total_target:
        limit = min(1000, total_target - len(all_funding))
        params = {'symbol': symbol, 'limit': limit}
        if end_time:
            params['endTime'] = end_time
            
        data = fetch_json(url, params)
        if not data or not isinstance(data, list) or len(data) == 0:
            break
            
        all_funding = data + all_funding
        end_time = data[0]['fundingTime'] - 1
        if len(data) < limit:
            break
        time.sleep(0.02)

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

def fetch_and_save_fear_and_greed(filepath, limit=800):
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

def process_single_coin(symbol, target_4h=4500, target_1d=800, target_funding=2200):
    coin_folder = os.path.join(COINS_DIR, symbol)
    os.makedirs(coin_folder, exist_ok=True)
    
    k4h_path = os.path.join(coin_folder, 'klines_4h.csv')
    k1d_path = os.path.join(coin_folder, 'klines_1d.csv')
    fr_path = os.path.join(coin_folder, 'funding_rates.csv')
    
    # 4h
    candles_4h = fetch_klines_paginated(symbol, interval='4h', total_target=target_4h)
    if not candles_4h:
        return symbol, False, "Sem candles 4h"
    save_klines_csv(candles_4h, k4h_path)
    save_klines_csv(candles_4h, os.path.join(DIR_4H, f"{symbol}.csv"))
    
    # 1D
    candles_1d = fetch_klines_paginated(symbol, interval='1d', total_target=target_1d)
    save_klines_csv(candles_1d, k1d_path)
    save_klines_csv(candles_1d, os.path.join(DIR_1D, f"{symbol}.csv"))
    
    # Funding
    funding_count = fetch_and_save_funding(symbol, fr_path, total_target=target_funding)
    fetch_and_save_funding(symbol, os.path.join(DIR_FUNDING, f"{symbol}.csv"), total_target=target_funding)
    
    return symbol, True, f"4h: {len(candles_4h)} | 1D: {len(candles_1d)} | FR: {funding_count}"

def main():
    print("=" * 85)
    print("DOWNLOAD DE DADOS BRUTOS — MERCADO TOTAL DA BINANCE FUTURES (2 ANOS HISTÓRICOS)")
    print(f"Diretório Raiz: {RAW_DIR}")
    print("=" * 85)
    
    # 1. Macro
    print("\n1. Baixando Dados Macro de Referência (Fear & Greed + BTC Benchmark)...")
    fng_path = os.path.join(MACRO_DIR, 'fear_and_greed.csv')
    fetch_and_save_fear_and_greed(fng_path, limit=800)
    print(f"   ✓ Fear & Greed Index (800 dias): {fng_path}")
    
    btc_4h = fetch_klines_paginated('BTCUSDT', interval='4h', total_target=4500)
    btc_4h_path = os.path.join(MACRO_DIR, 'BTCUSDT_4h.csv')
    save_klines_csv(btc_4h, btc_4h_path)
    save_klines_csv(btc_4h, os.path.join(DIR_4H, 'BTCUSDT.csv'))
    print(f"   ✓ BTCUSDT 4h Benchmark: {len(btc_4h)} candles -> {btc_4h_path}")
    
    btc_1d = fetch_klines_paginated('BTCUSDT', interval='1d', total_target=800)
    btc_1d_path = os.path.join(MACRO_DIR, 'BTCUSDT_1d.csv')
    save_klines_csv(btc_1d, btc_1d_path)
    save_klines_csv(btc_1d, os.path.join(DIR_1D, 'BTCUSDT.csv'))
    print(f"   ✓ BTCUSDT 1D Benchmark: {len(btc_1d)} candles -> {btc_1d_path}")
    
    # 2. Obter Todos os Pares USDT
    print("\n2. Identificando Todos os Pares Perpétuos USDT da Binance...")
    symbols = get_all_binance_usdt_futures()
    print(f"   Total de Ativos Encontrados: {len(symbols)} moedas")
    
    # 3. Download Paralelo Multi-Thread
    print(f"\n3. Iniciando Download Paralelo (12 Threads Concorrentes) para {len(symbols)} Ativos...")
    start_time = time.time()
    
    success_count = 0
    failed_symbols = []
    successful_symbols = []
    
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(process_single_coin, sym): sym for sym in symbols}
        
        for idx, future in enumerate(as_completed(futures), 1):
            sym = futures[future]
            try:
                symbol, success, msg = future.result()
                if success:
                    success_count += 1
                    successful_symbols.append(symbol)
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
    
    # Metadados
    metadata = {
        'download_timestamp': datetime.datetime.utcnow().isoformat(),
        'period_years': 2,
        'target_candles_4h': 4500,
        'target_candles_1d': 800,
        'total_found': len(symbols),
        'coins_count': len(successful_symbols),
        'symbols': sorted(successful_symbols),
        'failed_symbols': failed_symbols
    }
    
    with open(os.path.join(RAW_DIR, 'universe_metadata.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
        
    print("\n" + "=" * 85)
    print(f"DOWNLOAD CONCLUÍDO COM SUCESSO EM {elapsed_total:.1f} SEGUNDOS!")
    print(f"Moedas Baixadas e Estruturadas: {len(successful_symbols)} / {len(symbols)}")
    print(f"Metadados Salvos em: {os.path.join(RAW_DIR, 'universe_metadata.json')}")
    print(f"Pastas Modulares em: {COINS_DIR}")
    print("=" * 85)

if __name__ == '__main__':
    main()
