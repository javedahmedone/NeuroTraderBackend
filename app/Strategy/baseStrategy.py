from abc import ABC, abstractmethod
from fastapi import Request
from models.schemas import CancelOrderRequest, LoginRequest, StockOrderRequest, UserPromptRequest

class BaseStrategy(ABC):
    @abstractmethod
    def placeOrder(self, headers: dict, orderparams : StockOrderRequest, transactionType: str):
        pass

    @abstractmethod
    def getOrders(self, headers: dict, navigateFrom: str):
        pass

    @abstractmethod
    def cancelOrder(self, headers: dict, data: UserPromptRequest, navigateFrom: str):
        pass

    @abstractmethod
    def cancelAllOrders(self, headers: dict):
        pass

    @abstractmethod
    def getHoldings(self, headers: dict, navigateFrom: str):
        pass

    @abstractmethod
    def get_profile(self, headers: dict):
        pass

    @abstractmethod
    def login(self,data: LoginRequest):
        pass

    @abstractmethod
    def portfolioAnalysis(self, headers:dict, userPrompt: str):
        pass

    @abstractmethod
    def marketData(self, headers:dict,exchange: str, symboltoken:str):
        pass
