from dataclasses import dataclass
from decimal import Decimal

from backend.api.config import settings


@dataclass
class RiskCheck:
    approved: bool
    reason: str
    position_size: int = 0


class RiskEngine:
    def __init__(self):
        self.risk_per_trade_pct = settings.risk_per_trade_pct / 100
        self.daily_loss_limit_pct = settings.daily_loss_limit_pct / 100
        self.max_drawdown_pct = settings.max_drawdown_pct / 100

    def check_order(
        self,
        portfolio_value: Decimal,
        daily_pnl: Decimal,
        peak_value: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
        quantity: int,
    ) -> RiskCheck:
        # Circuit breaker: daily loss limit
        daily_loss_pct = float(-daily_pnl / portfolio_value) if portfolio_value else 0
        if daily_loss_pct >= self.daily_loss_limit_pct:
            return RiskCheck(False, f"Daily loss limit reached ({daily_loss_pct:.1%})")

        # Circuit breaker: max drawdown
        drawdown = float((peak_value - portfolio_value) / peak_value) if peak_value else 0
        if drawdown >= self.max_drawdown_pct:
            return RiskCheck(False, f"Max drawdown breached ({drawdown:.1%})")

        # Risk per trade
        risk_per_unit = abs(float(entry_price - stop_loss))
        if risk_per_unit == 0:
            return RiskCheck(False, "Stop loss equals entry price")

        max_risk_amount = float(portfolio_value) * self.risk_per_trade_pct
        max_qty = int(max_risk_amount / risk_per_unit)

        if max_qty == 0:
            return RiskCheck(False, "Position size rounds to zero given risk limits")

        approved_qty = min(quantity, max_qty)
        return RiskCheck(True, "OK", position_size=approved_qty)

    def calculate_position_size(
        self,
        portfolio_value: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
    ) -> int:
        risk_amount = float(portfolio_value) * self.risk_per_trade_pct
        risk_per_unit = abs(float(entry_price - stop_loss))
        return int(risk_amount / risk_per_unit) if risk_per_unit else 0
