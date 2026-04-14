# Binance Futures Testnet — Trading Bot CLI

A clean, modular Python CLI application for placing **Market**, **Limit**, and **Stop-Limit** orders on the [Binance Futures Testnet](https://testnet.binancefuture.com) (USDT-M).

---

## Features

| Feature | Details |
|---|---|
| **Order types** | MARKET · LIMIT · STOP_LIMIT (bonus) |
| **Sides** | BUY / SELL |
| **CLI modes** | Direct command mode & interactive wizard |
| **Validation** | Symbol format, side, type, quantity, price, stop-price |
| **Logging** | Timestamped file logs (DEBUG) + clean console output (INFO) |
| **Error handling** | API errors, network failures, invalid input — all caught and reported |
| **Output** | Rich-formatted tables for order summaries and results |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py           # Package marker
│   ├── client.py             # Binance HTTP client (HMAC signing, request/response handling)
│   ├── orders.py             # Order placement logic + OrderResult dataclass
│   ├── validators.py         # Input validation + OrderParams dataclass
│   └── logging_config.py     # Dual-output logging setup (file + console)
├── cli.py                    # CLI entry point (Click + Rich)
├── logs/
│   └── samples/              # Sample log files from test runs
│       ├── market_order.log
│       └── limit_order.log
├── .env.example              # Template for API credentials
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Prerequisites

- **Python 3.9+** (tested on 3.11+)
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account with API keys

### 2. Clone & Install

```bash
git clone https://github.com/<your-username>/trading_bot.git
cd trading_bot

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux / macOS
# or
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Optional editable install
pip install -e .
```

### 3. Configure API Keys

```bash
# Copy the template
cp .env.example .env            # Linux / macOS
copy .env.example .env          # Windows

# Edit .env and paste your testnet API key + secret
```

Your `.env` should look like:

```env
BINANCE_TESTNET_API_KEY=abc123...
BINANCE_TESTNET_API_SECRET=xyz789...
```

> `.env` is ignored by Git via `.gitignore`. Keep your actual API credentials local and do not commit them.

### 4. Verify Connectivity

```bash
python cli.py ping
```

Expected output:

```
✓ API is reachable — server time: 1713100000000
```

---

## Usage

### Direct Command Mode

Place orders directly from the command line with full argument support.

#### Market Order (BUY)

```bash
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

#### Market Order (SELL)

```bash
python cli.py order --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

#### Limit Order

```bash
python cli.py order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 50000
```

#### Stop-Limit Order (Bonus)

```bash
python cli.py order --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.001 --price 48000 --stop-price 49000
```

#### Skip Confirmation Prompt

```bash
python cli.py order -s BTCUSDT -S BUY -t MARKET -q 0.001 --yes
```

### Interactive Mode

A guided wizard that prompts for each field with defaults and validation:

```bash
python cli.py interactive
```

The wizard will walk you through:
1. Symbol selection (default: BTCUSDT)
2. Side (BUY / SELL)
3. Order type (MARKET / LIMIT / STOP_LIMIT)
4. Quantity, price, stop price (as needed)
5. Confirmation before submission
6. Option to place another order

### Help

```bash
python cli.py --help
python cli.py order --help
```

---

## CLI Options Reference

| Flag | Short | Required | Description |
|---|---|---|---|
| `--symbol` | `-s` | ✅ | Trading pair, e.g. `BTCUSDT` |
| `--side` | `-S` | ✅ | `BUY` or `SELL` |
| `--type` | `-t` | ✅ | `MARKET`, `LIMIT`, or `STOP_LIMIT` |
| `--quantity` | `-q` | ✅ | Order quantity (e.g. `0.001`) |
| `--price` | `-p` | For LIMIT | Limit price |
| `--stop-price` | | For STOP_LIMIT | Stop trigger price |
| `--tif` | | No | Time in force: `GTC` (default), `IOC`, `FOK` |
| `--yes` | `-y` | No | Skip confirmation prompt |

---

## Logging

Every run generates a timestamped log file in the `logs/` directory:

```
logs/trading_bot_20260414_153000.log
```

Log files include:
- API request parameters (secrets redacted)
- Full API response payloads
- Validation details
- Error stack traces

**Console output** shows only INFO-level and above for a clean user experience.

Sample log files from actual test runs are included in `logs/samples/`:
- `logs/samples/market_order.log`
- `logs/samples/limit_order.log`

---

## Assumptions

1. **Testnet only** — This bot is configured exclusively for the Binance Futures Testnet (`https://testnet.binancefuture.com`). It does **not** connect to production.
2. **USDT-M futures** — All orders target USDT-margined futures contracts.
3. **No position management** — The bot places individual orders; it does not track open positions or implement strategies.
4. **Symbol validation** — Symbols must end with `USDT`, `BUSD`, or `USDC`. The bot does not query the exchange info endpoint for exhaustive symbol validation.
5. **Default margin mode** — The bot uses whatever margin mode (cross/isolated) is already set on the testnet account.
6. **Quantity precision** — The bot sends the quantity as-is. Testnet is generally lenient, but production would require querying tick/step sizes from exchange info.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing/invalid API keys | Clear error message with setup instructions |
| Network timeout | Caught and logged; user sees failure message |
| Binance API error (e.g. insufficient balance) | Error code + message displayed and logged |
| Invalid user input | Validation error shown before any API call |
| Invalid symbol format | Rejected with format guidance |
| Missing required price for LIMIT | Rejected at validation |

---

## Dependencies

| Package | Purpose |
|---|---|
| `httpx` | Modern HTTP client with timeout and connection pooling |
| `click` | CLI framework with argument parsing and validation |
| `python-dotenv` | Load `.env` files for API credentials |
| `rich` | Beautiful terminal formatting (tables, panels, colours) |
| `pytest` | Automated unit testing for validation logic |

All listed in `requirements.txt`. No heavyweight SDK required — the bot uses direct REST calls.

## Testing

Run the validator and order-mapping tests with:

```bash
python -m pytest tests/test_validators.py -q
```

---

## License

MIT
