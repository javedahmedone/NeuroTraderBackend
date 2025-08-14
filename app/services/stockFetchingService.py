import redis
from rapidfuzz import process
from typing import Optional
from models.schemas import StockOrderRequest

class StockFetchingService:
    def __init__(self):
        # redis_host = os.getenv("REDIS_HOST", "localhost")
        # redis_port = int(os.getenv("REDIS_PORT", "6379"))
        # self.redis = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        self.redis = redis.Redis.from_url("rediss://default:ATl-AAIjcDEwNjM2ZDRiMjBlZmQ0NTAzOTQ2YWFmNTJmNmRkNTk5NnAxMA@prompt-ladybird-14718.upstash.io:6379")
        # redis_host = os.getenv("REDIS_HOST", "localhost")
        # redis_port = int(os.getenv("REDIS_PORT", "6379"))
        # self.redis = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        # self.redis = redis.Redis.from_url("rediss://default:ATl-AAIjcDEwNjM2ZDRiMjBlZmQ0NTAzOTQ2YWFmNTJmNmRkNTk5NnAxMA@prompt-ladybird-14718.upstash.io:6379")

    def getStockByKey(self, stock_key: str, quantity: int): #-> Optional[StockOrderRequest]:
        if not stock_key.lower().startswith("stock:"):
            key = f"stock:{stock_key.lower()}"
        else:
            key = stock_key
        try:
            data = self.redis.hgetall(key)
            if not data:
                return None
            return StockOrderRequest(
                symbol= data[b'symbol'].decode('utf-8'),
                name= data[b'name'].decode('utf-8'),
                token=data[b'token'].decode('utf-8'),
                instrumenttype=data[b'instrumenttype'].decode('utf-8'),
                quantity=quantity,
                transactionType= ""
            )
            print(obj)
        except Exception as e:
            print("❌ Error getting stock:", e)
            return e

    def extract_stock_from_prompt(self, prompt: str) -> Optional[StockOrderRequest]: 
        # Check if prompt contains exact symbol
        find_exact_symbol = prompt.lower().strip()
        redis_symbols = {
            symbol.decode("utf-8").strip().lower()
            for symbol in self.redis.smembers("stock:symbols")
        }
        if find_exact_symbol in redis_symbols:
            stock_key = f"stock:{find_exact_symbol}"
            result = self.getStockByKey(stock_key, -1)
            print("✅ Exact symbol match:", result)
            return result
        
        find_exact_symbol = prompt.lower() + "-eq"
        if find_exact_symbol in redis_symbols:
            stock_key = f"stock:{find_exact_symbol}"
            result = self.getStockByKey(stock_key, -1)
            print("✅ Exact symbol match:", result)
            return result

        # Try exact name match
        for key in self.redis.scan_iter("stock:*"):
            if key in ["stock:names", "stock:symbols"]:
                continue
            try:
                name = self.redis.hget(key, "name")
                if name and name.lower() == prompt:
                    return self.getStockByKey(key, -1)
            except Exception:
                continue

        # Fuzzy match
        all_names = list(self.redis.smembers("stock:names"))
        all_symbols = list(self.redis.smembers("stock:symbols"))

        match_name = process.extractOne(prompt, all_names, score_cutoff=60)
        match_symbol = process.extractOne(prompt, all_symbols, score_cutoff=60)

        stock_key = None
        if match_name and (not match_symbol or match_name[1] >= match_symbol[1]):
            # Fuzzy match on name
            matched_name = match_name[0]
            for key in self.redis.scan_iter("stock:*"):
                if key in ["stock:names", "stock:symbols"]:
                    continue
                try:
                    if self.redis.hget(key, "name") == matched_name:
                        stock_key = key
                        break
                except:
                    continue
        elif match_symbol:
            # Fuzzy match on symbol
            matched_symbol = match_symbol[0].upper()
            stock_key = f"stock:{matched_symbol}"

        if stock_key:
            return self.getStockByKey(stock_key, -1)

        print("⚠️ No stock match found.")
        return None
