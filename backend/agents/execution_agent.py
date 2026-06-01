from decimal import Decimal

from backend.execution.router import ExecutionRouter

_router = ExecutionRouter()

_PAPER_PORTFOLIO_VALUE = Decimal("1000000")
_PAPER_PEAK_VALUE = Decimal("1000000")
_PAPER_DAILY_PNL = Decimal("0")


async def execution_agent_node(state: dict) -> dict:
    symbol = state["symbol"]
    signal = state["signal"]
    risk = state["risk_assessment"]

    order_type = signal.get("signal", "HOLD")
    if order_type == "HOLD":
        return {**state, "execution_result": {"status": "SKIPPED", "reason": "HOLD signal"}}

    result = await _router.execute(
        symbol=symbol,
        order_type=order_type,
        quantity=int(risk.get("position_size", 0)),
        entry_price=Decimal(str(risk.get("entry_price", "0"))),
        stop_loss=Decimal(str(risk.get("stop_loss", "0"))),
        portfolio_value=_PAPER_PORTFOLIO_VALUE,
        daily_pnl=_PAPER_DAILY_PNL,
        peak_value=_PAPER_PEAK_VALUE,
    )

    return {
        **state,
        "execution_result": {
            "order_id": result.order_id,
            "status": result.status,
            "message": result.message,
        },
    }
