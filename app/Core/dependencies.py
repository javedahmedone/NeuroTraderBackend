
from fastapi import Header
from fastapi.params import Depends
from services.geminiService import GeminiService
from services.intentDetectionService import IntentDetectionService
from services.promptAnalyzerService import PromptAnalyzerService
from services.stockFetchingService import StockFetchingService

def get_intent_detection_service():
    return IntentDetectionService()

def get_stock_service():
    return StockFetchingService()

def get_gemini_service():
    return GeminiService()

def get_analyzer_service(
    intent_service: IntentDetectionService = Depends(get_intent_detection_service),
    stock_fetching_service: StockFetchingService = Depends(get_stock_service),
    gemini_service : GeminiService = Depends(get_gemini_service)

):
    return PromptAnalyzerService(intent_service, stock_fetching_service, gemini_service)



