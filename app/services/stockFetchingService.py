from pymongo import MongoClient
from rapidfuzz import process
from typing import Optional, List
from global_constant import constants
from models.schemas import SearchStockModel, StockOrderRequest
from config import config
import redis
from config import config
from pymongo import MongoClient

class StockFetchingService:
    def __init__(self):  
        self.redis = redis.from_url(config.REDIS_URL,decode_responses=config.REDIS_DECODE_RESPONSES,socket_connect_timeout=config.REDIS_SOCKET_CONNECT_TIMEOUT)
        self.client = MongoClient(config.MONGO_URL)

        # self.client  = MongoClient(uri, tlsCAFile=certifi.where())
        self.db = self.client[config.MONGO_DB_NAME]            # Database name
        self.collection = self.db["companies"] 

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
                isinNumber=data[b'isinNumber'].decode('utf-8'),
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

    def stockBySearchQuery(self, query: str) -> List[SearchStockModel]:
        pipeline = [
            {
                "$search": {
                    "index": "default",   # 🔹 replace with your index name
                    "compound": {
                        "should": [
                            {
                                "text": {
                                    "query": query,
                                    "path": "company_name",
                                    "fuzzy": { "maxEdits": 1 }  # allow typos
                                }
                            },
                            {
                                "text": {
                                    "query": query,
                                    "path": "symbol",
                                    "fuzzy": { "maxEdits": 1 }
                                }
                            }
                        ]
                    }
                }
            },
            {"$limit": 10},   # only return top 10 results
            {
                "$project": {
                    "_id": 0,
                    "symbol": 1,
                    "company_name": 1,
                    "isinNumber": 1,   # ✅ include isin
                    "token": 1   
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))
        stocksData: list[SearchStockModel] = []

    # ✅ Simple for loop to build the list
        for item in results:
            model = SearchStockModel(
                stockName=item.get("company_name"),
                stockSymbol=item.get("symbol"),
                isinNumber=item.get("isinNumber"),
                stockToken=item.get("token")
            )
            stocksData.append(model)

        return stocksData
