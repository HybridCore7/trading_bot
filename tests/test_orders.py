from decimal import Decimal
from unittest.mock import Mock

from bot.orders import _build_request_params, OrderResult, place_order
from bot.validators import OrderParams


def test_build_request_params_market_order():
    order = OrderParams(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.001"),
    )

    params = _build_request_params(order)

    assert params == {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": "0.001",
    }


def test_build_request_params_stop_limit_order():
    order = OrderParams(
        symbol="BTCUSDT",
        side="SELL",
        order_type="STOP_LIMIT",
        quantity=Decimal("0.001"),
        price=Decimal("48000"),
        stop_price=Decimal("49000"),
        time_in_force="GTC",
    )

    params = _build_request_params(order)

    assert params["type"] == "STOP"
    assert params["price"] == "48000"
    assert params["stopPrice"] == "49000"
    assert params["timeInForce"] == "GTC"


def test_place_order_returns_error_on_exception():
    client = Mock()
    client.post.side_effect = Exception("network failure")

    order = OrderParams(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.001"),
    )

    result = place_order(client, order)

    assert not result.success
    assert "network failure" in result.error


def test_place_order_returns_success_from_api_response():
    client = Mock()
    client.post.return_value = {
        "orderId": 123,
        "clientOrderId": "abc123",
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "status": "NEW",
        "origQty": "0.001",
        "executedQty": "0.000",
        "price": "0",
        "avgPrice": "0",
        "stopPrice": "0",
        "timeInForce": "GTC",
        "updateTime": 1713100202000,
    }

    order = OrderParams(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.001"),
    )

    result = place_order(client, order)

    assert result.success
    assert result.order_id == 123
    assert result.symbol == "BTCUSDT"
    assert result.status == "NEW"
