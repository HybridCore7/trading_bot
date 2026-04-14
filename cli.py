#!/usr/bin/env python3
"""
CLI entry point for the Binance Futures Testnet Trading Bot.

Provides two interfaces:
  1. Direct command mode:  python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  2. Interactive mode:     python cli.py interactive

Uses Click for argument parsing and Rich for polished terminal output.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from bot.logging_config import setup_logging
from bot.client import BinanceClient, BinanceAPIError
from bot.orders import place_order, OrderResult
from bot.validators import validate_order, ValidationError, VALID_SIDES, VALID_ORDER_TYPES

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_dotenv()
logger = setup_logging()
console = Console(force_terminal=True)

BANNER = """
 +==================================================+
 |   Binance Futures Testnet  -  Trading Bot CLI    |
 +==================================================+
"""


def _get_client() -> BinanceClient:
    """Instantiate a BinanceClient from environment variables."""
    api_key = os.getenv("BINANCE_TESTNET_API_KEY", "")
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET", "")
    if not api_key or not api_secret or api_key == "your_api_key_here":
        console.print(
            "[bold red]X[/] API credentials not configured.\n"
            "  Copy [cyan].env.example[/] -> [cyan].env[/] and fill in your testnet keys.\n"
            "  Get keys at: [link]https://testnet.binancefuture.com[/link]",
        )
        sys.exit(1)
    return BinanceClient(api_key=api_key, api_secret=api_secret)


def _print_order_summary(params) -> None:
    """Display a formatted order request summary before submission."""
    table = Table(
        title="Order Request Summary",
        box=box.ROUNDED,
        title_style="bold cyan",
        show_header=False,
        padding=(0, 2),
    )
    table.add_column("Field", style="bold white", min_width=14)
    table.add_column("Value", style="yellow")

    table.add_row("Symbol", params.symbol)
    table.add_row("Side", f"[green]{params.side}[/]" if params.side == "BUY" else f"[red]{params.side}[/]")
    table.add_row("Type", params.order_type)
    table.add_row("Quantity", str(params.quantity))
    if params.price is not None:
        table.add_row("Price", str(params.price))
    if params.stop_price is not None:
        table.add_row("Stop Price", str(params.stop_price))
    table.add_row("Time In Force", params.time_in_force)

    console.print()
    console.print(table)


def _print_order_result(result: OrderResult) -> None:
    """Display a formatted order result."""
    if result.success:
        table = Table(
            title="[OK] Order Placed Successfully",
            box=box.ROUNDED,
            title_style="bold green",
            show_header=False,
            padding=(0, 2),
        )
        table.add_column("Field", style="bold white", min_width=16)
        table.add_column("Value", style="cyan")

        table.add_row("Order ID", str(result.order_id))
        table.add_row("Client Order ID", str(result.client_order_id or "-"))
        table.add_row("Symbol", str(result.symbol))
        table.add_row("Side", str(result.side))
        table.add_row("Type", str(result.order_type))
        table.add_row("Status", str(result.status))
        table.add_row("Quantity", str(result.quantity))
        table.add_row("Executed Qty", str(result.executed_qty))
        if result.price and result.price != "0":
            table.add_row("Price", str(result.price))
        if result.avg_price and result.avg_price != "0":
            table.add_row("Avg Price", str(result.avg_price))
        if result.stop_price and result.stop_price != "0":
            table.add_row("Stop Price", str(result.stop_price))
        table.add_row("Time In Force", str(result.time_in_force or "-"))

        console.print()
        console.print(table)
        console.print(f"  [bold green]>>>[/] Order [cyan]{result.order_id}[/] submitted.\n")
    else:
        console.print()
        console.print(
            Panel(
                f"[bold red]X Order Failed[/bold red]\n\n{result.error}",
                border_style="red",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )


def _prompt_or_quit(prompt: str, default: Optional[str] = None, choices: Optional[list[str]] = None) -> Optional[str]:
    """Ask a prompt, allow typing 'quit' to exit, and validate choice options."""
    value = Prompt.ask(prompt, default=default)
    if isinstance(value, str) and value.strip().lower() == "quit":
        return None
    if choices:
        normalized = value.strip().upper()
        if normalized not in [choice.upper() for choice in choices]:
            raise ValueError(
                f"Invalid choice '{value}'. Must be one of: {', '.join(choices)}."
            )
        return normalized
    return value


@click.group()
def cli():
    """Binance Futures Testnet Trading Bot - place orders from the command line."""
    pass


@cli.command()
@click.option("--symbol", "-s", required=True, help="Trading pair, e.g. BTCUSDT")
@click.option("--side", "-S", required=True, type=click.Choice(["BUY", "SELL"], case_sensitive=False), help="Order side")
@click.option("--type", "-t", "order_type", required=True, type=click.Choice(["MARKET", "LIMIT", "STOP_LIMIT"], case_sensitive=False), help="Order type")
@click.option("--quantity", "-q", required=True, type=float, help="Order quantity")
@click.option("--price", "-p", type=float, default=None, help="Limit price (required for LIMIT / STOP_LIMIT)")
@click.option("--stop-price", type=float, default=None, help="Stop trigger price (required for STOP_LIMIT)")
@click.option("--tif", default="GTC", type=click.Choice(["GTC", "IOC", "FOK"], case_sensitive=False), help="Time in force (default: GTC)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def order(symbol, side, order_type, quantity, price, stop_price, tif, yes):
    """Place a single order on Binance Futures Testnet."""
    console.print(BANNER, style="bold cyan")

    # Validate
    try:
        params = validate_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=tif,
        )
    except ValidationError as ve:
        console.print(f"[bold red]X Validation error:[/] {ve}")
        logger.error("Validation failed: %s", ve)
        sys.exit(1)

    _print_order_summary(params)

    # Confirm
    if not yes:
        if not Confirm.ask("  [bold]Submit this order?[/]", default=True):
            console.print("  [dim]Order cancelled by user.[/dim]")
            logger.info("Order cancelled by user.")
            return

    # Execute
    with _get_client() as client:
        if not client.ping():
            console.print("[bold red]X[/] Cannot reach API. Check your connection.")
            sys.exit(1)

        result = place_order(client, params)
        _print_order_result(result)

        if not result.success:
            sys.exit(1)


@cli.command()
def interactive():
    """Launch an interactive order wizard with guided prompts."""
    console.print(BANNER, style="bold cyan")
    console.print("  [dim]Type 'quit' at any prompt to exit.[/dim]\n")

    with _get_client() as client:
        if not client.ping():
            console.print("[bold red]X[/] Cannot reach API. Check your connection.")
            sys.exit(1)
        console.print("  [green]>>>[/] Connected to Binance Futures Testnet.\n")

        while True:
            try:
                # --- Gather input ---
                symbol = _prompt_or_quit("  [bold]Symbol[/]", default="BTCUSDT")
                if symbol is None:
                    break

                side = _prompt_or_quit(
                    "  [bold]Side[/]",
                    choices=["BUY", "SELL"],
                    default="BUY",
                )
                if side is None:
                    break

                order_type = _prompt_or_quit(
                    "  [bold]Order type[/]",
                    choices=["MARKET", "LIMIT", "STOP_LIMIT"],
                    default="MARKET",
                )
                if order_type is None:
                    break

                quantity = _prompt_or_quit("  [bold]Quantity[/]", default="0.001")
                if quantity is None:
                    break

                price = None
                stop_price = None
                if order_type in ("LIMIT", "STOP_LIMIT"):
                    price = _prompt_or_quit("  [bold]Price[/]")
                    if price is None:
                        break
                if order_type == "STOP_LIMIT":
                    stop_price = _prompt_or_quit("  [bold]Stop price[/]")
                    if stop_price is None:
                        break

                tif = "GTC"
                if order_type != "MARKET":
                    tif = _prompt_or_quit(
                        "  [bold]Time in force[/]",
                        choices=["GTC", "IOC", "FOK"],
                        default="GTC",
                    )
                    if tif is None:
                        break

                # --- Validate ---
                params = validate_order(
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    stop_price=stop_price,
                    time_in_force=tif,
                )

                _print_order_summary(params)

                if not Confirm.ask("  [bold]Submit this order?[/]", default=True):
                    console.print("  [dim]Skipped.[/dim]\n")
                    continue

                # --- Place ---
                result = place_order(client, params)
                _print_order_result(result)

            except ValidationError as ve:
                console.print(f"\n  [bold red]X Validation error:[/] {ve}\n")
                logger.error("Validation error in interactive mode: %s", ve)
                continue
            except KeyboardInterrupt:
                console.print("\n  [dim]Interrupted.[/dim]")
                break

            # Another order?
            if not Confirm.ask("\n  [bold]Place another order?[/]", default=True):
                break

    console.print("\n  [dim]Goodbye![/dim]\n")


@cli.command()
def ping():
    """Test connectivity to the Binance Futures Testnet API."""
    console.print(BANNER, style="bold cyan")
    with _get_client() as client:
        if client.ping():
            server_ts = client.server_time()
            console.print(f"  [green]>>>[/] API is reachable - server time: {server_ts}")
        else:
            console.print("  [red]X[/] API unreachable.")
            sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    cli()
