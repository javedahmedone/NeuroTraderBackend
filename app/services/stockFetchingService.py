from rapidfuzz import process
from typing import Optional, List, Any, Dict
from app.models.schemas import SearchStockModel, StockOrderRequest
from app.config import config
from pymongo import MongoClient
import os
import json
import logging

from app.logging_config import get_logger

logger = get_logger(__name__)


def _decode_redis_value(val: Any) -> Optional[str]:
    """Handle redis hgetall values that may be bytes or str."""
    if val is None:
        return None
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8")
        except Exception:
            return str(val)
    return str(val)


class StockFetchingService:
    def __init__(self):
        # lazy import redis to avoid import-time side-effects/circulars
        try:
            import redis  # local import
        except Exception as e:
            logger.error("redis import failed: %s", e)
            raise

        self.redis = redis.from_url(
            config.REDIS_URL,
            decode_responses=config.REDIS_DECODE_RESPONSES,
        )
        self.client = MongoClient(config.MONGO_URL)
        self.db = self.client[config.MONGO_DB_NAME]
        self.collection = self.db["companies"]

    # Fetch a stock by Redis key
    def getStockByKey(self, stock_key: str, quantity: int) -> Optional[StockOrderRequest]:
        if not stock_key.lower().startswith("stock:"):
            key = f"stock:{stock_key.lower()}"
        else:
            key = stock_key

        try:
            data = self.redis.hgetall(key)
            if not data:
                return None

            # values may be str (if decode_responses=True) or bytes; handle both
            def g(k: str) -> Optional[str]:
                # try string key first, then bytes key
                v = data.get(k)
                if v is None:
                    v = data.get(k.encode("utf-8"))
                return _decode_redis_value(v)

            # Build dict for Pydantic model or return None if essential missing
            symbol = g("symbol") or g("SYMBOL")
            name = g("name") or g("NAME")
            token = g("token")
            instrumenttype = g("instrumenttype")
            isin = g("isinNumber") or g("isin")

            # If StockOrderRequest signature differs, caller should adapt; return dict safe
            try:
                return StockOrderRequest(
                    symbol=symbol,
                    quantity=quantity,
                    price=float(g("price") or 0.0) if g("price") else 0.0,
                    order_type=g("order_type") or "LIMIT"
                )
            except Exception:
                # fallback: return as dict if model creation fails
                return {
                    "symbol": symbol,
                    "name": name,
                    "token": token,
                    "instrumenttype": instrumenttype,
                    "quantity": quantity,
                    "isinNumber": isin,
                }

        except Exception as e:
            logger.error("Error getting stock by key %s: %s", stock_key, e, exc_info=True)
            return None

    # Extract stock by prompt (fast fuzzy search)
    def extract_stock_from_prompt(self, stockData: List[str]) -> Optional[Dict]:
        try:
            redis_symbols = {
                s.lower().strip()
                for s in self.redis.smembers("stock:symbols") or set()
            }
            redis_names = {
                n.lower().strip()
                for n in self.redis.smembers("stock:names") or set()
            }
        except Exception as e:
            logger.error("Error reading symbol/name sets from redis: %s", e)
            redis_symbols = set()
            redis_names = set()

        for prompt in stockData:
            query = prompt.lower().strip()
            # exact symbol
            if query in redis_symbols:
                stock_key = f"stock:{query}"
                result = self.getStockByKey(stock_key, -1)
                logger.info("Exact symbol match: %s", result)
                return result

            key = query + "-eq"
            if key in redis_symbols:
                stock_key = f"stock:{key}"
                result = self.getStockByKey(stock_key, -1)
                logger.info("Exact symbol match (with -EQ): %s", result)
                return result

            # fuzzy match
            match_name = process.extractOne(query, list(redis_names), score_cutoff=70)
            match_symbol = process.extractOne(query, list(redis_symbols), score_cutoff=70)

            if match_name and (not match_symbol or match_name[1] >= match_symbol[1]):
                matched_name = match_name[0]
                symbol = self.redis.get(f"stock:{matched_name}")
                if symbol:
                    # if decode_responses True, symbol is str
                    symbol_val = symbol if isinstance(symbol, str) else _decode_redis_value(symbol)
                    stock_key = f"stock:{symbol_val}"
                    result = self.getStockByKey(stock_key, -1)
                    logger.info("Fuzzy name match: %s", result)
                    return result

            elif match_symbol:
                matched_symbol = match_symbol[0].lower()
                stock_key = f"stock:{matched_symbol}"
                result = self.getStockByKey(stock_key, -1)
                logger.info("Fuzzy symbol match: %s", result)
                return result

        logger.warning("No stock match found for prompts.")
        return None

    def stockBySearchQuery(self, query: str) -> List[SearchStockModel]:
        pipeline = [
            {
                "$search": {
                    "index": "default",
                    "compound": {
                        "should": [
                            {"text": {"query": query, "path": "company_name", "fuzzy": {"maxEdits": 1}}},
                            {"text": {"query": query, "path": "symbol", "fuzzy": {"maxEdits": 1}}}
                        ]
                    }
                }
            },
            {"$limit": 10},
            {"$project": {"_id": 0, "symbol": 1, "company_name": 1, "isinNumber": 1, "token": 1}}
        ]

        results = list(self.collection.aggregate(pipeline))
        stocksData: List[SearchStockModel] = []

        for item in results:
            model = SearchStockModel(
                stockName=item.get("company_name"),
                stockSymbol=item.get("symbol"),
                isinNumber=item.get("isinNumber"),
                stockToken=item.get("token")
            )
            stocksData.append(model)

        return stocksData
