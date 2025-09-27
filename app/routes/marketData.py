from fastapi import APIRouter, HTTPException, Request
from services.MarketMoverService import MarketMoverService

router = APIRouter()

@router.get("/marketMovers")
def marketMover(
):
    try:
        service = MarketMoverService()
        return service.fetch_nse_gainers()
    except Exception as e:
        print("❌ Error during login:", str(e))
        raise HTTPException(status_code=500, detail="Login failed: " + str(e))
