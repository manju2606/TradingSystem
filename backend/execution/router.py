from decimal import Decimal

from backend.execution.broker_adapter import BrokerAdapter, OrderResult, PaperBrokerAdapter
from backend.risk.engine import RiskEngine


class ExecutionRouter:
    def __init__(self, broker: BrokerAdapter | None = None):
        self._broker = broker or PaperBrokerAdapter()
        self._risk = RiskEngine()

    async def execute(
        self,
        symbol: str,
        order_type: str,
        quantity: int,
        entry_price: Decimal,
        stop_loss: Decimal,
        portfolio_value: Decimal,
        daily_pnl: Decimal,
        peak_value: Decimal,
    ) -> OrderResult:
        check = self._risk.check_order(
            portfolio_value, daily_pnl, peak_value, entry_price, stop_loss, quantity
        )
        if not check.approved:
            return OrderResult(order_id="", status="REJECTED", message=check.reason)

        return await self._broker.place_order(symbol, order_type, check.position_size, entry_price)
