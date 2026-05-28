from app.config import config
from pymongo import MongoClient

class MongoClientService:

    def __init__(self):

        self.client = MongoClient(config.MONGO_URL)

        self.db = self.client[config.MONGO_DB_NAME]

        self.collection = self.db["companies"]

    def fetch_all(self, filter_query=None, projection=None):

        if filter_query is None:
            filter_query = {}

        return list(
            self.collection.find(
                filter_query,
                projection
            )
        )

    def fetch_one(self, filter_query, projection=None):

        return self.collection.find_one(
            filter_query,
            projection
        )

    def fetchBySymbol(self, symbol):

        return self.collection.find_one({
            "symbol": symbol.upper()
        })

    def bulkInsertDataFromRedis(self, redisService):

        documents = list(
            self.collection.find()
        )

        for doc in documents:

            symbol = doc.get("symbol")

            if not symbol:
                continue

            redis_data = redisService.getHashKeyData(symbol)

            if redis_data:

                update_fields = {
                    "isinNumber": redis_data.get("isinNumber"),
                    "token": redis_data.get("token"),
                }

                update_fields = {
                    k: v
                    for k, v in update_fields.items()
                    if v is not None
                }

                if update_fields:

                    self.collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": update_fields}
                    )

                    print(
                        f"Updated {symbol}"
                    )