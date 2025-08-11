from fastapi import APIRouter, Depends, HTTPException, Request
from app.Core.dependencies import get_analyzer_service
from app.services.promptAnalyzerService import PromptAnalyzerService

router = APIRouter()

@router.get("/processPrompt")
async def get_user_intent(
    prompt: str,
    request: Request,
    prompt_service: PromptAnalyzerService = Depends(get_analyzer_service)
):
    headers = dict(request.headers)
    required = ["brokername"]
    missing = [key for key in required if key not in headers]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required headers brokerName: {', '.join(missing)}")

    generator = prompt_service.processUserRequest(prompt, headers)
    return generator




