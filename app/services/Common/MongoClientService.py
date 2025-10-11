from global_constant import constants
from pymongo import MongoClient
from services.RedisClientService import RedisClientService

class MongoClientService:   
    def __init__(self):
        self.client = MongoClient(constants.MONGO_URL)
        self.db = self.client["stockdb"]            # Database name
        self.collection = self.db["companies"]  
        self._redis = RedisClientService()
    
    def fetch_all(self, filter_query=None, projection=None):
        if filter_query is None:
            filter_query = {}

        docs = list(self.collection.find(filter_query, projection))
        return docs

    def fetch_one(self, filter_query, projection=None):
        return self.collection.find_one(filter_query, projection)

    def fetchBySymbol(self, symbol):
        return self.collection.find_one({"symbol": symbol.upper()})

    def bulkInsertDataFromRedis1(self):
        redis_data = self._redis.getAllStockHashes()
        for doc in self.collection.find():
            symbol = doc.get("symbol")
            if symbol in redis_data:
                update_data = {
                    "instrumenttype": redis_data[symbol].get("instrumenttype"),
                    "isinNumber": redis_data[symbol].get("isinNumber"),
                    "token": redis_data[symbol].get("token"),
                }
                self.collection.update_one({"_id": doc["_id"]}, {"$set": update_data})

    def bulkInsertDataFromRedis(self):
        documents = list(self.collection.find())
        for doc in documents:
            symbol = doc.get("symbol")
            if not symbol:
                continue
            redis_data = self._redis.getHashKeyData(symbol)
            if redis_data:
                update_fields = {
                    "isinNumber": redis_data.get("isinNumber"),
                    "token": redis_data.get("token"),
                }
                update_fields = {k: v for k, v in update_fields.items() if v is not None}
                if update_fields:
                    self.collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": update_fields}
                    )
                    print(f"Updated {symbol} with {update_fields}")
