from datetime import datetime, timezone
from decimal import Decimal

from backend.market.service import MarketDataService
from backend.prediction.models.lightgbm_model import LightGBMModel
from backend.prediction.models.lstm_model import LSTMModel
from backend.prediction.models.transformer_model import TransformerModel
from backend.prediction.models.xgboost_model import XGBoostModel

# Timeframe → model mapping (from spec)
_MODEL_MAP = {
    "15m": "xgboost",
    "30m": "xgboost",
    "1h": "lightgbm",
    "4h": "lstm",
    "6h": "lstm",
    "8h": "lstm",
    "1D": "lstm",
    "1W": "transformer",
    "1M": "transformer",
}


class PredictionEngine:
    def __init__(self):
        self._market = MarketDataService()
        self._models = {
            "xgboost": XGBoostModel(),
            "lightgbm": LightGBMModel(),
            "lstm": LSTMModel(),
            "transformer": TransformerModel(),
        }

    async def predict(self, symbol: str, timeframe: str) -> dict:
        model_name = _MODEL_MAP.get(timeframe, "xgboost")
        model = self._models[model_name]

        df = await self._market.get_ohlc(symbol, timeframe)
        result = model.predict(df)

        latest_close = float(df["Close"].iloc[-1])
        atr = float(df["atr"].iloc[-1])

        direction = "BUY" if result["probability"] > 0.55 else ("SELL" if result["probability"] < 0.45 else "HOLD")
        entry = Decimal(str(round(latest_close, 2)))
        sl = Decimal(str(round(latest_close - 1.5 * atr if direction == "BUY" else latest_close + 1.5 * atr, 2)))
        target = Decimal(str(round(latest_close + 3 * atr if direction == "BUY" else latest_close - 3 * atr, 2)))

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "model": model_name,
            "direction": direction,
            "probability": result["probability"],
            "entry_price": entry,
            "stop_loss": sl,
            "target_price": target,
            "predicted_at": datetime.now(timezone.utc),
        }
