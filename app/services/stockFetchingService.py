import re
import redis
from rapidfuzz import process
from typing import Optional
from models.schemas import StockOrderRequest

class StockFetchingService:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    def getStockByKey(self, stock_key: str, quantity: int) -> Optional[StockOrderRequest]:
        if not stock_key.lower().startswith("stock:"):
            key = f"stock:{stock_key.upper()}"
        else:
            key = stock_key
        try:
            data = self.redis.hgetall(key)
            print("====15===",data)
            if not data:
                return None
            print("📦 Stock data retrieved:", data)
            return StockOrderRequest(
                symbol=data.get("symbol"),
                name=data.get("name"),
                token=data.get("token"),
                instrumenttype=data.get("instrumenttype"),
                quantity=quantity
            )
        except Exception as e:
            print("❌ Error getting stock:", e)
            return None

    def extract_stock_from_prompt(self, prompt: str) -> Optional[StockOrderRequest]:
        # prompt = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", prompt.lower().strip())
        # prompt = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", prompt)

        # quantity = 1
        # match = re.search(r"\b(\d+)\b", prompt)
        # if match:
        #     quantity = int(match.group(1))

        # # Step 2: Remove common filler words
        # common_words = {"i", "want", "to", "buy", "sell", "of", "stock", "stocks", "stok","sll"}
        # words = [w for w in prompt.split() if w not in common_words and not w.isdigit()]
        # fuzzy_input = " ".join(words).strip()

        # if not fuzzy_input:
        #     return None  # No stock-related word found

        # Check if prompt contains exact symbol
        find_exact_symbol = prompt.upper() + "-EQ"
        print("exact stokc ==========", find_exact_symbol)
        if find_exact_symbol.lower() in self.redis.smembers("stock:symbols"):
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

        print("match_name ======",match_name)
        print("match_symbol===========",match_symbol)
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
