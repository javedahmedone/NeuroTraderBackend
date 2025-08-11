from abc import ABC, abstractmethod
from fastapi import Request
from app.models.schemas import CancelOrderRequest, LoginRequest, StockOrderRequest

class BaseStrategy(ABC):
    @abstractmethod
    def place_order(self, headers: dict, orderparams : StockOrderRequest, transactionType: str):
        pass

    @abstractmethod
    def getOrders(self, headers: dict, navigateFrom: str):
        pass

    def cancelOrder(self, headers: dict, cancelRequest: CancelOrderRequest, navigateFrom: str):
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
