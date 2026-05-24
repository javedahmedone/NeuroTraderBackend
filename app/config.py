"""
Centralized Configuration Management for NeuroTrader Backend
All configuration loaded from environment variables with validation
"""

import os
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Base configuration class with all app settings"""
    
    # ====== APP SETTINGS ======
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENV: str = os.getenv("ENV", "development")
    PORT: int = int(os.getenv("PORT", "5000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # ====== GOOGLE GEMINI API ======
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # ====== MONGODB ======
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "neurotrader")
    
    # ====== REDIS ======
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_DECODE_RESPONSES: bool = True
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_KEEPALIVE: bool = True
    
    # ====== CACHE ======
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "43200"))  # 12 hours
    
    # ====== FRONTEND & BACKEND URLS ======
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")
    
    # ====== BROKER API KEYS ======
    UPSTOX_API_KEY: str = os.getenv("UPSTOX_API_KEY", "")
    UPSTOX_REDIRECT_URI: str = os.getenv("UPSTOX_REDIRECT_URI", f"{BACKEND_URL}/auth/upstox/callback")
    
    ANGEL_API_KEY: str = os.getenv("ANGEL_API_KEY", "")
    ANGEL_API_SECRET: str = os.getenv("ANGEL_API_SECRET", "")
    ANGEL_REDIRECT_URI: str = os.getenv("ANGEL_REDIRECT_URI", f"{BACKEND_URL}/auth/angel/callback")
    
    # ====== OBSERVABILITY ======
    JAEGER_HOST: str = os.getenv("JAEGER_HOST", "localhost")
    JAEGER_PORT: int = int(os.getenv("JAEGER_PORT", "6831"))
    LOKI_URL: str = os.getenv("LOKI_URL", "http://localhost:3100")
    PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    
    # ====== LOGGING ======
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # ====== VALIDATION METHODS ======
    
    @classmethod
    def validate(cls) -> Dict[str, any]:
        """Validate critical configuration"""
        errors: List[str] = []
        
        # Required for production
        if cls.ENV == "production":
            if not cls.GEMINI_API_KEY:
                errors.append("GEMINI_API_KEY is required in production")
            if not cls.UPSTOX_API_KEY:
                errors.append("UPSTOX_API_KEY is required in production")
           
        # Always required
        if not cls.MONGO_URL:
            errors.append("MONGO_URL is required")
        if not cls.REDIS_URL:
            errors.append("REDIS_URL is required")
        if not cls.FRONTEND_URL:
            errors.append("FRONTEND_URL is required")
        if not cls.BACKEND_URL:
            errors.append("BACKEND_URL is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @classmethod
    def to_dict(cls) -> Dict[str, any]:
        """Convert config to dictionary (non-sensitive values only)"""
        return {
            "environment": cls.ENV,
            "debug": cls.DEBUG,
            "port": cls.PORT,
            "host": cls.HOST,
            "frontend_url": cls.FRONTEND_URL,
            "backend_url": cls.BACKEND_URL,
            "mongo_db_name": cls.MONGO_DB_NAME,
            "cache_ttl": cls.CACHE_TTL,
            "log_level": cls.LOG_LEVEL,
            "log_format": cls.LOG_FORMAT,
            "jaeger_host": cls.JAEGER_HOST,
            "jaeger_port": cls.JAEGER_PORT,
        }
    
    # ====== URL GETTER METHODS (formerly GetSecrets) ======
    
    @classmethod
    def get_frontend_url(cls) -> str:
        """Get frontend URL (modern naming convention)"""
        return cls.FRONTEND_URL
    
    @classmethod
    def get_backend_url(cls) -> str:
        """Get backend URL (modern naming convention)"""
        return cls.BACKEND_URL
    
    @classmethod
    def getFrontendUrl(cls) -> str:
        """Get frontend URL (legacy camelCase naming)"""
        return cls.FRONTEND_URL
    
    @classmethod
    def getBackendUrl(cls) -> str:
        """Get backend URL (legacy camelCase naming)"""
        return cls.BACKEND_URL


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = "development"


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = "production"


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    ENV = "testing"
    MONGO_URL = "mongodb://localhost:27017/neurotrader_test"
    REDIS_URL = "redis://localhost:6379/1"


def get_config(env: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv("ENV", "development")
    
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)


# Export singleton config instance
config = get_config()
