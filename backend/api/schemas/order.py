from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class OrderRequest(BaseModel):
    symbol: str
    order_type: Literal["BUY", "SELL"]
    quantity: int = Field(..., gt=0)
    price: Decimal


class OrderResponse(BaseModel):
    id: int
    symbol: str
    order_type: Literal["BUY", "SELL"]
    quantity: int
    price: Decimal
    status: Literal["PENDING", "FILLED", "REJECTED", "CANCELLED"]
    is_paper: bool
    created_at: datetime


class PositionResponse(BaseModel):
    id: int
    symbol: str
    quantity: int
    avg_entry_price: Decimal
    current_price: Decimal
    unrealised_pnl: Decimal
    is_paper: bool
    opened_at: datetime
