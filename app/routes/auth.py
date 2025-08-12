from fastapi import APIRouter, Depends, HTTPException
from models.schemas import LoginRequest, LoginResponse
from services.brokerService import BrokerService

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    # broker_service: BrokerService = Depends(get_broker_service)
):
    try:
        print("✅ Received LoginRequest:", request.dict())
        service = BrokerService(request.brokerName)
        return service.login(request)
    except Exception as e:
        print("❌ Error during login:", str(e))
        raise HTTPException(status_code=500, detail="Login failed: " + str(e))
