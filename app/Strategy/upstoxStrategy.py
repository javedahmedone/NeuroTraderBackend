from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from Strategy.baseStrategy import BaseStrategy
from services.geminiService import GeminiService
from global_constant import constants
from models.schemas import CancelOrderRequest, LoginRequest, LoginResponse, ResponseModel, StockOrderRequest, UserPromptRequest
from services.stockFetchingService import StockFetchingService
from global_constant.BrokerUrl import upstoxUrl
import requests
import json
class UpstoxStrategy(BaseStrategy):
    def __init__(self):
        self.stockFetchService = StockFetchingService()
        self.geminiService =  GeminiService()
        self.client = MongoClient(constants.MONGO_URL)
        self.db = self.client["stockdb"]            # Database name
        self.collection = self.db["companies"]      

    def placeOrder(self, headers: dict, orderparams: StockOrderRequest, transactionType: str):
        try:
            result  = self.extract_required_headers(headers)
            if result is False:
                raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
            authorization =  headers["authorization"]  
            price =0
            orderType = "MARKET" 
            if orderparams.isinNumber is None:
                orderparams.instrument_token = self.collection.find({ "symbol": orderparams.symbol.upper })
            if orderparams.limitPrice is not None and len(orderparams.limitPrice) > 0:
                price = float(orderparams.limitPrice[0])
                orderType = "LIMIT"

            orderparams = json.dumps({
                "quantity": orderparams.quantity,
                "product": "D",
                "validity": "DAY",
                "price": price,
                "tag": "string",
                "instrument_token": "NSE_EQ|"+orderparams.isinNumber,
                "order_type": orderType,
                "transaction_type": transactionType.upper(),
                "disclosed_quantity": 0,
                "trigger_price": 0,
                "is_amo": True,
                "slice": True
                })

            headers = {
                'Content-Type': 'application/json',
                'Authorization':constants.BEARER + authorization,
            }

            response = requests.request("POST", upstoxUrl.PLACE_ORDER, headers=headers, data=orderparams)
            result = json.loads(response.text)
            placeOrderData = ResponseModel(
                status=result["status"],
                statusCode=response.status_code,
                data=result,
            )
            if result["status"] == constants.SUCCESS: 
                orderId = result["data"]["order_ids"]
                orderDetails =  self.__orders(orderId, authorization)
                if orderDetails.status == constants.SUCCESS : 
                    ordersData =  self.__mapPlaceOrderData(orderDetails)
                    placeOrderData.data = ordersData 
                else:
                    return orderDetails
            else :
                placeOrderData.errorMessage = result["errors"][0]["message"]
            return placeOrderData

        except Exception as e:
            placeOrderData = ResponseModel(
                status=constants.ERROR,
                statusCode=401,
                data=[],
                userIntent= None
            )
            if "NoneType" in  str(e):
               return placeOrderData
            else:
                placeOrderData.errorMessage = str(e)
                placeOrderData.statusCode=400
            return placeOrderData
    
    def getOrders(self, headers: dict, navigateFrom: str):
        authorization = headers["authorization"]   
        ordersData =  self.__orders("",authorization)
        if ordersData.status == constants.ERROR:
            return ordersData
        ordersData.data = self.__mapfetchOrdersData(ordersData.data)
        return ordersData
        

    def getHoldings(self, headers: dict, navigateFrom: str):
        result = self.extract_required_headers(headers)
        if result is False:
            raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
        authorization = headers["authorization"]       
        try:
            payload={}
            headers = {
                'Authorization':constants.BEARER + authorization,
                'Accept': 'application/json'
            }
            response = requests.request("GET", upstoxUrl.GET_USER_HOLDINGS, headers=headers, data=payload)
            jsonResponse = json.loads(response.text)
            holdingsData = ResponseModel(
                status = jsonResponse["status"],
                statusCode = response.status_code,
                data = jsonResponse["data"],
                userIntent = None
            )
            print(len(holdingsData.data))
            if jsonResponse["status"] == constants.ERROR or len(holdingsData.data) == 0 :
                return holdingsData            
            holdings = jsonResponse["data"]
            totalInValue = 0
            totalHoldingValue = 0
            total_profit_and_loss = 0
            for item in holdings:
                totalInValue += item["quantity"] * item["average_price"]
                totalHoldingValue += item["quantity"] * item["last_price"]

            total_profit_and_loss = totalHoldingValue - totalInValue
            total_pnl_percentage = (
                (total_profit_and_loss / totalInValue) * 100 if totalInValue > 0 else 0
            )

            jsonResponse["data"] = {
                "holdings": holdings,
                "totalholding": {
                    "totalholdingvalue": round(totalHoldingValue, 2),
                    "totalinvvalue": round(totalInValue, 2),
                    "totalprofitandloss": round(total_profit_and_loss, 2),
                    "totalpnlpercentage": round(total_pnl_percentage, 2)
                }
            }
            data = JSONResponse(content=jsonResponse)
            if navigateFrom == constants.USERPROMPT :
                holdings.data = self.__mapHoldingsData(data)
            else :
                holdingsData.data = data
            return holdingsData
        
        except HTTPException as http_err:
            raise http_err  # Don't wrap again
        except Exception as e:
            raise HTTPException(status_code=500, detail="Unexpected error in Upstox strategy: " + str(e))

    def get_profile(self, headers: dict):
        result  = self.extract_required_headers(headers)
        if result is False:
            raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
        authorization =  headers["authorization"]
        payload={}
        headers = {
        'Authorization':constants.BEARER + authorization,
        'Accept': 'application/json'
        }
        response = requests.request("GET", upstoxUrl.GET_USER_PROFILE, headers=headers, data=payload)
        jsonResponse = json.loads(response.text)
        profileData = ResponseModel(
                status = jsonResponse["status"],
                statusCode = response.status_code,
                data = jsonResponse,
                userIntent = None
        )
        return profileData
    
    def login(self, data: LoginRequest): # -> LoginResponse:
        payload = {
            'code': data.code,
            'client_id': data.apiKey,
            'client_secret': data.apiSecret,
            'redirect_uri': "http://localhost:3000/callback/upstox",
            'grant_type': 'authorization_code'
        }
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
        }

        response = requests.request("POST",upstoxUrl.GET_TOKEN_URL , headers=headers, data=payload)
        result = response.text
        print(response.text)
        result = response.json()   # ✅ dict, not str

            # Now you can safely access keys
        return LoginResponse(
                jwt=result.get("access_token"),
                userName=result.get("user_name")
            )
       
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
    
    def cancelOrder(self, headers:dict, data: UserPromptRequest, userPrompt: str):
        result  = self.extract_required_headers(headers)
        if result is False:
            cancelOrderData = ResponseModel(
                status=constants.ERROR,
                statusCode=400,
                data=[],
                errorMessage= "Missing required headers: apikey, clientcode, authorization, refresh"
            )
            return cancelOrderData
        
        authorization =  headers["authorization"] 
        orderId =   data.orderIds[0] 
        url = upstoxUrl.CANCEL_ORDER_BY_ORDERID+ orderId
        payload={}
        headers = {
            'Authorization':constants.BEARER + authorization,
            'Accept': 'application/json'
        }
        response = requests.request("DELETE",url , headers=headers, data=payload)
        result = json.loads(response.text)
        cancelOrderData = ResponseModel(
                status=result["status"],
                statusCode=response.status_code,
                data=result,
                userIntent= None,
        )
        if cancelOrderData.status == constants.ERROR:
            cancelOrderData.errorMessage = "Order Id :"+orderId+result["errors"][0]["message"]
        return cancelOrderData

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
            
    def __mapHoldingsData(self, holdingsData):
        holdings = []
        userHoldings = holdingsData  #["data"]["holdings"]
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
        userOrders = userOrders.data
        symbol =  userOrders["tradingsymbol"]
        data = self.stockFetchService.getStockByKey(symbol,0)
        ordersData = {
            "symbol": symbol,
            "name": data.name,
            "quantity": userOrders["quantity"],
            "status": userOrders["status"],
            "orderstatus": userOrders["status"],
            "text": userOrders["status_message"],
            "orderid": userOrders["order_id"],
            "transactiontype": userOrders["transaction_type"],
            "orderType": userOrders["order_type"]
        }
        return ordersData
    
    def __mapfetchOrdersData(self, userOrders):
        holdings = []
        userOrdersData = userOrders if isinstance(userOrders, list) else [userOrders]
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
                "orderstatus": item["status"],
                "text": item["status_message"],
                "orderid": item["order_id"],
                "transactiontype": item["transaction_type"],
                "updatetime": item["order_timestamp"],
                "orderType": item["order_type"]
            }
            holdings.append(obj)
        return holdings

    def __orders(self, orderId , authorization: str):
        url = ''
        if len(orderId) > 0 :
            url = upstoxUrl.GET_ORDER+orderId[0]
        else:
            url =  upstoxUrl.GET_ALL_ORDER
        payload={}
        headers = {
            'Accept': 'application/json',
            'Authorization': constants.BEARER + authorization
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        result =  json.loads(response.text)
        
        ordersData = ResponseModel(
            status=result["status"],
            statusCode=response.status_code,
            data=result["data"],
            userIntent= None
        )
        return ordersData
        
