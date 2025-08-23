from fastapi import APIRouter, HTTPException, Request
from models.schemas import LoginRequest, LoginResponse
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
    print(code)
    print(request)
    # if not code:
    #     return JSONResponse({"error": "No code received"}, status_code=400)

    # # Step 3: Exchange code for access token
    # token_url = "https://api.upstox.com/v2/login/authorization/token"
    # payload = {
    #     "code": code,
    #     "client_id": API_KEY,
    #     "client_secret": SECRET_KEY,
    #     "redirect_uri": REDIRECT_URI,
    #     "grant_type": "authorization_code",
    # }
    # headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # res = requests.post(token_url, data=payload, headers=headers)
    # data = res.json()

    # # ✅ Send token back to frontend
    # return JSONResponse(data)

# def callback(broker: str, code: str):
#     return {"broker": broker, "code": code}
