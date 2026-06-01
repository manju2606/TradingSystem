import json
from decimal import Decimal

from openai import AsyncOpenAI

from backend.api.config import settings
from backend.prediction.engine import PredictionEngine
from backend.risk.engine import RiskEngine

_client = AsyncOpenAI(api_key=settings.openai_api_key)
_predictor = PredictionEngine()
_risk = RiskEngine()

_PAPER_PORTFOLIO_VALUE = Decimal("1000000")  # 10L virtual capital


async def risk_agent_node(state: dict) -> dict:
    symbol = state["symbol"]
    timeframe = state["timeframe"]
    signal = state["signal"]

    pred = await _predictor.predict(symbol, timeframe)
    position_size = _risk.calculate_position_size(
        _PAPER_PORTFOLIO_VALUE, pred["entry_price"], pred["stop_loss"]
    )

    prompt = f"""
You are a risk manager for NSE Futures trading.

Signal: {json.dumps(signal)}
Prediction: entry={pred['entry_price']}, SL={pred['stop_loss']}, target={pred['target_price']}
Calculated position size: {position_size} units
Portfolio value: {_PAPER_PORTFOLIO_VALUE}

Rules: max 2% risk/trade, 3% daily loss limit, 10% max drawdown.
Determine if this trade meets risk criteria and suggest any SL adjustments.

Respond in JSON: {{"approved": bool, "reason": str, "position_size": int, "stop_loss": str, "target": str}}
"""
    response = await _client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    assessment = json.loads(response.choices[0].message.content)
    assessment["entry_price"] = str(pred["entry_price"])

    return {**state, "risk_assessment": assessment}
