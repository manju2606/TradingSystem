from decimal import Decimal

import pytest

from backend.risk.engine import RiskEngine


@pytest.fixture
def engine():
    return RiskEngine()


def test_position_size_calculation(engine):
    size = engine.calculate_position_size(
        portfolio_value=Decimal("1000000"),
        entry_price=Decimal("22000"),
        stop_loss=Decimal("21780"),  # 220 pts risk
    )
    # 2% of 10L = 20000 / 220 = 90 units
    assert size == 90


def test_daily_loss_circuit_breaker(engine):
    result = engine.check_order(
        portfolio_value=Decimal("970000"),
        daily_pnl=Decimal("-30000"),  # 3% loss
        peak_value=Decimal("1000000"),
        entry_price=Decimal("22000"),
        stop_loss=Decimal("21780"),
        quantity=50,
    )
    assert not result.approved
    assert "Daily loss limit" in result.reason


def test_drawdown_circuit_breaker(engine):
    result = engine.check_order(
        portfolio_value=Decimal("900000"),
        daily_pnl=Decimal("0"),
        peak_value=Decimal("1000000"),  # 10% drawdown
        entry_price=Decimal("22000"),
        stop_loss=Decimal("21780"),
        quantity=50,
    )
    assert not result.approved
    assert "drawdown" in result.reason.lower()


def test_approved_order_caps_quantity(engine):
    result = engine.check_order(
        portfolio_value=Decimal("1000000"),
        daily_pnl=Decimal("0"),
        peak_value=Decimal("1000000"),
        entry_price=Decimal("22000"),
        stop_loss=Decimal("21780"),
        quantity=200,  # request more than risk allows
    )
    assert result.approved
    assert result.position_size <= 90
