from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_current_user
from backend.api.schemas.signal import SignalRequest, SignalResponse
from backend.strategy.signal_generator import SignalGenerator
from db.postgres.models import User

router = APIRouter()
_generator = SignalGenerator()


@router.post("", response_model=SignalResponse)
async def generate_signal(
    req: SignalRequest,
    current_user: User = Depends(get_current_user),
):
    result = await _generator.generate(req.symbol, req.timeframe)
    return SignalResponse(
        symbol=req.symbol,
        timeframe=req.timeframe,
        signal=result["signal"],
        confidence=result["confidence"],
        generated_at=datetime.now(timezone.utc),
    )
