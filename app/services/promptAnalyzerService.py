from Strategy.brokerFactory import BrokerFactory
from models.schemas import CancelOrderRequest
from services.geminiService import GeminiService
from global_constant import constants
from services.intentDetectionService import IntentDetectionService
from services.stockFetchingService import StockFetchingService

class PromptAnalyzerService():
    def __init__(self, intent_service: IntentDetectionService, stock_fetching_service: StockFetchingService , gemini_service: GeminiService):
        self.intent_service = intent_service
        self.stock_fetching_service = stock_fetching_service
        self.gemini_service =  gemini_service


    def processUserRequest(self, prompt: str, headers: dict):
        promptResult =  self.gemini_service.detect_intent(prompt)
        print("==16====",promptResult)
        return
        data = []
        if promptResult["stock_name"] is not None:
            data = self.stock_fetching_service.extract_stock_from_prompt(promptResult["stock_name"])
            data.quantity = promptResult["quantity"]
        print("==updated datat  ==",data)
        performAction = self.performAction(promptResult, data, headers, prompt)
        return performAction
    
    def performAction(self, promptResult, data, headers, prompt): 
        userIntent = promptResult["intent"]
        brokerName = headers["brokername"]
        brokerFactory = BrokerFactory(brokerName).get_broker()
        response = {}
        print("==userintent======",userIntent)
        if userIntent == "place_order": 
            response_data = brokerFactory.place_order(headers, data, constants.BUY)
            response = {
                "userIntent": constants.BUYORDER,
                "data": response_data
            }

        elif userIntent == "sell_order":
            response_data = brokerFactory.place_order(headers, data, constants.SELL)
            response = {
                "userIntent": constants.SELLORDER,
                "data": response_data
            }

        elif userIntent == "get_orders":
            response_data = brokerFactory.getOrders(headers,"")
            response = {
                "userIntent": constants.GETORDERS,
                "data": response_data
            }

        elif userIntent == "view_holdings" or userIntent == "get_total_holdings":
            response_data = brokerFactory.getHoldings(headers, constants.USERPROMPT)
            response = {
                "userIntent": constants.HOLDINGS,
                "data": response_data
            }

        elif userIntent == "analyze_portfolio":
            response_data = brokerFactory.portfolioAnalysis(headers, prompt)
            response = {
                "userIntent": constants.ANALYZE_PORTFOLIO,
                "data": response_data
            }
        elif userIntent == "cancel_order":
            obj =  CancelOrderRequest()
            obj.variety = "NORMAL",
            obj.orderid = promptResult["orderid"]
            response_data = brokerFactory.cancelOrder(headers, obj, constants.NUll)
            response = {
                "userIntent": constants.CANCELORDER,
                "data": response_data
            }
        else :
            response = {
                "userIntent": constants.UNKNOWN,
                "data": []
            }

        return response
