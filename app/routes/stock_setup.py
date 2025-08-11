from fastapi import APIRouter
from app.services.stockIngestionService import StockIngestionService


router = APIRouter()
@router.get("/addStockInRedis")
def store_in_redis():
    service = StockIngestionService()  # ✅ Create instance
    return service.store_stock()