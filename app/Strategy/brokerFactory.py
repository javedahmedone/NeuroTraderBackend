
from config import config
from logging_config import get_logger
from Strategy.upstoxStrategy import UpstoxStrategy
from Strategy.angelOneStrategy import AngelOneStrategy  # If you have this
from typing import Optional

logger = get_logger(__name__)


class BrokerFactory:
    """Factory for creating broker strategy instances"""
    
    _strategies = {
        "upstox": UpstoxStrategy,
        "angel": AngelOneStrategy,  # Add other brokers as needed
    }
    
    @classmethod
    def create_strategy(cls, broker_name: str):
        """
        Create broker strategy instance
        
        Args:
            broker_name: Name of the broker (upstox, angel, etc.)
            
        Returns:
            Strategy instance
            
        Raises:
            ValueError: If broker not supported
        """
        try:
            broker_name_lower = broker_name.lower()
            
            if broker_name_lower not in cls._strategies:
                raise ValueError(f"Unsupported broker: {broker_name}")
            
            strategy_class = cls._strategies[broker_name_lower]
            strategy = strategy_class()
            
            logger.info("✅ Broker strategy created", extra={
                "broker": broker_name_lower,
                "strategy": strategy_class.__name__
            })
            
            return strategy
            
        except Exception as e:
            logger.error("❌ Error creating broker strategy", extra={
                "broker": broker_name,
                "error": str(e)
            }, exc_info=True)
            raise
    
    @classmethod
    def get_supported_brokers(cls):
        """Get list of supported brokers"""
        return list(cls._strategies.keys())