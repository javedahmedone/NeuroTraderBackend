import requests
import ijson
import redis
import csv
import pandas as pd

# ✅ Redis connection
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# ✅ Angel One Scrip Master URL
json_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
csv_path = r"C:/Users/s.b.parveen/Downloads/EQUITY_L.csv"  


def stream_nse_equities(url):
    print("🔍 Streaming & filtering NSE stocks...")
        
    symbol_to_name = {}
    with open(csv_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        reader.fieldnames = [field.strip() for field in reader.fieldnames]
        for row in reader:
            row = {k.strip(): v for k, v in row.items()}
            symbol = row['SYMBOL'].strip().upper()
            name = row['NAME OF COMPANY'].strip().lower()
            symbol_to_name[symbol] = name

    response = requests.get(url, stream=True)
    objects = ijson.items(response.raw, "item")

    for obj in objects:
        symbol = obj.get("symbol", "").strip()
        curr_name = obj.get("name", "").strip()
        exch_seg = obj.get("exch_seg", "").strip().upper()
        token = str(obj.get("token", "")).strip()
        symbol in symbol_to_name
        # ✅ Filter valid NSE equity (BE/EQ segment)
        if  curr_name in symbol_to_name and exch_seg == "NSE" and symbol.endswith("-EQ") and name and token:
            name = symbol_to_name[curr_name]
            yield {
                "symbol": symbol,
                "name": name.lower(),
                "token": token,
                "instrumenttype": "EQ"
            }

def store_to_redis():
    print("🚀 Storing NSE equity stocks in Redis...")

    r.delete("stock:names")
    r.delete("stock:symbols")

    count = 0
    for stock in stream_nse_equities(json_url):
        redis_key = f"stock:{stock['symbol']}"
        r.hset(redis_key, mapping=stock)
        r.sadd("stock:names", stock["name"])
        r.sadd("stock:symbols", stock["symbol"].lower())
        count += 1

    print(f"✅ Loaded {count} NSE equity stocks into Redis.")


def store_stock():
    return store_to_redis()


# def store_to_redis121():
#     print("Redis Ping:", r.ping())
    
#     response = requests.get(json_url, stream=True)
#     json_data = ijson.items(response.raw, "item")

#     # response = requests.get(json_url)
#     # json_data = response.json()

#     symbol_to_name = {}
#     with open(csv_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
#         reader = csv.DictReader(csvfile)
#         reader.fieldnames = [field.strip() for field in reader.fieldnames]
#         for row in reader:
#             row = {k.strip(): v for k, v in row.items()}
#             symbol = row['SYMBOL'].strip().upper()
#             name = row['NAME OF COMPANY'].strip().lower()
#             symbol_to_name[symbol] = name

#     matched = 0
#     for stock in json_data:
#         # symbol = stock['name'].strip().upper()
#         symbol = stock.get("symbol", "").strip()
#         name = stock.get("name", "").strip()
#         exch_seg = stock.get("exch_seg", "").strip().upper()
#         token = str(stock.get("token", "")).strip()

        
#         if name in symbol_to_name and exch_seg == "NSE" and stock['instrumenttype'] == "EQ" and name and token:
#             name = symbol_to_name[name]
#             data = {
#                 "symbol": symbol,
#                 "name": name,
#                 "token": stock['token'],
#                 "instrumenttype": "EQ"
#             }
#             r.hset(f"stock:{symbol}", mapping=data)
#             r.hset(f"stockname:{name}", mapping=data)
#             r.sadd("stock:symbols", symbol.lower())
#             r.sadd("stock:names", name)
#             matched += 1

#     print("Total matched & stored:", matched)
#     print("Redis DB size:", r.dbsize())



# def store_to_redis12():
#     response = requests.get(json_url)
#     json_data = response.json()

#     # Step 2: Load CSV with stripped header and key names
#     symbol_to_name = {}

#     with open(csv_path, 'r', newline='') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             symbol = row['SYMBOL'].strip().upper()
#             name = row['NAME OF COMPANY'].strip().lower()
#             symbol_to_name[symbol] = name
    

#     # Step 3: Match with JSON and store in Redis
#     for stock in json_data:
#         symbol = stock['symbol'].strip().upper()
#         if symbol in symbol_to_name and stock['exch_seg'] == "NSE" and stock['instrumenttype'] == "EQ":
#             name = symbol_to_name[symbol]
#             data = {
#                 "symbol": symbol,
#                 "name": name,
#                 "token": stock['token'],
#                 "instrumenttype": "EQ"
#             }

#             # Save in Redis by both symbol and name
#             r.hset(f"stock:{symbol}", mapping=data)
#             r.hset(f"stockname:{name}", mapping=data)

#             # Add to sets for fast lookup
#             r.sadd("stock:symbols", symbol.lower())
#             r.sadd("stock:names", name)
