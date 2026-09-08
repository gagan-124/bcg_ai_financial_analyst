import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import httpx

from ..core.config import settings

# Mapping of ticker symbols to CIK identifiers
SEC_CIKS = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "TSLA": "0001318605",
}

# Simple in‑memory cache with TTL (1 hour)
_CACHE_LOCK = threading.Lock()
_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = timedelta(hours=1)


class SECClientError(RuntimeError):
    """Base class for SEC client errors."""


class SECConfigurationError(SECClientError):
    """Raised when required configuration (e.g., SEC_USER_AGENT) is missing."""


class SECRequestError(SECClientError):
    """Raised for HTTP/network errors when contacting the SEC endpoint."""


class SECResponseError(SECClientError):
    """Raised when the SEC response cannot be parsed or is invalid."""


def _get_user_agent() -> str:
    ua = getattr(settings, "SEC_USER_AGENT", None)
    if not ua:
        raise SECConfigurationError("SEC_USER_AGENT environment variable is not set")
    return ua


def _cache_get(cik: str) -> dict | None:
    with _CACHE_LOCK:
        entry = _CACHE.get(cik)
        if entry:
            fetched_at = entry["fetched_at"]
            if datetime.now(timezone.utc) - fetched_at < CACHE_TTL:
                return entry["data"]
            else:
                del _CACHE[cik]
    return None


def _cache_set(cik: str, data: dict) -> None:
    with _CACHE_LOCK:
        _CACHE[cik] = {"fetched_at": datetime.now(timezone.utc), "data": data}


def fetch_company_facts(ticker: str) -> dict:
    """Fetch SEC Company Facts JSON for the given ticker.

    Args:
        ticker: Upper‑case ticker symbol (e.g., "AAPL").
    Returns:
        Parsed JSON data as a dict.
    Raises:
        SECConfigurationError: Missing user‑agent.
        SECRequestError: HTTP/network failure.
        SECResponseError: Non‑JSON or unexpected payload.
    """
    cik = SEC_CIKS.get(ticker.upper())
    if not cik:
        raise SECRequestError(f"Unsupported ticker for SEC lookup: {ticker}")

    # Check cache first
    cached = _cache_get(cik)
    if cached is not None:
        return cached

    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {"User-Agent": _get_user_agent()}
    timeout = httpx.Timeout(10.0, connect=5.0)
    try:
        response = httpx.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SECRequestError(f"Error contacting SEC endpoint: {exc}") from exc

    try:
        data = response.json()
    except Exception as exc:
        raise SECResponseError("SEC response is not valid JSON") from exc

    _cache_set(cik, data)
    return data
