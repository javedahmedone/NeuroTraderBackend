from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.models.schemas import LoginRequest
from app.services.brokerService import BrokerService
from app.config import config
from app.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

router = APIRouter()


@router.post("/login")
def login(request: LoginRequest):
    """
    Handle user login request
    
    Args:
        request: LoginRequest containing brokerName
        
    Returns:
        Login response from broker service
        
    Raises:
        HTTPException: If login fails
    """
    try:
        logger.info("✅ Received LoginRequest", extra={
            "broker_name": request.brokerName,
            "request_body": request.dict()
        })
        
        service = BrokerService(request.brokerName)
        response = service.login(request)
        
        logger.info("✅ Login successful", extra={"broker_name": request.brokerName})
        return response
        
    except Exception as e:
        logger.error("❌ Error during login", extra={
            "error": str(e),
            "broker_name": request.brokerName
        }, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/callback/{broker}")
def callback(request: Request, code: str = None):
    """
    Handle OAuth callback from broker
    
    Args:
        request: FastAPI request object
        code: Authorization code from broker
        
    Returns:
        RedirectResponse to frontend callback URL
    """
    try:
        # Extract broker name from path
        broker_name = request.path_params.get('broker', 'unknown')
        
        logger.info("✅ Callback received", extra={
            "broker_name": broker_name,
            "code_received": bool(code)
        })
        
        # Get URLs from config (NOT calling as function)
        frontend_url = config.FRONTEND_URL
        backend_url = config.BACKEND_URL
        
        logger.debug("Backend URLs", extra={
            "frontend_url": frontend_url,
            "backend_url": backend_url,
            "broker_name": broker_name
        })
        
        # Build redirect URL
        react_url = f"{frontend_url}/callback/{broker_name}?code={code}"
        
        logger.info("Redirecting to frontend", extra={
            "redirect_url": react_url,
            "broker_name": broker_name
        })
        
        return RedirectResponse(url=react_url)
        
    except Exception as e:
        logger.error("❌ Error in callback", extra={
            "error": str(e),
            "broker_name": request.path_params.get('broker', 'unknown')
        }, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Callback handling failed: {str(e)}"
        )
