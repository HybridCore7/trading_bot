import pytest
from decimal import Decimal

from bot.orders import _build_request_params
from bot.validators import validate_order, ValidationError, OrderParams


def test_validate_market_order():
    params = validate_order("BTCUSDT", "BUY", "MARKET", "0.001")
    assert params.symbol == "BTCUSDT"
    assert params.order_type == "MARKET"
    assert params.price is None
    assert params.stop_price is None
    assert params.quantity == Decimal("0.001")


def test_validate_limit_order():
    params = validate_order("ETHUSDT", "SELL", "LIMIT", "0.5", price="3000")
    assert params.order_type == "LIMIT"
    assert params.price == Decimal("3000")
    assert params.time_in_force == "GTC"


def test_limit_order_requires_price():
    with pytest.raises(ValidationError, match="Price is required"):
        validate_order("BTCUSDT", "BUY", "LIMIT", "1")


def test_invalid_symbol_raises_validation_error():
    with pytest.raises(ValidationError, match="must end with a supported quote asset"):
        validate_order("INVALID", "BUY", "MARKET", "1")


def test_negative_quantity_raises_validation_error():
    with pytest.raises(ValidationError, match="Quantity must be positive"):
        validate_order("BTCUSDT", "BUY", "MARKET", "-5")


def test_build_request_params_for_limit_order():
    order = OrderParams(
        symbol="ETHUSDT",
        side="SELL",
        order_type="LIMIT",
        quantity=Decimal("0.5"),
        price=Decimal("3000"),
        time_in_force="GTC",
    )

    params = _build_request_params(order)
    assert params["symbol"] == "ETHUSDT"
    assert params["side"] == "SELL"
    assert params["type"] == "LIMIT"
    assert params["quantity"] == "0.5"
    assert params["price"] == "3000"
    assert params["timeInForce"] == "GTC"
