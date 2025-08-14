from fastapi import HTTPException
from Strategy.brokerFactory import BrokerFactory
from models.schemas import CancelOrderRequest, LoginRequest, StockOrderRequest

class BrokerService:

    def __init__(self):
        pass
                                
    def __init__(self, broker_name: str):
        self.brokerFactory = BrokerFactory(broker_name).get_broker()

    def login(self, request: LoginRequest):
        try:
            return self.brokerFactory.login(request)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Login failed: " + str(e))
        
    def place_order(self, headers: dict, orderParams: StockOrderRequest, transactionType: str):
        try:
            return self.brokerFactory.placeOrder(headers,orderParams,transactionType)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Login failed: " + str(e))


    def getOrders(self, headers, navigateFrom:str):
        try:
            ordersData = self.brokerFactory.getOrders(headers, navigateFrom)
            return ordersData
        except Exception as e:
            raise HTTPException(status_code=500, detail="fetch holding failed: " + str(e))
        

    def getHoldings(self, headers: dict, navigateFrom: str):
        try:
            data = self.brokerFactory.getHoldings(headers, navigateFrom)
            return data
        except Exception as e:
            raise HTTPException(status_code=500, detail="Fetch holding failed: " + str(e))

    def get_profile(self, headers: dict):
        try:
            return self.brokerFactory.get_profile(headers)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Login failed: " + str(e))
        

    def cancelOrder(self, headers, cancelRequest: CancelOrderRequest, navigateFrom:str):
        try:
            ordersData = self.brokerFactory.cancelOrder(headers, cancelRequest, navigateFrom)
            return ordersData
        except Exception as e:
            raise HTTPException(status_code=500, detail="cancel order failed: " + str(e))
        
