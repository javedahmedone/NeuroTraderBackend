from typing import Any, Union, Optional, List, Dict
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    clientcode: Optional[str] = None
    password: Optional[str] = None
    totp: Optional[str] = None
    apiKey: Optional[str] = None
    apiSecret : Optional[str] =None
    brokerName: Optional[str] = None
    code: Optional[str] = None



class LoginResponse(BaseModel):
    clientCode: Optional[str] = None
    jwt: Optional[str] = None
    refreshToken: Optional[str] = None
    userName : Optional[str] = None
    feedToken: Optional[str] = None

class StockOrderRequest(BaseModel):
    symbol: str 
    quantity: int 
    token: int
    transactionType: str
    name: str | None = None
    instrumenttype: str | None = None   
    isinNumber: str | None = None   
    limitPrice: list[int] = Field(default_factory=list)

class CancelOrderRequest(BaseModel):
    variety :str
    orderid :str

class UserPromptRequest(BaseModel):
    userIntent : str
    quantity : int
    orderIds : list[str]
    stock_name : list[str] = Field(default_factory=list)
    token: int
    symbol: str | None = None
    isinNumber : str  | None = None
    limitPrice: list[int] = Field(default_factory=list)  # ✅ always a list


class SearchedStockModel(BaseModel):
    symbol : str
    companyName : str


class ResponseModel(BaseModel):
    status: str
    statusCode: int
    # data: Optional[Union[Dict, List[Dict]]] = None
    data: Optional[Any] = None

    userIntent :str | None = None
    errorMessage : str | None = None

class MarketData(BaseModel):
    stockName: str | None = None      # Full company name
    ltp: float | None = None          # Last traded price
    perChange: float | None = None     # % change from previous close
    symbol: str   | None = None        # Stock ticker symbol
    openPrice : float | None = None   # Absolute price gain/loss
    closePrice : float | None = None   # Absolute price gain/loss
    isin : str | None = None
    todayPriceChange : float | None = None

class SearchStockModel(BaseModel):
    stockName: str | None = None      # Full company name
    stockSymbol: str | None = None          # Last traded price
    isinNumber: str | None = None     # % change from previous close
    stockToken: str   | None = None   

