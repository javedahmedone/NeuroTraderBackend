from pydantic import BaseModel
import requests
import ijson
import redis
import csv
import os
from pymongo import MongoClient
from config import REDIS_URL
from global_constant import constants
import json
from typing import Any

class RedisClientService:   
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
            # mongoDb = {
            #     "symbol": stock['symbol'],
            #     "company_name": stock['name'],
            #     "isinNumber" : stock['isinNumber'].upper()
            # }
            # self.collection.insert_one(mongoDb)
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
    
  
    def _convert_for_json(self, obj: Any) -> Any:
        if isinstance(obj, BaseModel):
            return obj.dict()
        elif isinstance(obj, list):
            return [self._convert_for_json(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self._convert_for_json(v) for k, v in obj.items()}
        return obj

    def set(self, key: str, value: Any, ttl: int = None):
        value_to_store = json.dumps(self._convert_for_json(value))
        self.r.set(key, value_to_store, ex=ttl)

    def get(self, key: str) -> Any:
        raw = self.r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    
    def delete(self, key: str):
        self.r.delete(key)

    def getHashKeyData(self, key):
        key = key.lower()
    
    # Prepend "stock:" only if not already present
        if not key.startswith("stock:"):
            key = "stock:" + key

        data =  self.r.hgetall(key)
        decoded_data = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
        return decoded_data

    def getAllStockHashes(self, pattern="stock:*eq", batch_size=500):
        """
        Fetch all stock hashes that end with -eq
        Return as list of dicts [{...}, {...}]
        """
        cursor = 0
        stock_data = []

        while True:
            cursor, keys = self.r.scan(cursor=cursor, match=pattern, count=batch_size)
            for key in keys:
                # key is bytes, convert to str
                key = key.decode("utf-8")

                if not key.endswith("-eq"):   # extra safety check
                    continue

                raw_data = self.r.hgetall(key)

                # decode each field in the hash
                decoded_data = {k.decode("utf-8"): v.decode("utf-8") for k, v in raw_data.items()}

                stock_data.append(decoded_data)

            if cursor == 0:
                break

        return stock_data
