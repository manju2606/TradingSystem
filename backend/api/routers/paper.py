from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.api.schemas.order import OrderRequest, OrderResponse
from backend.paper.engine import PaperTradingEngine
from db.postgres.database import get_db
from db.postgres.models import User

router = APIRouter()
_paper = PaperTradingEngine()


@router.post("/order", response_model=OrderResponse)
async def place_paper_order(
    req: OrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _paper.place_order(db, current_user.id, req)
