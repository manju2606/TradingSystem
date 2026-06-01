from backend.market.service import MarketDataService
from backend.prediction.engine import PredictionEngine

_TIMEFRAMES = ["15m", "30m", "1h", "4h", "6h", "8h", "1D", "1W", "1M"]


class SignalGenerator:
    def __init__(self):
        self._market = MarketDataService()
        self._predictor = PredictionEngine()

    async def generate(self, symbol: str, timeframe: str) -> dict:
        df = await self._market.get_ohlc(symbol, timeframe)
        latest = df.iloc[-1]

        # Rule-based layer: EMA crossover + RSI filter
        trend = "BUY" if latest["ema_20"] > latest["ema_50"] else "SELL"
        rsi = latest["rsi"]
        if trend == "BUY" and rsi > 70:
            trend = "HOLD"
        if trend == "SELL" and rsi < 30:
            trend = "HOLD"

        # ML confidence boost
        pred = await self._predictor.predict(symbol, timeframe)
        rule_conf = 60
        if pred["direction"] == trend:
            confidence = min(100, rule_conf + int(pred["probability"] * 40))
        else:
            confidence = max(0, rule_conf - int(pred["probability"] * 40))
            if confidence < 40:
                trend = "HOLD"

        return {"signal": trend, "confidence": confidence}

    async def generate_all_timeframes(self, symbol: str) -> list[dict]:
        results = []
        for tf in _TIMEFRAMES:
            try:
                r = await self.generate(symbol, tf)
                results.append({"timeframe": tf, **r})
            except Exception:
                results.append({"timeframe": tf, "signal": "HOLD", "confidence": 0})
        return results
