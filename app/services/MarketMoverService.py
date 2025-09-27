from typing import List
from HttpClient.httpClient import HttpClient
from global_constant import constants
from models.schemas import MarketData, ResponseModel
import json
from config import REDIS_URL
from services.redisClientService import RedisClientService
from services.stockFetchingService import StockFetchingService as stockFetchingService
class MarketMoverService:

    def __init__(self):
        self._stockFetchingService = stockFetchingService()
        self._httpClient = HttpClient()
        self._redis = RedisClientService()


    def fetch_nse_gainers(self):
        cached_data = self._redis.get(constants.CACHE_KEY)
        if cached_data is not None:
            return ResponseModel(
                status=constants.SUCCESS,
                statusCode=200,
                data=cached_data,
                # fromCache=True
            )
        headers = {
            'Accept': 'application/json',
        }
        gainersTempData = []
        losersTempData = []
        response = self._httpClient.get(constants.MARKETMOVERAPI, headers=headers) 
        if response.status_code  != 200:
            return  ResponseModel(
                status=constants.ERROR,
                statusCode=400,
                data=[],
                userIntent=constants.VALIDATIONERROR,
                errorMessage= result.error
            )
        result =  json.loads(response.text)['data']
        for item in result:
            if item['name'].lower() == constants.TODAY_GAINER:
                gainersTempData = item['instruments']
            if item['name'].lower() == constants.TODAY_LOSER:
                losersTempData = item['instruments']
        result = self.__bindStockDetails(gainersTempData,losersTempData)

        # Step 3: Save in Redis with TTL
        TTL = int(constants.CACHE_TTL)

        self._redis.set(constants.CACHE_KEY, result, ttl=TTL)
        return ResponseModel(
            status=constants.SUCCESS,
            statusCode=200,
            data=result,
        )

    def __bindStockDetails(self,gainersTempData:any ,losersTempData:any):
        gainersStockSymbol : List[str] = []
        losersStockSymbol : List[str] = []
        gainerData = self.__parseStocks(gainersTempData,gainersStockSymbol)
        losersData = self.__parseStocks(losersTempData,losersStockSymbol)
        gainerData = self.__stocksPriceData(gainersStockSymbol, gainerData)
        losersData = self.__stocksPriceData(losersStockSymbol, losersData)
        bindedData =  [{"gainers": gainerData}, {"losers": losersData}]
        return bindedData

    def __parseStocks(self, data_list: List[dict], stockSymbolList : List[dict]) -> List[MarketData]:
        index = 0
        stocks = []
        for d in data_list:
            if index >=10:
                return stocks
            stock = MarketData(
                stockName=d["n"],
                symbol=d["s"],
                isin=d["ik"]
            )
            stockSymbolList.append(stock.symbol)
            stocks.append(stock)
            index +=1
        return stocks
    
    def __stocksPriceData(self , stockSymbolList: List[str], stockData : List[MarketData])-> List[MarketData]:
        payload = {
            "exchangeAggReqMap": {
                "NSE": {
                    "priceSymbolList": stockSymbolList
                }
            }
        }
        headers = {
            "Content-Type": "application/json",
        }
        # POST request
        response = self._httpClient.post(constants.STOCKPRICEDATA, headers, payload)
        # requests.post(constants.STOCKPRICEDATA, headers=headers, json=payload)
        if(response.status_code != 200):
            return
        result =  json.loads(response.text)['exchangeAggRespMap']['NSE']["priceLivePointsMap"]
        for stock in stockData:
            symbol = stock.symbol
            if symbol in result:
                live = result[symbol]
                stock.ltp = live.get("ltp", stock.ltp)
                stock.openPrice = live.get("open", stock.openPrice)
                stock.closePrice = live.get("close", stock.closePrice)
                stock.perChange = round(((live.get("close") - live.get("open")) / live.get("open")) * 100, 2) if live.get("open") else 0.0
                stock.todayPriceChange =   round(live.get("close") - live.get("open"), 2)
        
        return stockData

            

