from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class OrderResult:
    order_id: str
    status: str
    filled_price: Decimal | None = None
    message: str = ""


class BrokerAdapter(ABC):
    @abstractmethod
    async def place_order(
        self, symbol: str, order_type: str, quantity: int, price: Decimal
    ) -> OrderResult: ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool: ...

    @abstractmethod
    async def get_positions(self) -> list[dict]: ...


class ZerodhaAdapter(BrokerAdapter):
    """Zerodha Kite Connect adapter — Phase 5 live execution."""

    def __init__(self, api_key: str, access_token: str):
        self._api_key = api_key
        self._access_token = access_token
        # kiteconnect.KiteConnect would be initialised here

    async def place_order(self, symbol, order_type, quantity, price) -> OrderResult:
        raise NotImplementedError("Live broker execution not yet enabled")

    async def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError

    async def get_positions(self) -> list[dict]:
        raise NotImplementedError


class PaperBrokerAdapter(BrokerAdapter):
    """No-op adapter used during paper trading phases."""

    async def place_order(self, symbol, order_type, quantity, price) -> OrderResult:
        return OrderResult(order_id="PAPER-0", status="FILLED", filled_price=price)

    async def cancel_order(self, order_id: str) -> bool:
        return True

    async def get_positions(self) -> list[dict]:
        return []
