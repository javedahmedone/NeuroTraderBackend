import requests
import ijson
import redis
import csv
import os
from pymongo import MongoClient
from config import REDIS_URL
from global_constant import constants

class StockIngestionService:   
    def __init__(self):
        base_path = os.getcwd()  
        self.csv_path = os.path.join(base_path,  "Files", "EQUITY_L.csv")
        self.client = MongoClient(constants.MONGO_URL)
        self.r = redis.Redis.from_url(REDIS_URL)
        self.db = self.client["stockdb"]            # Database name
        self.collection = self.db["companies"]      # Collection name
        self.json_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

        # ✅ Ensure CSV exists
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV file not found at: {self.csv_path}")

    def stream_nse_equities(self):
        print("🔍 Streaming & filtering NSE stocks...")
            
        symbol_to_name = {}
        symbol_to_isin = {}
        with open(self.csv_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            reader.fieldnames = [field.strip() for field in reader.fieldnames]
            for row in reader:
                row = {k.strip(): v for k, v in row.items()}
                symbol = row['SYMBOL'].strip().upper()
                name = row['NAME OF COMPANY'].strip().lower()
                isinNumber = row['ISIN NUMBER']
                symbol_to_name[symbol] = name
                symbol_to_isin[symbol] = isinNumber
        response = requests.get(self.json_url, stream=True)
        objects = ijson.items(response.raw, "item")

        for obj in objects:
            symbol = obj.get("symbol", "").strip()
            curr_name = obj.get("name", "").strip()
            exch_seg = obj.get("exch_seg", "").strip().upper()
            token = str(obj.get("token", "")).strip()
            # isin =  obj.get("ISIN NUMBER")
            symbol in symbol_to_name
            # ✅ Filter valid NSE equity (BE/EQ segment)
            if  curr_name in symbol_to_name and exch_seg == "NSE" and symbol.endswith("-EQ") and name and token:
                name = symbol_to_name[curr_name]
                isinNumber =  symbol_to_isin[curr_name]
                yield {
                    "symbol": symbol,
                    "name": name.lower(),
                    "token": token,
                    "instrumenttype": "EQ",
                    "isinNumber": isinNumber
                }

    def store_to_redis(self):
        count = 0
        pipe = self.r.pipeline(transaction=False)
        for stock in self.stream_nse_equities():
            redis_key = f"stock:{stock['symbol'].lower()}"
            stock_name_key = f"stock:{stock['name'].lower()}"
            stock_symbol = stock["symbol"].lower()
            mongoDb = {
                "symbol": stock['symbol'],
                "company_name": stock['name'],
                "isinNumber" : stock['isinNumber'].upper()
            }
            self.collection.insert_one(mongoDb)
            pipe.set(stock_name_key, stock_symbol)
            pipe.hset(redis_key, mapping=stock)
            pipe.sadd("stock:symbols", stock_symbol)
            pipe.sadd("stock:names", stock["name"].lower())
            count += 1
            if count % 200 == 0:
                pipe.execute()
        pipe.execute()
        print(f"✅ Loaded {count} NSE equity stocks into Redis.")

    def store_stock(self):
        """Shortcut method to store all stocks."""
        self.store_to_redis()

