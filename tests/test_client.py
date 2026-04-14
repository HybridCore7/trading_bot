import hmac
import hashlib
from unittest.mock import patch

from bot.client import BinanceClient


def test_sign_includes_timestamp_and_signature():
    client = BinanceClient(api_key="key", api_secret="secret")

    with patch("bot.client.time.time", return_value=1713100202.0):
        qs = client._sign({"symbol": "BTCUSDT"})

    assert "timestamp=1713100202000" in qs
    assert "signature=" in qs
    assert "symbol=BTCUSDT" in qs

    secret = b"secret"
    expected = hmac.new(
        secret,
        "symbol=BTCUSDT&timestamp=1713100202000".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert qs.endswith(f"&signature={expected}")
