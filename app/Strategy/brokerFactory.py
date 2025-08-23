from Strategy.angelOneStrategy import AngelOneStrategy
from Strategy.baseStrategy import BaseStrategy
from Strategy.upstoxStrategy import UpstoxStrategy
from global_constant import brokerConstants

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