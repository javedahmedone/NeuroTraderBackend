import os
from dotenv import load_dotenv

# Load .env file at startup
load_dotenv()

# ====== NON-SENSITIVE CONSTANTS ======
SELL = "SELL"
BUY = "BUY" 
NUll = "NULL"
USERPROMPT = "USERPROMPT"
GETORDERS = "getOrders"
HOLDINGS = "holdings"
SELLORDER = "sellOrder"
BUYORDER = "buyOrder"
ANALYZE_PORTFOLIO = "analyzePortfolio"
CANCELORDER = "cancelOrder"
CANCELALLORDERS = "cancelAllOrders"
UNKNOWN = "unknown"
BEARER = "Bearer "
SUCCESS = "success"
ERROR = "error"
VALIDATIONERROR = "validationError"
TODAY_GAINER = "todays gainers"
TODAY_LOSER = "todays losers"
MARKETMOVERAPI = "https://upstox.com/simsim-api/seo/api/watchlists-admin.php"
STOCKPRICEDATA = "https://groww.in/v1/api/stocks_data/v1/tr_live_delayed/segment/CASH/latest_aggregated"
CACHE_KEY = "nse_market_movers"
PLACE_ORDER_PROMPT = "place_order"
SELL_ORDER_PROMPT = "sell_order"
VIEW_HOLDING_PROMPT = "view_holdings"
SELL_ALL_PROMPT = "sell_all"
GET_ORDERS_PROMPT = "get_orders"
ANALYZE_PORTFOLIO_PROMPT = "analyze_portfolio"
CANCEL_ORDER_PROMPT = "cancel_order"
CANCEL_ALL_ORDERS_PROMPT = "cancel_all"
GET_TOTAL_HOLDINGS_PROMPT = "get_total_holdings"
CONTENT_APPLICATION_JSON = "application/json"
ONEWEEK = "ONEWEEK"
ONEMONTH = "ONEMONTH"
THREEMONTH = "THREEMONTH"
ONEYEAR = "ONEYEAR"
FIVEYEAR = "FIVEYEAR"
ALL = "ALL"

# ====== SECRETS (LOADED FROM .env) ======
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MONGO_URL = os.getenv("MONGO_URL", "")
REDIS_URL = os.getenv("REDIS_URL", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")
CACHE_TTL = os.getenv("CACHE_TTL", "43200")

# Broker API Keys
UPSTOX_API_KEY = os.getenv("UPSTOX_API_KEY", "")
ANGEL_API_KEY = os.getenv("ANGEL_API_KEY", "")

# App Settings
DEBUG = os.getenv("DEBUG", "False") == "True"
PORT = int(os.getenv("PORT", "5000"))
HOST = os.getenv("HOST", "0.0.0.0")