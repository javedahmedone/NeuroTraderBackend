
from app.config import config
from app.logging_config import get_logger
from app.strategy.upstoxStrategy import UpstoxStrategy
from app.strategy.angelOneStrategy import AngelOneStrategy  # If you have this
from app.strategy.baseStrategy import BaseStrategy
from typing import Optional
from app.globalConstant import brokerConstants

logger = get_logger(__name__)

class BrokerFactory:
    def __init__(self, strategy_type: str):
        self.strategy_type = strategy_type.lower()

    def get_broker(self) -> BaseStrategy:
        if self.strategy_type == brokerConstants.AngelOne:
            return AngelOneStrategy()
        elif self.strategy_type == brokerConstants.Upstox:
            return UpstoxStrategy()
        else:
            raise ValueError(f"Unknown strategy type: {self.strategy_type}")