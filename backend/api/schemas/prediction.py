from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    symbol: str
    timeframe: str
    model: str
    direction: Literal["BUY", "SELL", "HOLD"]
    probability: float
    entry_price: Decimal
    stop_loss: Decimal
    target_price: Decimal
    predicted_at: datetime
