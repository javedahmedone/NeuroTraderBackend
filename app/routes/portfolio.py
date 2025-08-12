from fastapi import APIRouter, Request
from models.schemas import CancelOrderRequest
from global_constant import constants
from services.brokerService import BrokerService

router = APIRouter()

# ✅ Endpoint 1: Get Holdings
@router.get("/holdings")
def fetch_holdings(
    request: Request
):
    headers = dict(request.headers)
    required = ["brokername"]
    missing = [key for key in required if key not in headers]
    if missing or headers["brokername"] == '' :
        raise ValueError(f"Missing required headers brokerName: {', '.join(missing)}")
        
    service = BrokerService(headers["brokername"])
    return service.getHoldings(headers,constants.NUll)


# ✅ Endpoint 2: Get Profile
@router.get("/profile")
def fetch_holdings(
    request: Request
):
    headers = dict(request.headers)
    required = ["brokername"]
    missing = [key for key in required if key not in headers]
    if missing:
        raise ValueError(f"Missing required headers brokerName: {', '.join(missing)}")  
    service = BrokerService(headers["brokername"])
    return service.get_profile(headers)

# ✅ Endpoint 2: Get Orders
@router.get("/orders")
def fetch_orders(
       request: Request
    ):
    headers = dict(request.headers)
    required = ["brokername"]
    missing = [key for key in required if key not in headers]
    if missing:
        raise ValueError(f"Missing required headers brokerName: {', '.join(missing)}")  
    service = BrokerService(headers["brokername"])
    data =  service.getOrders(headers,constants.NUll)
    return data


@router.post("/cancelOrder")
def fetch_orders(
    request: Request,
    cancelRequest: CancelOrderRequest
):

    headers = dict(request.headers)
    required = ["brokername"]
    missing = [key for key in required if key not in headers]
    if missing:
        raise ValueError(f"Missing required headers brokerName: {', '.join(missing)}")  
    service = BrokerService(headers["brokername"])
    data =  service.cancelOrder(headers, cancelRequest, constants.NUll)
    return data

