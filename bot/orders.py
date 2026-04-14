"""
Order placement logic.

Translates validated OrderParams into Binance API calls
and normalises the response into a clean OrderResult.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .client import BinanceClient
from .validators import OrderParams

logger = logging.getLogger("trading_bot")

ORDER_ENDPOINT = "/fapi/v1/order"


@dataclass
class OrderResult:
    """Normalised order response for display and logging."""

    success: bool
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    quantity: Optional[str] = None
    executed_qty: Optional[str] = None
    price: Optional[str] = None
    avg_price: Optional[str] = None
    stop_price: Optional[str] = None
    time_in_force: Optional[str] = None
    update_time: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "OrderResult":
        """Build an OrderResult from a successful API response dict."""
        return cls(
            success=True,
            order_id=data.get("orderId"),
            client_order_id=data.get("clientOrderId"),
            symbol=data.get("symbol"),
            side=data.get("side"),
            order_type=data.get("type"),
            status=data.get("status"),
            quantity=data.get("origQty"),
            executed_qty=data.get("executedQty"),
            price=data.get("price"),
            avg_price=data.get("avgPrice"),
            stop_price=data.get("stopPrice"),
            time_in_force=data.get("timeInForce"),
            update_time=data.get("updateTime"),
            raw=data,
        )

    @classmethod
    def from_error(cls, error_msg: str) -> "OrderResult":
        """Build an OrderResult from an error."""
        return cls(success=False, error=error_msg)


def _build_request_params(order: OrderParams) -> Dict[str, Any]:
    """Convert validated OrderParams to the dict expected by the API."""
    params: Dict[str, Any] = {
        "symbol": order.symbol,
        "side": order.side,
        "type": order.order_type if order.order_type != "STOP_LIMIT" else "STOP",
        "quantity": str(order.quantity),
    }

    if order.order_type in ("LIMIT", "STOP_LIMIT"):
        params["price"] = str(order.price)
        params["timeInForce"] = order.time_in_force

    if order.order_type == "STOP_LIMIT" and order.stop_price:
        params["stopPrice"] = str(order.stop_price)

    return params


def place_order(client: BinanceClient, order: OrderParams) -> OrderResult:
    """
    Submit an order to Binance Futures Testnet.

    Args:
        client: An authenticated BinanceClient instance.
        order: Validated OrderParams.

    Returns:
        OrderResult with success/failure details.
    """
    params = _build_request_params(order)

    logger.info(
        "Placing %s %s order — symbol=%s qty=%s price=%s stop=%s",
        order.side,
        order.order_type,
        order.symbol,
        order.quantity,
        order.price or "N/A",
        order.stop_price or "N/A",
    )
    logger.debug("Request params: %s", params)

    try:
        data = client.post(ORDER_ENDPOINT, params=params)
        result = OrderResult.from_api_response(data)
        logger.info(
            "Order placed successfully — orderId=%s status=%s executedQty=%s",
            result.order_id,
            result.status,
            result.executed_qty,
        )
        logger.debug("Full API response: %s", data)
        return result

    except Exception as exc:
        logger.error("Order placement failed: %s", exc, exc_info=True)
        return OrderResult.from_error(str(exc))
