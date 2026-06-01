from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from db.postgres.database import get_db
from db.postgres.models import Backtest, User

router = APIRouter()


@router.get("")
async def list_backtests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Backtest)
        .where(Backtest.user_id == current_user.id)
        .order_by(Backtest.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.post("/run")
async def run_backtest(
    symbol: str = Query(...),
    strategy: str = Query(...),
    start: date = Query(...),
    end: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Backtest execution is async/heavy — dispatch to background worker in Phase 2
    return {"status": "queued", "symbol": symbol, "strategy": strategy}
