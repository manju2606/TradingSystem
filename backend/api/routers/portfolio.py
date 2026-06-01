from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.api.schemas.order import PositionResponse
from db.postgres.database import get_db
from db.postgres.models import Position, Symbol, User

router = APIRouter()


@router.get("/positions", response_model=list[PositionResponse])
async def get_positions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Position, Symbol.name)
        .join(Symbol, Position.symbol_id == Symbol.id)
        .where(Position.user_id == current_user.id, Position.closed_at.is_(None))
    )
    rows = result.all()
    return [
        PositionResponse(
            id=pos.id,
            symbol=sym_name,
            quantity=pos.quantity,
            avg_entry_price=pos.avg_entry_price,
            current_price=pos.current_price,
            unrealised_pnl=pos.unrealised_pnl,
            is_paper=pos.is_paper,
            opened_at=pos.opened_at,
        )
        for pos, sym_name in rows
    ]


@router.get("/summary")
async def portfolio_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Position).where(
            Position.user_id == current_user.id,
            Position.closed_at.is_(None),
        )
    )
    positions = result.scalars().all()
    total_pnl = sum(p.unrealised_pnl for p in positions)
    return {"total_positions": len(positions), "total_unrealised_pnl": float(total_pnl)}
