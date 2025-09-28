from Strategy.brokerFactory import BrokerFactory
from models.schemas import UserPromptRequest
from services.Common.ResponseBuilder import ResponseBuilder
from services.geminiService import GeminiService
from global_constant import constants, errorMessageConstants
from services.intentDetectionService import IntentDetectionService
from services.stockFetchingService import StockFetchingService

class PromptAnalyzerService():
    def __init__(self, intent_service: IntentDetectionService, stock_fetching_service: StockFetchingService , gemini_service: GeminiService):
        self.intent_service = intent_service
        self.stock_fetching_service = stock_fetching_service
        self.gemini_service =  gemini_service

    def processUserRequest(self, prompt: str, headers: dict):
        promptResult =  self.gemini_service.detect_intent(prompt)  
        promptObject = UserPromptRequest(
            userIntent= promptResult.get("intent"),
            quantity=0,
            stock_name=[],
            orderIds = promptResult.get("orderids", []),
            symbol=None,
            token=0,
            isinNumber = None,
            limitPrice=promptResult.get("limitPrice") or []  # ✅ ensures list, not None
        )
        if promptObject.userIntent is constants.PLACE_ORDER_PROMPT or promptObject.userIntent is constants.SELL_ORDER_PROMPT:   
            validatePromptData = self.__validatePromptData(promptResult)
            return ResponseBuilder().status(constants.ERROR).statusCode(400).errorMessage(validatePromptData).userIntent(constants.VALIDATIONERROR).build()
        if promptResult["stock_name"] is not None and  len(promptResult["stock_name"]) == 1:
            stockData = self.stock_fetching_service.extract_stock_from_prompt(promptResult["stock_name"])
            promptObject.stock_name = stockData.name
            promptObject.quantity = promptResult["quantity"]  # if it's a model, use dot notation
            promptObject.symbol = stockData.symbol
            promptObject.token = stockData.token 
            promptObject.isinNumber =  stockData.isinNumber  

        print("==updated datat  ==",promptResult)
        performAction = self.performAction(promptResult, promptObject, headers, prompt)
        return performAction
    
    def performAction(self, promptResult, data:UserPromptRequest, headers, prompt): 
        userIntent = promptResult["intent"]
        brokerName = headers["brokername"]
        brokerFactory = BrokerFactory(brokerName).get_broker()
        response = {}
        if userIntent == constants.PLACE_ORDER_PROMPT: 
            response_data = self.__validateStockQuantity(data)
            if response_data["success"] is True:
                response_data = brokerFactory.placeOrder(headers, data, constants.BUY)
                response_data.userIntent = constants.BUYORDER
            return response_data

        elif userIntent == constants.SELL_ORDER_PROMPT:
            response_data = self.__validateStockQuantity(data)
            if response_data["success"] is True:
                response_data = self.__placeOrder(brokerFactory, headers, data, constants.SELL )
                response_data.userIntent = constants.SELLORDER
            return response_data
       
        elif userIntent == constants.SELL_ALL_PROMPT:
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

        elif userIntent == constants.GET_ORDERS_PROMPT:
            response_data = self.___getOrders(brokerFactory, headers)
            response_data.userIntent = constants.GETORDERS
            return response_data

        elif userIntent == constants.VIEW_HOLDING_PROMPT or userIntent == constants.GET_TOTAL_HOLDINGS_PROMPT:
            response_data = self.__getHoldings(brokerFactory,headers)
            response_data.userIntent = constants.HOLDINGS
            return response_data 

        elif userIntent == constants.ANALYZE_PORTFOLIO_PROMPT:
            response_data = brokerFactory.portfolioAnalysis(headers, prompt)
            response = {
                "userIntent": constants.ANALYZE_PORTFOLIO,
                "data": response_data
            }
        elif userIntent == constants.CANCEL_ORDER_PROMPT:
            response_data = brokerFactory.cancelOrder(headers, data, constants.NUll)
            response_data.userIntent = constants.CANCELORDER
            return response_data
        
        elif userIntent == constants.CANCEL_ALL_ORDERS_PROMPT:
            response_data = brokerFactory.cancelAllOrders(headers)  # ✅ fixed          
            response = {
                "userIntent": constants.CANCELALLORDERS,
                "data": response_data
            }

        else :
            response = {
                "userIntent": constants.UNKNOWN,
                "data": []
            }

        return response

    def __validateStockQuantity(self,data):
        if not data:
            return {"success": False, "message": "Invalid request format, Please give proper stock name and quantity ","error": "CODE01" }
        if len(data.symbol) == 0  or not data.symbol:
            return {"success": False, "message": "Invalid request format, Please give proper stock name","error": "CODE01" }
        elif data.quantity is None or data.quantity == 0  :  
            response = {"success":False,"message":"Please enter valid stock quantity", "error":"CODE01"}
        else:
            response = {"success":True}
        return response 
    
    def __getHoldings(self,brokerFactory,headers):
        return brokerFactory.getHoldings(headers, constants.USERPROMPT)

    def ___getOrders(self,brokerFactory,headers):
        return brokerFactory.getOrders(headers,"")
    
    def __placeOrder(self, brokerFactory, headers, data, transactionType: str):
        return brokerFactory.placeOrder(headers, data, transactionType)
    
    def __validatePromptData(self, promptResult: any):
        userIntent = promptResult.get("intent")
        if userIntent == "place_order" or userIntent == "sell_order":
            if promptResult["stock_name"] is  None :
                return errorMessageConstants.INVALIDSTOCKNAME
            elif promptResult["quantity"] is None or promptResult["quantity"] <0:
                return errorMessageConstants.INVALIDQUANTITY
        elif promptResult["limitPrice"] is None or len(promptResult["limitPrice"]) > 1:
            return errorMessageConstants.INVALIDLIMITPRICE
        return None