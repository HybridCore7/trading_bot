from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

logger = logging.getLogger("trading_bot")

# Supported values (extend as needed)
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}
VALID_TIME_IN_FORCE = {"GTC", "IOC", "FOK"}


class ValidationError(Exception):
    """Raised when user input fails validation."""


@dataclass(frozen=True)
class OrderParams:
    """Validated, immutable order parameters ready for submission."""

    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = "GTC"


def validate_symbol(symbol: str) -> str:
    """Normalise and validate a trading pair symbol.

    Rules:
        - Must be non-empty
        - Must end with a quote asset (USDT, BUSD, etc.)
        - Uppercased automatically
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValidationError("Symbol cannot be empty.")
    if len(symbol) < 5:
        raise ValidationError(
            f"Symbol '{symbol}' is too short. Expected format like BTCUSDT."
        )
    quote_assets = ("USDT", "BUSD", "USDC")
    if not any(symbol.endswith(q) for q in quote_assets):
        raise ValidationError(
            f"Symbol '{symbol}' must end with a supported quote asset: {', '.join(quote_assets)}."
        )
    return symbol


def validate_side(side: str) -> str:
    """Validate order side."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """Validate and convert quantity to Decimal."""
    try:
        qty = Decimal(str(quantity))
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be positive, got {qty}.")
    return qty


def validate_price(price: str | float | None, required: bool = False) -> Optional[Decimal]:
    """Validate and convert price to Decimal.

    Args:
        price: Price value (can be None for MARKET orders).
        required: If True, price must be provided.
    """
    if price is None:
        if required:
            raise ValidationError("Price is required for this order type.")
        return None
    try:
        p = Decimal(str(price))
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValidationError(f"Price must be positive, got {p}.")
    return p


def validate_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
    stop_price: str | float | None = None,
    time_in_force: str = "GTC",
) -> OrderParams:
    """
    Run full validation on order parameters and return an OrderParams object.

    Raises:
        ValidationError: If any parameter fails validation.
    """
    validated_type = validate_order_type(order_type)

    price_required = validated_type in ("LIMIT", "STOP_LIMIT")
    stop_price_required = validated_type == "STOP_LIMIT"

    validated_price = validate_price(price, required=price_required)
    validated_stop_price = validate_price(stop_price, required=stop_price_required)

    if validated_type == "MARKET" and validated_price is not None:
        logger.warning("Price is ignored for MARKET orders.")
        validated_price = None

    tif = time_in_force.strip().upper()
    if tif not in VALID_TIME_IN_FORCE:
        raise ValidationError(
            f"Invalid timeInForce '{tif}'. Must be one of: {', '.join(sorted(VALID_TIME_IN_FORCE))}."
        )

    params = OrderParams(
        symbol=validate_symbol(symbol),
        side=validate_side(side),
        order_type=validated_type,
        quantity=validate_quantity(quantity),
        price=validated_price,
        stop_price=validated_stop_price,
        time_in_force=tif,
    )

    logger.debug("Validated order params: %s", params)
    return params
