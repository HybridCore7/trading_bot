from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx

logger = logging.getLogger("trading_bot")


# Defaults
DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
REQUEST_TIMEOUT = 15  # seconds


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, status_code: int, code: int, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"[HTTP {status_code}] Binance error {code}: {message}")


class BinanceClient:
    """
    Low-level HTTP client for the Binance USDT-M Futures Testnet API.

    Usage:
        client = BinanceClient(api_key="...", api_secret="...")
        response = client.post("/fapi/v1/order", params={...})
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = REQUEST_TIMEOUT,
    ):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must be provided. Check your .env file.")

        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={"X-MBX-APIKEY": self._api_key},
        )
        logger.info("BinanceClient initialised — base URL: %s", self._base_url)

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp and HMAC-SHA256 signature to request parameters."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    # ------------------------------------------------------------------
    # Core request methods
    # ------------------------------------------------------------------

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse response; raise BinanceAPIError on non-2xx codes."""
        logger.debug(
            "Response [%s] %s — %s",
            response.status_code,
            response.request.url,
            response.text[:500],
        )
        if response.status_code >= 400:
            try:
                data = response.json()
                code = data.get("code", -1)
                msg = data.get("msg", "Unknown error")
            except Exception:
                code = -1
                msg = response.text[:200]
            raise BinanceAPIError(response.status_code, code, msg)

        return response.json()

    def get(
        self, path: str, params: Optional[Dict[str, Any]] = None, signed: bool = False
    ) -> Dict[str, Any]:
        """Send a GET request."""
        params = dict(params or {})
        if signed:
            params = self._sign(params)
        logger.debug("GET %s params=%s", path, params)
        resp = self._client.get(path, params=params)
        return self._handle_response(resp)

    def post(
        self, path: str, params: Optional[Dict[str, Any]] = None, signed: bool = True
    ) -> Dict[str, Any]:
        """Send a POST request (signed by default for order endpoints)."""
        params = dict(params or {})
        if signed:
            params = self._sign(params)
        logger.debug("POST %s params=%s", path, {k: v for k, v in params.items() if k != "signature"})
        resp = self._client.post(path, params=params)
        return self._handle_response(resp)

    def delete(
        self, path: str, params: Optional[Dict[str, Any]] = None, signed: bool = True
    ) -> Dict[str, Any]:
        """Send a DELETE request."""
        params = dict(params or {})
        if signed:
            params = self._sign(params)
        logger.debug("DELETE %s params=%s", path, params)
        resp = self._client.delete(path, params=params)
        return self._handle_response(resp)

    # ------------------------------------------------------------------
    # Convenience: connectivity check
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Test connectivity to the API server."""
        try:
            self.get("/fapi/v1/ping")
            logger.info("API ping successful.")
            return True
        except Exception as exc:
            logger.error("API ping failed: %s", exc)
            return False

    def server_time(self) -> int:
        """Return the server timestamp (ms)."""
        data = self.get("/fapi/v1/time")
        return data["serverTime"]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self):
        """Close the underlying HTTP client."""
        self._client.close()
        logger.debug("HTTP client closed.")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
