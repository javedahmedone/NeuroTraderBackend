from fastapi import APIRouter, HTTPException, Request
from services.MarketDataService import MarketDataService
router = APIRouter()

@router.get("/marketMovers")
def marketMover():
    try:
        service = MarketDataService()
        return service.fetch_nse_gainers()
    except Exception as e:
        print("❌ Error during login:", str(e))
        raise HTTPException(status_code=500, detail="Login failed: " + str(e))

@router.get("/stockDataById")
def get_time( request: Request, stockSymbol: str, token: str, isinNumber: str, interval:str):
    headers = dict(request.headers)
    if headers.get("brokername") is None or headers.get("brokername") == '':
        raise HTTPException(status_code=401, detail={ "message": "failed", "status": "false", "error": "Headers are missing or brokername is empty" })        
    service = MarketDataService(headers["brokername"])
    return service.fetchMarketData(request, stockSymbol, token, isinNumber, interval)

@router.get("/time")
def get_time():
    service = MarketDataService()
    return service.isMarketOpen()
    
