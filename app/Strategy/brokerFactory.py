from Strategy.angelOneStrategy import AngelOneStrategy
from Strategy.baseStrategy import BaseStrategy

class BrokerFactory:
    def __init__(self, strategy_type: str):
        self.strategy_type = strategy_type.lower()

    def get_broker(self) -> BaseStrategy:
        if self.strategy_type == "angelone":
            return AngelOneStrategy()
        # elif self.strategy_type == "zerodha":
        #     return ZerodhaStrategy()
        else:
            raise ValueError(f"Unknown strategy type: {self.strategy_type}")