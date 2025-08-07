
# from fastapi import APIRouter, Depends, HTTPException, Request
# from Core.dependencies import get_analyzer_service
# from services.promptAnalyzerService import PromptAnalyzerService
# router = APIRouter()

# @router.get("/processPrompt")
# def get_user_intent(
#     prompt: str,
#     request: Request,
#     prompt_service: PromptAnalyzerService = Depends(get_analyzer_service)
# ):
#     # try:
#         headers = dict(request.headers)
#         required = ["brokername"]
#         missing = [key for key in required if key not in headers]
#         if missing:
#             raise ValueError(f"Missing required headers brokerName: {', '.join(missing)}")    
#         return prompt_service.processUserRequest(prompt, headers)
#     # except Exception as e:
#     #     print("❌ Error during intent detection:", str(e))
#     #     raise HTTPException(status_code=500, detail="Intent detection failed: " + str(e))



from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from Core.dependencies import get_analyzer_service
from services.promptAnalyzerService import PromptAnalyzerService

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

    # Call the service which returns a generator
    generator = prompt_service.processUserRequest(prompt, headers)
    return generator
    # return StreamingResponse(generator, media_type="text/plain")




