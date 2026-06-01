from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from backend.strategy.signal_generator import SignalGenerator


@pytest.fixture
def mock_df():
    df = pd.DataFrame({
        "Close": [22000.0] * 5,
        "ema_20": [22100.0] * 5,
        "ema_50": [22000.0] * 5,
        "rsi": [55.0] * 5,
    })
    return df


@pytest.mark.asyncio
async def test_buy_signal_when_ema20_above_ema50(mock_df):
    gen = SignalGenerator()
    with patch.object(gen._market, "get_ohlc", return_value=mock_df), \
         patch.object(gen._predictor, "predict", return_value={"direction": "BUY", "probability": 0.7}):
        result = await gen.generate("NIFTY", "15m")
    assert result["signal"] == "BUY"
    assert result["confidence"] > 60


@pytest.mark.asyncio
async def test_hold_when_overbought(mock_df):
    mock_df["rsi"] = 75.0  # overbought
    gen = SignalGenerator()
    with patch.object(gen._market, "get_ohlc", return_value=mock_df), \
         patch.object(gen._predictor, "predict", return_value={"direction": "BUY", "probability": 0.5}):
        result = await gen.generate("NIFTY", "15m")
    assert result["signal"] == "HOLD"
