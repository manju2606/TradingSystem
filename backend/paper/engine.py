from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.order import OrderRequest, OrderResponse
from backend.market.service import MarketDataService
from db.postgres.models import Order, Position, Symbol


class PaperTradingEngine:
    def __init__(self):
        self._market = MarketDataService()

    async def place_order(
        self, db: AsyncSession, user_id: int, req: OrderRequest
    ) -> OrderResponse:
        # Resolve symbol
        result = await db.execute(select(Symbol).where(Symbol.name == req.symbol))
        symbol = result.scalar_one_or_none()
        if symbol is None:
            symbol = Symbol(name=req.symbol)
            db.add(symbol)
            await db.flush()

        # Fill at current market price
        market_price = await self._market.get_latest_price(req.symbol)
        fill_price = Decimal(str(round(market_price, 2)))

        order = Order(
            user_id=user_id,
            symbol_id=symbol.id,
            order_type=req.order_type,
            quantity=req.quantity,
            price=fill_price,
            status="FILLED",
            is_paper=True,
            filled_at=datetime.now(timezone.utc),
        )
        db.add(order)

        await self._update_position(db, user_id, symbol.id, req.order_type, req.quantity, fill_price)
        await db.commit()
        await db.refresh(order)

        return OrderResponse(
            id=order.id,
            symbol=req.symbol,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            status=order.status,
            is_paper=True,
            created_at=order.created_at,
        )

    async def _update_position(
        self,
        db: AsyncSession,
        user_id: int,
        symbol_id: int,
        order_type: str,
        quantity: int,
        price: Decimal,
    ) -> None:
        result = await db.execute(
            select(Position).where(
                Position.user_id == user_id,
                Position.symbol_id == symbol_id,
                Position.closed_at.is_(None),
                Position.is_paper.is_(True),
            )
        )
        position = result.scalar_one_or_none()

        if position is None:
            position = Position(
                user_id=user_id,
                symbol_id=symbol_id,
                quantity=quantity if order_type == "BUY" else -quantity,
                avg_entry_price=price,
                current_price=price,
                unrealised_pnl=Decimal("0"),
                is_paper=True,
            )
            db.add(position)
        else:
            if order_type == "BUY":
                total_qty = position.quantity + quantity
                position.avg_entry_price = (
                    (position.avg_entry_price * position.quantity + price * quantity) / total_qty
                )
                position.quantity = total_qty
            else:
                position.quantity -= quantity
                if position.quantity == 0:
                    position.closed_at = datetime.now(timezone.utc)

            position.current_price = price
            position.unrealised_pnl = (price - position.avg_entry_price) * position.quantity
