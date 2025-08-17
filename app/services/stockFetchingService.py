import redis
from rapidfuzz import process
from typing import Optional, List
from config import REDIS_URL
from models.schemas import StockOrderRequest


class StockFetchingService:
    def __init__(self):
        self.redis = redis.Redis.from_url(REDIS_URL)

    # ✅ Save stock into Redis
    # def save_stock(self, stock_key: str, stock_data: dict):
    #     """
    #     Stores stock data as a hash in Redis and maintains helper sets/maps
    #     stock_key example: "stock:tcs-eq"
    #     stock_data example:
    #     {
    #         "symbol": "TCS-EQ",
    #         "token": "11536",
    #         "instrumenttype": "EQ",
    #         "name": "tata consultancy services limited"
    #     }
    #     """
    #     # Store full stock as hash
    #     self.redis.hset(stock_key, mapping=stock_data)

    #     # Maintain sets for search
    #     self.redis.sadd("stock:symbols", stock_data["symbol"].lower())
    #     self.redis.sadd("stock:names", stock_data["name"].lower())

    #     # Maintain direct mapping: name → symbol
    #     self.redis.hset("stock:name_to_symbol", stock_data["name"].lower(), stock_data["symbol"].lower())

    # ✅ Fetch a stock by Redis key
    def getStockByKey(self, stock_key: str, quantity: int) -> Optional[StockOrderRequest]:
        if not stock_key.lower().startswith("stock:"):
            key = f"stock:{stock_key.lower()}"
        else:
            key = stock_key

        try:
            data = self.redis.hgetall(key)
            if not data:
                return None

            return StockOrderRequest(
                symbol=data[b'symbol'].decode('utf-8'),
                name=data[b'name'].decode('utf-8'),
                token=data[b'token'].decode('utf-8'),
                instrumenttype=data[b'instrumenttype'].decode('utf-8'),
                quantity=quantity,
                transactionType=""
            )
        except Exception as e:
            print("❌ Error getting stock:", e)
            return None

    # ✅ Extract stock by prompt (fast fuzzy search)
    def extract_stock_from_prompt(self, stockData: List[str]) -> Optional[StockOrderRequest]:
        redis_symbols = {
            symbol.decode("utf-8").strip().lower()
            for symbol in self.redis.smembers("stock:symbols")
        }
        redis_names = {
            name.decode("utf-8").strip().lower()
            for name in self.redis.smembers("stock:names")
        }

        for prompt in stockData:
            query = prompt.lower().strip()
            # --- 1. Exact match on symbol
            if query in redis_symbols:
                stock_key = f"stock:{query}"
                result = self.getStockByKey(stock_key, -1)
                print("✅ Exact symbol match:", result)
                return result
            
            key = query + '-eq'
            if key in redis_symbols:
                stock_key = f"stock:{key}"
                result = self.getStockByKey(stock_key, -1)
                print("✅ Exact symbol match:", result)
                return result

          
            # --- 3. Fuzzy match
            match_name = process.extractOne(query, redis_names, score_cutoff=70)
            match_symbol = process.extractOne(query, redis_symbols, score_cutoff=70)

            if match_name and (not match_symbol or match_name[1] >= match_symbol[1]):
                matched_name = match_name[0]
                name = "stock:"+matched_name
                symbol = self.redis.get(name)
                if symbol:
                    stock_key = f"stock:{symbol.decode('utf-8')}"
                    result = self.getStockByKey(stock_key, -1)
                    print("✅ Fuzzy name match:", result)
                    return result

            elif match_symbol:
                matched_symbol = match_symbol[0].lower()
                stock_key = f"stock:{matched_symbol}"
                result = self.getStockByKey(stock_key, -1)
                print("✅ Fuzzy symbol match:", result)
                return result

        print("⚠️ No stock match found for any prompt.")
        return None
