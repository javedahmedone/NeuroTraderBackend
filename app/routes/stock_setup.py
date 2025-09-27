from fastapi import APIRouter
from services.stockFetchingService import StockFetchingService
from services.redisClientService import RedisClientService


router = APIRouter()
@router.get("/addStockInRedis")
def store_in_redis():
    service = RedisClientService()  # ✅ Create instance
    return service.store_stock()

@router.get("/search")
def search_companies(query: str):
    service =  StockFetchingService()
    data = service.stockBySearchQuery(query)
    print(data)
    return data