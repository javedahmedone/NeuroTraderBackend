from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from dotenv import load_dotenv

from prometheus_client import generate_latest

import sys

# ==========================================================
# LOCAL IMPORTS
# ==========================================================

from config import config

from logging_config import (
    configure_logging,
    get_logger
)

from middleware.correlation import (
    CorrelationMiddleware,
    get_correlation_context
)

from observability.otel_setup import (
    init_observability
)

from observability.metrics import registry

from routes import (
    auth,
    marketData,
    portfolio,
    promtAnalyzer,
    stock_setup
)

# ==========================================================
# LOAD ENV
# ==========================================================

load_dotenv()

# ==========================================================
# VALIDATE CONFIG
# ==========================================================

validation = config.validate()

if not validation["valid"]:

    print("❌ Configuration validation failed")

    for error in validation["errors"]:
        print(f" - {error}")

    sys.exit(1)

# ==========================================================
# LOGGING
# ==========================================================

configure_logging(
    log_level=config.LOG_LEVEL,
    log_format=config.LOG_FORMAT
)

logger = get_logger(__name__)

logger.info("🚀 NeuroTrader Backend Starting")

# ==========================================================
# FASTAPI
# ==========================================================

app = FastAPI(
    title="NeuroTrader Backend",
    version="1.0.0"
)

# ==========================================================
# MIDDLEWARE
# ==========================================================

app.add_middleware(CorrelationMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ==========================================================
# OBSERVABILITY
# ==========================================================

try:

    init_observability(app)

    logger.info("✅ Observability initialized")

except Exception as e:

    logger.warning(
        f"Observability init failed: {e}"
    )

# ==========================================================
# ROUTERS
# ==========================================================

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

app.include_router(
    portfolio.router,
    prefix="/portfolio",
    tags=["Portfolio"]
)

app.include_router(
    promtAnalyzer.router,
    prefix="/promtAnalyzer",
    tags=["AI"]
)

app.include_router(
    stock_setup.router,
    prefix="/stock",
    tags=["Stock"]
)

app.include_router(
    marketData.router,
    prefix="/marketData",
    tags=["Market"]
)

logger.info("✅ Routers registered")

# ==========================================================
# HEALTH ENDPOINT
# ==========================================================

@app.get("/health")
async def health():

    context = get_correlation_context()

    logger.info(
        "health_check",
        extra=context
    )

    return {
        "status": "healthy",
        "service": "neurotrader-backend",
        "correlation_id": context["correlation_id"]
    }

# ==========================================================
# METRICS ENDPOINT
# ==========================================================

@app.get("/metrics")
async def metrics():

    return Response(
        content=generate_latest(registry),
        media_type="text/plain"
    )

# ==========================================================
# ROOT ENDPOINT
# ==========================================================

@app.get("/ready")
async def root():

    return {
        "service": "NeuroTrader Backend",
        "status": "running",
        "environment": config.ENV
    }

# ==========================================================
# STARTUP EVENT
# ==========================================================

@app.on_event("startup")
async def startup_event():

    logger.info(
        "application_started",
        extra={
            "environment": config.ENV
        }
    )

# ==========================================================
# SHUTDOWN EVENT
# ==========================================================

@app.on_event("shutdown")
async def shutdown_event():

    logger.info("application_shutdown")

# ==========================================================
# LOCAL RUN
# ==========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_config=None
    )