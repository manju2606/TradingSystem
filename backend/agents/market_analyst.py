from openai import AsyncOpenAI

from backend.api.config import settings
from backend.market.service import MarketDataService

_client = AsyncOpenAI(api_key=settings.openai_api_key)
_market = MarketDataService()


async def market_analyst_node(state: dict) -> dict:
    symbol = state["symbol"]
    timeframe = state["timeframe"]

    df = await _market.get_ohlc(symbol, timeframe, bars=50)
    latest = df.iloc[-1].to_dict()
    trend = "uptrend" if latest["ema_20"] > latest["ema_50"] else "downtrend"

    prompt = f"""
You are a market analyst for NSE Futures. Analyse {symbol} on {timeframe} timeframe.

Latest indicators:
- EMA20: {latest.get('ema_20', 'N/A'):.2f}, EMA50: {latest.get('ema_50', 'N/A'):.2f}
- RSI: {latest.get('rsi', 'N/A'):.1f}
- MACD diff: {latest.get('macd_diff', 'N/A'):.2f}
- ADX: {latest.get('adx', 'N/A'):.1f}
- ATR: {latest.get('atr', 'N/A'):.2f}

Detect: market regime (trending/ranging/volatile), momentum, key levels.
Respond in JSON: {{"regime": str, "momentum": str, "key_levels": list, "summary": str}}
"""
    response = await _client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    import json
    analysis = json.loads(response.choices[0].message.content)
    analysis["trend"] = trend

    return {**state, "market_analysis": analysis}
