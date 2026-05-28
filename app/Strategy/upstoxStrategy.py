from app.config import config
from app.logging_config import get_logger
import requests
import json
from typing import Dict
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.services.Common.MongoClientService import MongoClientService
from app.services.Common.httpClient import HttpClient
from app.strategy.baseStrategy import BaseStrategy  # ✅ ADD app.
from app.services.Common.HeaderBuilder import HeaderBuilder
from app.services.Common.ResponseBuilder import ResponseBuilder
from app.services.geminiService import GeminiService
from app.globalConstant import constants
from app.models.schemas import CancelOrderRequest, LoginRequest, LoginResponse, ResponseModel, StockOrderRequest, UserPromptRequest
from app.services.stockFetchingService import StockFetchingService
from app.globalConstant.BrokerUrl import upstoxUrl
import requests
import json

logger = get_logger(__name__)

class UpstoxStrategy(BaseStrategy):
    """Upstox broker trading strategy"""
    
    def __init__(self):
        """Initialize Upstox strategy"""
        self.api_key = config.UPSTOX_API_KEY
        self.redirect_uri = config.UPSTOX_REDIRECT_URI
        self.backend_url = config.BACKEND_URL
        self.frontend_url = config.FRONTEND_URL
        
        logger.info("✅ UpstoxStrategy initialized", extra={
            "redirect_uri": self.redirect_uri,
            "backend_url": self.backend_url
        })
        
        self.stockFetchService = StockFetchingService()
        self.geminiService =  GeminiService()
        self._mongoService =  MongoClientService()  
        self._httpClient = HttpClient()

    def get_login_url(self) -> str:
        try:
            if not self.api_key:
                raise ValueError("UPSTOX_API_KEY not configured")
            
            login_url = f"https://api.upstox.com/index/dialog/authorize?apikey={self.api_key}&redirect_uri={self.redirect_uri}"
            
            logger.info("✅ Generated Upstox login URL", extra={
                "url": login_url[:50] + "..."
            })
            
            return login_url
            
        except Exception as e:
            logger.error("❌ Error generating login URL", extra={
                "error": str(e)
            }, exc_info=True)
            raise
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from Upstox
            
        Returns:
            Dict: Token response
        """
        try:
            if not code:
                raise ValueError("Authorization code is required")
            
            # Exchange code for token
            token_url = "https://api.upstox.com/login/process/token"
            
            payload = {
                "code": code,
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code"
            }
            
            logger.info("Exchanging authorization code for token", extra={
                "code": code[:10] + "..."
            })
            
            response = requests.post(token_url, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            
            logger.info("✅ Token exchange successful", extra={
                "access_token": token_data.get("access_token", "")[:20] + "..."
            })
            
            return token_data
            
        except Exception as e:
            logger.error("❌ Error exchanging code for token", extra={
                "error": str(e)
            }, exc_info=True)
            raise
    
    def get_user_profile(self, access_token: str) -> Dict:
        """
        Get user profile from Upstox
        
        Args:
            access_token: OAuth access token
            
        Returns:
            Dict: User profile data
        """
        try:
            profile_url = "https://api.upstox.com/user/profile"
            
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            response = requests.get(profile_url, headers=headers)
            response.raise_for_status()
            
            profile = response.json()
            
            logger.info("✅ Retrieved user profile", extra={
                "user_id": profile.get("user_id", "unknown")
            })
            
            return profile
            
        except Exception as e:
            logger.error("❌ Error retrieving user profile", extra={
                "error": str(e)
            }, exc_info=True)
            raise

    def placeOrder(self, headers: dict, orderparams: StockOrderRequest, transactionType: str):
        try:
            result  = self.extract_required_headers(headers)
            if result is False:
                raise ValueError("Missing required headers: apikey, clientcode, authorization, refresh")
            authorization =  headers["authorization"]  
            price =0
            orderType = "MARKET" 
            if orderparams.isinNumber is None:
                orderparams.instrument_token = self._mongoService.fetchBySymbol(orderparams)
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

            headers = HeaderBuilder().with_content_type(constants.CONTENT_APPLICATION_JSON).with_auth(constants.BEARER + authorization) 
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
                    # placeOrderData.data = ordersData 
                    return ResponseBuilder().status(constants.SUCCESS).statusCode(200).data(ordersData).build()
                else:
                    return orderDetails
            return ResponseBuilder().status(constants.ERROR).statusCode(400).errorMessage(result["message"]).build()


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
        try:
            header_builder = HeaderBuilder()
            headers = header_builder.with_content_type(constants.CONTENT_APPLICATION_JSON).with_auth(constants.BEARER + headers["authorization"]).build()
            response = self._httpClient.get(upstoxUrl.GET_USER_HOLDINGS, headers=headers)
            jsonResponse = json.loads(response.text)
            if jsonResponse["status"] == constants.ERROR:
                return ResponseBuilder().status(constants.ERROR).statusCode(response.status_code).errorMessage(jsonResponse["errors"][0]["message"]).build()

            data = []
            if len(jsonResponse["data"]) > 0 :
                data = self.__mapHoldingsData(jsonResponse, navigateFrom)           
            return ResponseBuilder().status(constants.SUCCESS).statusCode(200).data(data).build()
        
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
        BackendUrl = config.BACKEND_URL

        payload = {
            'code': data.code,
            'client_id': data.apiKey,
            'client_secret': data.apiSecret,
            'redirect_uri': f"{BackendUrl}/auth/callback/upstox", #"http://localhost:3000/callback/upstox",
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
            errorMessage= "Missing required headers: apikey, clientcode, authorization, refresh"
            return ResponseBuilder().status(constants.ERROR).statusCode(400).errorMessage(errorMessage).build()

            # cancelOrderData = ResponseModel(
            #     status=constants.ERROR,
            #     statusCode=400,
            #     data=[],
            # )
            # return cancelOrderData
        
        authorization =  headers["authorization"]
        if userPrompt == constants.NUll :
            orderId = data["orderIds"][0] if isinstance(data["orderIds"], list) else data["orderIds"]
        else :
            orderId = data.orderid
        url = upstoxUrl.CANCEL_ORDER_BY_ORDERID+ orderId
        payload={}
        headers = {
            'Authorization':constants.BEARER + authorization,
            'Accept': 'application/json'
        }
        response = requests.request("DELETE",url , headers=headers, data=payload)
        result = json.loads(response.text)
        if result["status"] == constants.ERROR:
            errorMessage = "Order Id :"+orderId+result["errors"][0]["message"]
            return ResponseBuilder().status(constants.ERROR).statusCode(400).errorMessage(errorMessage).build()
        return ResponseBuilder().status(constants.SUCCESS).statusCode(200).data(result["data"]).build()

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

    def marketData(self, headers:dict,exchange: str, stockSymbol: str, token: str, isinNumber: str, interval:str):
        pass

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
        return ResponseBuilder().status(constants.SUCCESS).statusCode(200).data(result["data"]).build()

        
    def __mapHoldingsData(self, jsonResponse :any, navigateFrom):
        holdings = jsonResponse["data"]
        totalInValue = 0
        totalHoldingValue = 0
        total_profit_and_loss = 0
        for item in holdings:
            totalInValue += item["quantity"] * item["average_price"]
            totalHoldingValue += item["quantity"] * item["last_price"]

        total_profit_and_loss = totalHoldingValue - totalInValue
        total_pnl_percentage = ((total_profit_and_loss / totalInValue) * 100 if totalInValue > 0 else 0)

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
            data = self.__mapHoldingsData(data)