"""
Script de Download de Dados Brutos de Mercado para 2 Anos (Binance + Alternative.me)
Baixa o histórico completo (Agosto/2024 a Agosto/2026 = 730+ dias) para o universo
de moedas institucionais e organiza tudo por moeda em data/raw/coins/{SYMBOL}/
e em data/raw/macro/ para isolamento estrito de contexto da IA.
"""

import os
import sys
import json
import time
import datetime
import urllib
import urllib.request
import urllib.parse
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
COINS_DIR = os.path.join(RAW_DIR, 'coins')
MACRO_DIR = os.path.join(RAW_DIR, 'macro')

# Pastas de compatibilidade direta
DIR_4H = os.path.join(RAW_DIR, 'klines_4h')
DIR_1D = os.path.join(RAW_DIR, 'klines_1d')
DIR_FUNDING = os.path.join(RAW_DIR, 'funding_rates')

for d in [RAW_DIR, COINS_DIR, MACRO_DIR, DIR_4H, DIR_1D, DIR_FUNDING]:
    os.makedirs(d, exist_ok=True)

def fetch_json(url, params=None):
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

def fetch_klines_paginated(symbol, interval='4h', total_target=4500):
    url = 'https://api.binance.com/api/v3/klines'
    spot_symbol = 'PEPEUSDT' if symbol == '1000PEPEUSDT' else symbol
    all_candles = []
    end_time = None
    
    while len(all_candles) < total_target:
        limit = min(1000, total_target - len(all_candles))
        params = {'symbol': spot_symbol, 'interval': interval, 'limit': limit}
        if end_time:
            params['endTime'] = end_time
        try:
            data = fetch_json(url, params)
            if not data or isinstance(data, dict):
                break
            all_candles = data + all_candles
            end_time = data[0][0] - 1
            if len(data) < limit:
                break
            time.sleep(0.04)
        except Exception as e:
            # Fallback para futuros se o spot não existir com esse ticker
            try:
                fut_url = 'https://fapi.binance.com/fapi/v1/klines'
                params = {'symbol': symbol, 'interval': interval, 'limit': limit}
                if end_time:
                    params['endTime'] = end_time
                data = fetch_json(fut_url, params)
                if data and isinstance(data, list):
                    all_candles = data + all_candles
                    end_time = data[0][0] - 1
                    if len(data) < limit:
                        break
            except Exception:
                pass
            break

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

def fetch_and_save_funding_paginated(symbol, filepath, total_target=2200):
    fut_symbol = '1000PEPEUSDT' if symbol == 'PEPEUSDT' else symbol
    url = 'https://fapi.binance.com/fapi/v1/fundingRate'
    all_funding = []
    end_time = None
    
    while len(all_funding) < total_target:
        limit = min(1000, total_target - len(all_funding))
        params = {'symbol': fut_symbol, 'limit': limit}
        if end_time:
            params['endTime'] = end_time
        try:
            data = fetch_json(url, params)
            if not data or not isinstance(data, list):
                break
            all_funding = data + all_funding
            end_time = data[0]['fundingTime'] - 1
            if len(data) < limit:
                break
            time.sleep(0.04)
        except Exception:
            break

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

def fetch_and_save_fear_and_greed(filepath, limit=800):
    url = f'https://api.alternative.me/fng/?limit={limit}'
    try:
        res = fetch_json(url)
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

def get_liquid_universe():
    # Universo do Prompt.md (20 moedas) + 9 Moedas Iniciais + Top Futuros Líquidos (> $25M)
    core_pool = [
        'SOLUSDT', 'ETHUSDT', 'BNBUSDT', 'NEARUSDT', 'AVAXUSDT',
        'SUIUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT', 'RENDERUSDT',
        'FETUSDT', 'ONDOUSDT', 'LINKUSDT', 'AAVEUSDT', 'INJUSDT',
        'PENDLEUSDT', 'TIAUSDT', 'PEPEUSDT', 'GALAUSDT', 'TONUSDT',
        'ILVUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT', 'DOTUSDT',
        'POLUSDT', 'SEIUSDT', 'WLDUSDT', 'KASUSDT', 'STXUSDT'
    ]
    try:
        req = urllib.request.urlopen('https://fapi.binance.com/fapi/v1/ticker/24hr', timeout=10)
        tickers = json.loads(req.read().decode())
        liquid = [
            t['symbol'].replace('1000', '') for t in tickers 
            if t['symbol'].endswith('USDT') and float(t['quoteVolume']) >= 30_000_000
        ]
        # Converter para formato Binance padrão
        clean_liquid = [s if s.endswith('USDT') else f"{s}USDT" for s in liquid]
        merged = list(dict.fromkeys(core_pool + clean_liquid))
        return merged[:50]  # Top 50 moedas institucionais mais líquidas
    except Exception:
        return core_pool

