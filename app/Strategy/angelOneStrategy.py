from datetime import timedelta
from SmartApi import SmartConnect
from fastapi import HTTPException
import pyotp
import requests
from Strategy.baseStrategy import BaseStrategy
from services.Common.CommonService import CommonService
from services.Common.ResponseBuilder import ResponseBuilder
from services.geminiService import GeminiService
from global_constant import constants
from models.schemas import CancelOrderRequest, LoginRequest, LoginResponse, StockOrderRequest, UserPromptRequest
from services.stockFetchingService import StockFetchingService


class AngelOneStrategy(BaseStrategy):
    def __init__(self):
        self.stockFetchService = StockFetchingService()
        self.geminiService =  GeminiService()
        self.service  = CommonService()


    def placeOrder(self, headers: dict, orderparams: StockOrderRequest, transactionType: str):
        try:
            result  = self.extract_required_headers(headers)
            if result is False:
                raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
            authorization =  headers["authorization"]
            price =0
            orderType = "MARKET"
            token = authorization.replace("Bearer ", "")
            smart_api = SmartConnect(api_key=headers["apikey"])
            smart_api.setAccessToken(token)
            smart_api.generateToken(headers["refresh"])
            if orderparams.limitPrice is not None and len(orderparams.limitPrice) > 0:
                price = float(orderparams.limitPrice[0])
                orderType = "LIMIT"
            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": orderparams.symbol,
                "symboltoken": orderparams.token,
                "transactiontype": transactionType.upper(),
                "exchange": "NSE",
                "ordertype": orderType,
                "producttype": "DELIVERY",
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": orderparams.quantity
            }
            response = smart_api.placeOrderFullResponse(orderparams)
            if  response["status"] != True:
                return ResponseBuilder().status(constants.ERROR).statusCode(400).errorMessage(response["message"]).build() 
            response = smart_api.individual_order_details(response["data"]["uniqueorderid"])
            data =   self.__mapPlaceOrderData(response)
            return ResponseBuilder().status(constants.SUCCESS).statusCode(200).data(data).build()
        
        except Exception as e:
                errorMessage = str(e)
                return ResponseBuilder().status(constants.ERROR).statusCode(400).errorMessage(errorMessage).build() 
    
    def getOrders(self, headers: dict, navigateFrom: str):
        authorization =  headers["authorization"]
        token = authorization.replace("Bearer ", "")
        smart_api = SmartConnect(api_key=headers["apikey"]) 
        smart_api.setAccessToken(token) 
        userOrders =  smart_api.orderBook()
        data  =  self.__mapfetchOrdersData(userOrders)
        if  userOrders["status"] != True:
            return ResponseBuilder().status(constants.ERROR).statusCode(400).errorMessage(userOrders["message"]).build()
        return ResponseBuilder().status(constants.SUCCESS).statusCode(200).data(data).build()

    def getHoldings(self, headers: dict, navigateFrom: str):
        result = self.extract_required_headers(headers)
        if result is False:
            raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")

        token = headers["authorization"].replace("Bearer ", "")
        smart_api = SmartConnect(api_key=headers["apikey"])
        smart_api.setAccessToken(token)
        try:
            holdingsData = smart_api.allholding()  
            if  holdingsData["errorcode"] != '':
                return ResponseBuilder().status(constants.ERROR).statusCode(401).build()

            print(holdingsData)          
            if holdingsData.get("status") is True and navigateFrom == constants.USERPROMPT:
                mapHoldingsData = self.__mapHoldingsData(holdingsData)
                data = mapHoldingsData
            else:
                data = holdingsData["data"]

            if  holdingsData["status"] != True:
                return ResponseBuilder().status(constants.ERROR).statusCode(400).errorMessage(holdingsData["message"]).build()
            return ResponseBuilder().status(constants.SUCCESS).statusCode(200).data(data).build()
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
        print(userHoldings)
        data = self.geminiService.processUserRequest(userHoldings, userPrompt)
        return data
    
    def cancelOrder(self, headers:dict, data: UserPromptRequest, userPrompt: str):
        result  = self.extract_required_headers(headers)
        if result is False:
            raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
        
        authorization = headers["authorization"]
        token = authorization.replace("Bearer ", "")
        smart_api = SmartConnect(api_key=headers["apikey"])
        smart_api.setAccessToken(token)
        if userPrompt == constants.NUll :
            print("===cancelOrder===",  data.orderIds[0])
            cancelRequest = CancelOrderRequest (
                variety="NORMAL",
                orderid= data.orderIds[0]
            )
        else:
            cancelRequest= CancelOrderRequest (
                variety="NORMAL",
                orderid= data.orderid
            )
        try:
            result = smart_api.cancelOrder(cancelRequest.orderid, cancelRequest.variety)  
            print(result)
            if  result["status"] != True:
                return ResponseBuilder().status(constants.ERROR).statusCode(400).errorMessage(result["message"] + " or order is already cancelled").build()
            return ResponseBuilder().status(constants.SUCCESS).statusCode(200).data("order is successfully cancelled").build()
        except Exception as e:
            raise HTTPException(status_code=500, detail="Unexpected error in AngelOne strategy: " + str(e))

    def cancelAllOrders(self, headers:dict):
        orders_data = self.getOrders(headers,constants.NUll)
        for order in orders_data:
            orderStatus = order.get("status")
            if orderStatus and orderStatus.lower() == "open":
                obj = CancelOrderRequest(
                    variety="NORMAL",
                    orderid=order.get("orderid")
                )
                self.cancelOrder(headers, obj, None)
        return self.getOrders(headers,constants.NUll)

    def marketData(self, headers:dict,exchange: str, stockSymbol: str, token: str, isinNumber: str, interval:str):
        result  = self.extract_required_headers(headers)
        if result is False:
            raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
        
        authToken = headers["authorization"].replace("Bearer ", "")
        smart_api = SmartConnect(api_key=headers["apikey"])
        smart_api.setAccessToken(token)                
        url = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"
        headers = {
        'X-PrivateKey': headers["apikey"],
        'Accept': 'application/json',
        'X-SourceID':  smart_api.sourceID, 
        'X-ClientLocalIP': smart_api.clientLocalIp,
        'X-ClientPublicIP':  smart_api.clientPublicIP,
        'X-MACAddress': smart_api.clientMacAddress,
        #   'X-UserType': 'USER',
        'Authorization': headers["authorization"],
        'Accept': 'application/json',
        'Content-Type': 'application/json'
        }
        todayDate = self.service.currentIstTime().strftime("%Y-%m-%d")
        if(interval == constants.ONEWEEK):
            intervalTime = "FIVE_MINUTE"
        elif(interval == constants.ONEMONTH):
            intervalTime = "THIRTY_MINUTE"
        else:
            intervalTime = "ONE_MINUTE"
        fromDate = self.service.fetchFromDate(todayDate,interval) 
        payload = {
            "exchange": "NSE",
            "symboltoken": token,
            "interval": intervalTime,
            "fromdate": fromDate,
            "todate": todayDate + " 15:30"
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == False or result.get("success") is False:
                statusCode = 400
                message = result.get("message")
                if message == "Invalid Token":
                    statusCode = 401
                return ResponseBuilder().status(constants.ERROR).statusCode(statusCode).errorMessage(result["message"]).build()
            print(result.get("data"))
            return ResponseBuilder().status(constants.SUCCESS).statusCode(200).data(result.get("data")).build()
        else:
            print(f"Error: status code = {response.status_code}")
            print(response.text)     
    
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
        transactionType = constants.BUY if userOrders["data"]["transactiontype"].upper() == constants.BUY else constants.SELL

        ordersData = {
            "symbol": symbol,
            "name": data.name,
            "quantity": userOrders["data"]["quantity"],
            "status": userOrders["data"]["status"],
            "orderstatus": userOrders["data"]["orderstatus"],
            "text": userOrders["data"]["text"],
            "orderid": userOrders["data"]["orderid"],
            "transactiontype": transactionType,
            "orderType": userOrders["data"]["ordertype"],
            "price": userOrders["data"]["price"]

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
            transactionType = constants.BUY if item["transactiontype"].upper() == constants.BUY else constants.SELL
            obj = {
                "symbol": symbol,
                "name": stock_info.name.upper(),  # Assuming it's a Pydantic model or object
                "quantity": item["quantity"],
                "status": item["status"],
                "orderstatus": item["orderstatus"],
                "text": item["text"],
                "orderid": item["orderid"],
                "transactiontype": transactionType,
                "updatetime": item["updatetime"],
                "orderType": item["ordertype"],
                "price": item["price"]
            }
            holdings.append(obj)
        return holdings
