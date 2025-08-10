from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, portfolio, promtAnalyzer, stock_setup

app = FastAPI()

# Allow frontend CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


print("main py")
app.include_router(auth.router, prefix="/auth")
app.include_router(portfolio.router, prefix="/portfolio")
app.include_router(promtAnalyzer.router, prefix="/promtAnalyzer")
app.include_router(stock_setup.router, prefix="/stock")