def main():
    print("=" * 80)
    print("DOWNLOAD DE DADOS BRUTOS DE MERCADO — HISTÓRICO DE 2 ANOS (2024 - 2026)")
    print(f"Diretório Raiz: {RAW_DIR}")
    print("=" * 80)
    
    # 1. Macro Data
    print("\n1. Baixando Dados Macro (Fear & Greed Index + BTC Benchmark)...")
    fng_path = os.path.join(MACRO_DIR, 'fear_and_greed.csv')
    fetch_and_save_fear_and_greed(fng_path, limit=800)
    print(f"   ✓ Fear & Greed (800 dias): {fng_path}")
    
    btc_4h = fetch_klines_paginated('BTCUSDT', interval='4h', total_target=4500)
    btc_4h_path = os.path.join(MACRO_DIR, 'BTCUSDT_4h.csv')
    save_klines_csv(btc_4h, btc_4h_path)
    save_klines_csv(btc_4h, os.path.join(DIR_4H, 'BTCUSDT.csv'))
    print(f"   ✓ BTCUSDT 4h: {len(btc_4h)} candles -> {btc_4h_path}")
    
    btc_1d = fetch_klines_paginated('BTCUSDT', interval='1d', total_target=800)
    btc_1d_path = os.path.join(MACRO_DIR, 'BTCUSDT_1d.csv')
    save_klines_csv(btc_1d, btc_1d_path)
    save_klines_csv(btc_1d, os.path.join(DIR_1D, 'BTCUSDT.csv'))
    print(f"   ✓ BTCUSDT 1D: {len(btc_1d)} candles -> {btc_1d_path}")
    
    # 2. Coins Universe
    symbols = get_liquid_universe()
    print(f"\n2. Baixando Dados Individuais de 2 Anos para {len(symbols)} Moedas Líquidas...")
    
    metadata = {
        'download_timestamp': datetime.datetime.utcnow().isoformat(),
        'period_years': 2,
        'target_candles_4h': 4500,
        'target_candles_1d': 800,
        'coins_count': len(symbols),
        'symbols': symbols
    }
    
    for idx, s in enumerate(symbols, 1):
        print(f"\n[{idx}/{len(symbols)}] Processando {s}:")
        coin_folder = os.path.join(COINS_DIR, s)
        os.makedirs(coin_folder, exist_ok=True)
        
        # 4h Klines (4.500 candles = 750 dias)
        k4h = fetch_klines_paginated(s, interval='4h', total_target=4500)
        c_k4h_path = os.path.join(coin_folder, 'klines_4h.csv')
        save_klines_csv(k4h, c_k4h_path)
        save_klines_csv(k4h, os.path.join(DIR_4H, f"{s}.csv"))
        print(f"   ✓ 4h Klines ({len(k4h)} velas) -> data/raw/coins/{s}/klines_4h.csv")
        
        # 1D Klines (800 candles = 800 dias)
        k1d = fetch_klines_paginated(s, interval='1d', total_target=800)
        c_1d_path = os.path.join(coin_folder, 'klines_1d.csv')
        save_klines_csv(k1d, c_1d_path)
        save_klines_csv(k1d, os.path.join(DIR_1D, f"{s}.csv"))
        print(f"   ✓ 1D Klines ({len(k1d)} velas) -> data/raw/coins/{s}/klines_1d.csv")
        
        # Funding Rates (8h)
        c_fr_path = os.path.join(coin_folder, 'funding_rates.csv')
        fetch_and_save_funding_paginated(s, c_fr_path, total_target=2200)
        fetch_and_save_funding_paginated(s, os.path.join(DIR_FUNDING, f"{s}.csv"), total_target=2200)
        print(f"   ✓ Funding Rates 8h -> data/raw/coins/{s}/funding_rates.csv")
        
    with open(os.path.join(RAW_DIR, 'universe_metadata.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
        
    print("\n" + "=" * 80)
    print("CONCLUÍDO COM SUCESSO! BASE HISTÓRICA DE 2 ANOS ARMAZENADA E ORGANIZADA.")
    print(f"Estrutura organizada por moeda pronta em: {COINS_DIR}")
    print("=" * 80)

if __name__ == '__main__':
    main()
