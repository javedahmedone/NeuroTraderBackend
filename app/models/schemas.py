from pydantic import BaseModel

class LoginRequest(BaseModel):
    clientcode: str
    password: str
    totp: str
    apiKey: str
    brokerName: str



class LoginResponse(BaseModel):
    clientCode: str
    jwt: str
    refreshToken: str
    userName : str
    feedToken: str

class StockOrderRequest(BaseModel):
    symbol: str              # e.g. "TCS-EQ"
    name: str                # e.g. "tcs"
    token: str               # e.g. "11536"
    instrumenttype: str      # e.g. "EQ"
    quantity: int     

class CancelOrderRequest(BaseModel):
    variety :str
    orderid :str



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
