import json

from openai import AsyncOpenAI

from backend.api.config import settings
from backend.strategy.signal_generator import SignalGenerator

_client = AsyncOpenAI(api_key=settings.openai_api_key)
_generator = SignalGenerator()


async def signal_validator_node(state: dict) -> dict:
    symbol = state["symbol"]
    timeframe = state["timeframe"]
    market_analysis = state["market_analysis"]

    raw_signal = await _generator.generate(symbol, timeframe)

    prompt = f"""
You are a signal validator for NSE Futures trading.

Market analysis: {json.dumps(market_analysis)}
Raw signal: {json.dumps(raw_signal)}

Validate this signal. Reject if:
- Confidence < 50
- Signal contradicts market regime
- RSI is overbought (>70) on BUY or oversold (<30) on SELL

Respond in JSON: {{"approved": bool, "reason": str, "adjusted_confidence": int}}
"""
    response = await _client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    validation = json.loads(response.choices[0].message.content)
    merged_signal = {**raw_signal, **validation}

    return {**state, "signal": merged_signal}
