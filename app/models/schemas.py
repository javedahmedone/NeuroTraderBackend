from typing import Optional
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    clientcode: Optional[str] = None
    password: Optional[str] = None
    totp: Optional[str] = None
    apiKey: Optional[str] = None
    apiSecret : Optional[str] =None
    brokerName: Optional[str] = None



class LoginResponse(BaseModel):
    clientCode: str
    jwt: str
    refreshToken: str
    userName : str
    feedToken: str

class StockOrderRequest(BaseModel):
    symbol: str 
    quantity: int 
    token: int
    transactionType: str
    name: str | None = None
    instrumenttype: str | None = None   

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


class SearchedStockModel(BaseModel):
    symbol : str
    companyName : str


# class StockOrderRequest(BaseModel):
#     variety: str                # e.g. "NORMAL"
#     tradingsymbol: str         # e.g. "SBIN-EQ"
#     symboltoken: str           # e.g. "3045"
#     transactiontype: str       # e.g. "BUY"
#     exchange: str              # e.g. "NSE"
#     ordertype: str             # e.g. "LIMIT"
#     producttype: str           # e.g. "INTRADAY"
#     duration: str              # e.g. "DAY"
#     price: str                 # e.g. "19500" (can also be float)
#     squareoff: str             # e.g. "0"
#     stoploss: str              # e.g. "0"
#     quantity: str              # e.g. "1"
