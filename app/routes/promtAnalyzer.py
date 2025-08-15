from fastapi import APIRouter, Depends, HTTPException, Request
from Core.dependencies import get_analyzer_service
from services.promptAnalyzerService import PromptAnalyzerService

router = APIRouter()

@router.get("/processPrompt")
def get_user_intent(
    prompt: str,
    request: Request,
    prompt_service: PromptAnalyzerService = Depends(get_analyzer_service)
):
    print("===controller==")
    headers = dict(request.headers)
    required = ["brokername"]
    missing = [key for key in required if key not in headers]
    if missing:
        raise HTTPException(status_code=401, detail={ "message": "failed", "status": "false", "error": "Headers are missing or brokername is empty" })        

    generator = prompt_service.processUserRequest(prompt, headers)
    return generator




