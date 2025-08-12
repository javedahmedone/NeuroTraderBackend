from app.Strategy.brokerFactory import BrokerFactory
from app.models.schemas import CancelOrderRequest
from app.services.geminiService import GeminiService
from app.global_constant import constants
from app.services.intentDetectionService import IntentDetectionService
from app.services.stockFetchingService import StockFetchingService

class PromptAnalyzerService():
    def __init__(self, intent_service: IntentDetectionService, stock_fetching_service: StockFetchingService , gemini_service: GeminiService):
        self.intent_service = intent_service
        self.stock_fetching_service = stock_fetching_service
        self.gemini_service =  gemini_service
        


    def processUserRequest(self, prompt: str, headers: dict):
        promptResult =  self.gemini_service.detect_intent(prompt)        
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
        if userIntent == "place_order": 
            response_data = self.__validateStockQuantity(data)
            if response_data["success"] is True:
                response_data = brokerFactory.place_order(headers, data, constants.BUY)
            response = {
                "userIntent": constants.BUYORDER,
                "data": response_data,
            }

        elif userIntent == "sell_order":
            response_data = self.__validateStockQuantity(data)
            if response_data["success"] is True:
                response_data = self.__placeOrder(brokerFactory, headers, data, constants.SELL )
                # response_data = brokerFactory.place_order(headers, data, constants.SELL)
            response = {
                "userIntent": constants.SELLORDER,
                "data": response_data
            }
        
        elif userIntent == "sell_all":
            response_data = []
            holdings_data = self.__getHoldings(brokerFactory,headers);
            for holding in holdings_data["data"]["holdings"]:
                qty = holding.get("quantity", 0)
                if qty and qty > 0:
                   response_data.append(self.__placeOrder(brokerFactory, headers, holding, constants.SELL ))
            response = {
                "userIntent": constants.SELLORDER,
                "data": response_data
            }

        elif userIntent == "get_orders":
            # response_data = brokerFactory.getOrders(headers,"")
            response_data = self.___getOrders(brokerFactory, headers)
            response = {
                "userIntent": constants.GETORDERS,
                "data": response_data
            }

        elif userIntent == "view_holdings" or userIntent == "get_total_holdings":
            response_data = self.__getHoldings(brokerFactory,headers)   
            # brokerFactory.getHoldings(headers, constants.USERPROMPT)
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

    def __validateStockQuantity(self,data):
        if not data :
            response = {"success":False,"message":"Please enter valid prompt", "error":"CODE01"}
        elif data.quantity is None or data.quantity == 0  :  
            response = {"success":False,"message":"Please enter valid stock quantity", "error":"CODE01"}
        elif data.symbol is None or data.symbol == 0  :  
            response = {"success":False,"message":"Please enter valid stock name", "error":"CODE01"}
        
        else:
            response = {"success":True}
        return response 
    
    def __getHoldings(self,brokerFactory,headers):
        return brokerFactory.getHoldings(headers, constants.USERPROMPT)

    def ___getOrders(self,brokerFactory,headers):
        return brokerFactory.getOrders(headers,"")
    
    def __placeOrder(self, brokerFactory, headers, data, transactionType: str):
        return brokerFactory.placeOrder(headers, data, transactionType)
    