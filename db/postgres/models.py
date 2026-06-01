from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, ForeignKey,
    Integer, Numeric, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="trader")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # NIFTY, BANKNIFTY
    exchange: Mapped[str] = mapped_column(String(20), default="NSE")
    instrument_type: Mapped[str] = mapped_column(String(20), default="FUT")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Candle(Base):
    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    symbol_id: Mapped[int] = mapped_column(Integer, ForeignKey("symbols.id"), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)  # 15m, 1h, 4h, 1D …
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    high: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    low: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    close: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    volume: Mapped[int] = mapped_column(BigInteger)


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    symbol_id: Mapped[int] = mapped_column(Integer, ForeignKey("symbols.id"))
    timeframe: Mapped[str] = mapped_column(String(10))
    signal: Mapped[str] = mapped_column(Enum("BUY", "SELL", "HOLD", name="signal_type"))
    confidence: Mapped[int] = mapped_column(Integer)  # 0–100
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    symbol_id: Mapped[int] = mapped_column(Integer, ForeignKey("symbols.id"))
    timeframe: Mapped[str] = mapped_column(String(10))
    model: Mapped[str] = mapped_column(String(50))  # xgboost, lightgbm, lstm, transformer
    direction: Mapped[str] = mapped_column(Enum("BUY", "SELL", "HOLD", name="direction_type"))
    probability: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    target_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    predicted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    symbol_id: Mapped[int] = mapped_column(Integer, ForeignKey("symbols.id"))
    order_type: Mapped[str] = mapped_column(Enum("BUY", "SELL", name="order_type"))
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(
        Enum("PENDING", "FILLED", "REJECTED", "CANCELLED", name="order_status"),
        default="PENDING",
    )
    is_paper: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    filled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    symbol_id: Mapped[int] = mapped_column(Integer, ForeignKey("symbols.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    avg_entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unrealised_pnl: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    is_paper: Mapped[bool] = mapped_column(Boolean, default=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Backtest(Base):
    __tablename__ = "backtests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    symbol_id: Mapped[int] = mapped_column(Integer, ForeignKey("symbols.id"))
    strategy: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    win_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    results_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(255))
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
