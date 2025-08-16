import requests
import ijson
import redis
import csv
import os

from config import REDIS_URL


class StockIngestionService:   
    def __init__(self):
        base_path = os.getcwd()  
        self.csv_path = os.path.join(base_path,  "Files", "EQUITY_L.csv")
        # ✅ Ensure CSV exists
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV file not found at: {self.csv_path}")

        # ✅ Redis connection
        self.r = redis.Redis.from_url(REDIS_URL)

        # ✅ Angel One Scrip Master URL
        self.json_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

    def stream_nse_equities(self):
        print("🔍 Streaming & filtering NSE stocks...")
            
        symbol_to_name = {}
        with open(self.csv_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            reader.fieldnames = [field.strip() for field in reader.fieldnames]
            for row in reader:
                row = {k.strip(): v for k, v in row.items()}
                symbol = row['SYMBOL'].strip().upper()
                name = row['NAME OF COMPANY'].strip().lower()
                symbol_to_name[symbol] = name

        response = requests.get(self.json_url, stream=True)
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


    def store_to_redis(self):
            """Store streamed stocks in Redis."""
            print("🚀 Storing NSE equity stocks in Redis...")

            # Clear old data
            self.r.delete("stock:names")
            self.r.delete("stock:symbols")

            count = 0
            for stock in self.stream_nse_equities():
                redis_key = f"stock:{stock['symbol'].lower()}"
                self.r.hset(redis_key, mapping=stock)
                self.r.sadd("stock:names", stock["name"].lower())
                self.r.sadd("stock:symbols", stock["symbol"].lower())
                count += 1

            print(f"✅ Loaded {count} NSE equity stocks into Redis.")

    def store_stock(self):
        """Shortcut method to store all stocks."""
        self.store_to_redis()

