from fastapi import APIRouter, Depends, Query

from backend.api.dependencies import get_current_user
from backend.api.schemas.prediction import PredictionResponse
from backend.prediction.engine import PredictionEngine
from db.postgres.models import User

router = APIRouter()
_engine = PredictionEngine()


@router.get("", response_model=PredictionResponse)
async def get_prediction(
    symbol: str = Query(..., examples=["NIFTY"]),
    timeframe: str = Query(..., examples=["15m"]),
    current_user: User = Depends(get_current_user),
):
    return await _engine.predict(symbol, timeframe)
