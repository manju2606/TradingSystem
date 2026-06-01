from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SignalRequest(BaseModel):
    symbol: str = Field(..., examples=["NIFTY"])
    timeframe: str = Field(..., examples=["15m"])


class SignalResponse(BaseModel):
    symbol: str
    timeframe: str
    signal: Literal["BUY", "SELL", "HOLD"]
    confidence: int = Field(..., ge=0, le=100)
    generated_at: datetime
