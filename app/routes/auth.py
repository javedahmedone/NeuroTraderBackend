from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from models.schemas import LoginRequest, LoginResponse
from services.Common.GetSecrets import GetSecrets
from services.brokerService import BrokerService
router = APIRouter()

@router.post("/login")
def login(
    request: LoginRequest
):
    try:
        print("✅ Received LoginRequest:", request.dict())
        service = BrokerService(request.brokerName)
        return service.login(request)
    except Exception as e:
        print("❌ Error during login:", str(e))
        raise HTTPException(status_code=500, detail="Login failed: " + str(e))


@router.get("/callback/{broker}")
def callback(request: Request, code: str = None):
    print("✅ Callback received with code:", code)
    print(GetSecrets().getFrontendUrl())  # https://frontend-production.up.railway.app
    print(GetSecrets().getBackendUrl()) 
    brokerName=request.path_params['broker']
    FrontendUrl = GetSecrets().getFrontendUrl()
    react_url = f"{FrontendUrl}/callback/{brokerName}?code={code}"
    print("Redirecting to:", react_url)
    return RedirectResponse(url=react_url)
    