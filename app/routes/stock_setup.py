from fastapi import APIRouter
from services import stock_store_in_redis

router = APIRouter()
@router.get("/addStockInRedis")
def store_in_redis():
    return stock_store_in_redis.store_stock()