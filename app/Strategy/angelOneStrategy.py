from SmartApi import SmartConnect
from fastapi import HTTPException
import pyotp
from Strategy.baseStrategy import BaseStrategy
from services.geminiService import GeminiService
from global_constant import constants
from models.schemas import CancelOrderRequest, LoginRequest, LoginResponse, StockOrderRequest
from services.stockFetchingService import StockFetchingService


class AngelOneStrategy(BaseStrategy):
    def __init__(self):
        self.stockFetchService = StockFetchingService()
        self.geminiService =  GeminiService()

    def placeOrder(self, headers: dict, orderparams: StockOrderRequest, transactionType: str):
        try:
            result  = self.extract_required_headers(headers)
            if result is False:
                raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
            authorization =  headers["authorization"]
            token = authorization.replace("Bearer ", "")
            smart_api = SmartConnect(api_key=headers["apikey"])
            smart_api.setAccessToken(token)
            smart_api.generateToken(headers["refresh"])
            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": orderparams.symbol,
                "symboltoken": orderparams.token,
                "transactiontype": transactionType.upper(),
                "exchange": "NSE",
                "ordertype": "MARKET",
                "producttype": "DELIVERY",
                "duration": "DAY",
                "price": "0",
                "squareoff": "0",
                "stoploss": "0",
                "quantity": orderparams.quantity
            }

            response = smart_api.placeOrderFullResponse(orderparams)
            if not response.get("status", False):
                return {
                    "success": False,
                    "message": response.get("message"),
                    "errorcode": response.get("errorcode"),
                    "data": response.get("data")
                }
            response = smart_api.individual_order_details(response["data"]["uniqueorderid"])
            return  self.__mapPlaceOrderData(response)
        except Exception as e:
        # Generic fallback — won't crash if `response` is undefined
            return {
                "success": False,
                "message": locals().get("response", {}).get("message", "Unexpected error"),
                "error": str(e)
            }
    
    def getOrders(self, headers: dict, navigateFrom: str):
        authorization =  headers["authorization"]
        token = authorization.replace("Bearer ", "")
        smart_api = SmartConnect(api_key=headers["apikey"]) 
        smart_api.setAccessToken(token) 
        userOrders =  smart_api.orderBook()
        if userOrders.get('errorcode') != '':
            return userOrders
        data  =  self.__mapfetchOrdersData(userOrders)
        return data

    def getHoldings(self, headers: dict, navigateFrom: str):
        result = self.extract_required_headers(headers)
        if result is False:
            raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")

        authorization = headers["authorization"]
        token = authorization.replace("Bearer ", "")
        smart_api = SmartConnect(api_key=headers["apikey"])
        smart_api.setAccessToken(token)
        try:
            holdingsData = smart_api.allholding()  
            print(holdingsData)          
            if holdingsData.get("status") is True and navigateFrom == constants.USERPROMPT:
                mapHoldingsData = self.__mapHoldingsData(holdingsData)
                return mapHoldingsData
            return holdingsData

        except HTTPException as http_err:
            raise http_err  # Don't wrap again
        except Exception as e:
            raise HTTPException(status_code=500, detail="Unexpected error in AngelOne strategy: " + str(e))

    def get_profile(self, headers: dict):
        result  = self.extract_required_headers(headers)
        if result is False:
            raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
        authorization =  headers["authorization"]
        token = authorization.replace("Bearer ", "")
        smart_api = SmartConnect(api_key=headers["apikey"])
        smart_api.setAccessToken(token)
        try:
            return smart_api.getProfile(headers["refresh"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def login(self, data: LoginRequest) -> LoginResponse:
        smart_api = SmartConnect(api_key=data.apiKey)
        totp = pyotp.TOTP(data.totp).now()
        session = smart_api.generateSession(data.clientcode, data.password, totp)
        print("Session data:", session)
        if not session["status"]:
            raise HTTPException(status_code=401, detail="Login failed: " + session["message"])
        jwt = session["data"]["jwtToken"]
        refresh = session["data"]["refreshToken"]
        clientCode = session["data"]["clientcode"]
        name =  session["data"]["name"]
        feedToken = session["data"]["feedToken"]
        return LoginResponse(clientCode=clientCode, jwt=jwt, refreshToken=refresh,userName=name, feedToken=feedToken)

    def extract_required_headers(self, headers: dict) -> bool:
        required = ["apikey", "clientcode", "authorization", "refresh"]
        missing = [key for key in required if key not in headers]
        if missing:
            return False
        return True

    def portfolioAnalysis(self, headers:dict, userPrompt: str):
        result  = self.extract_required_headers(headers)
        if result is False:
            raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
        userHoldings = self.getHoldings(headers, constants.NUll)
        data = self.geminiService.processUserRequest(userHoldings, userPrompt)
        return data
    
    def cancelOrder(self, headers:dict, cancelRequest: CancelOrderRequest, userPrompt: str):
        result  = self.extract_required_headers(headers)
        if result is False:
            raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
        
        authorization = headers["authorization"]
        token = authorization.replace("Bearer ", "")
        smart_api = SmartConnect(api_key=headers["apikey"])
        smart_api.setAccessToken(token)
        try:
            result = smart_api.cancelOrder(cancelRequest.orderid, cancelRequest.variety)  
            print(result)
            return result;
        except Exception as e:
            raise HTTPException(status_code=500, detail="Unexpected error in AngelOne strategy: " + str(e))


    def __mapHoldingsData(self, holdingsData):
        holdings = []
        userHoldings = holdingsData["data"]["holdings"]
        for holding in userHoldings:
            symbol = holding["tradingsymbol"]
            stock_info = self.stockFetchService.getStockByKey(symbol.lower(), 0)
            obj = {
                "symbol": symbol,
                "name": stock_info.name.upper(),
                "quantity": holding["quantity"],
                "average_price": holding["averageprice"],
                "current_price": holding["ltp"]
            }
            holdings.append(obj)
        return holdings
    
    def __mapPlaceOrderData(self, userOrders):
        ordersData = []
        print("==147==",userOrders["data"])
        symbol =  userOrders["data"]["tradingsymbol"]
        data = self.stockFetchService.getStockByKey(symbol,0)
        ordersData = {
            "symbol": symbol,
            "name": data.name,
            "quantity": userOrders["data"]["quantity"],
            "status": userOrders["data"]["status"],
            "orderstatus": userOrders["data"]["orderstatus"],
            "text": userOrders["data"]["text"],
            "orderid": userOrders["data"]["orderid"],
            "transactiontype": userOrders["data"]["transactiontype"]

        }
        return ordersData
    
    def __mapfetchOrdersData(self, userOrders):
        holdings = []
        userOrdersData = userOrders["data"]  # Access the nested data list
        print(userOrdersData)
        if userOrdersData is None:
            return []
        for item in userOrdersData:
            symbol = item["tradingsymbol"]  # Correct key from input JSON
            stock_info = self.stockFetchService.getStockByKey(symbol.lower(), 0)
            obj = {
                "symbol": symbol,
                "name": stock_info.name.upper(),  # Assuming it's a Pydantic model or object
                "quantity": item["quantity"],
                "status": item["status"],
                "orderstatus": item["orderstatus"],
                "text": item["text"],
                "orderid": item["orderid"],
                "transactiontype": item["transactiontype"],
                "updatetime": item["updatetime"]
            }
            holdings.append(obj)
        return holdings
