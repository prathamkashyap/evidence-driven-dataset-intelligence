"""Minimal public-HTTP client for M0; it neither sends nor reads credentials."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter_ns
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .cache import CachedResponse, ResponseCache


@dataclass(frozen=True)
class FetchResult:
    response: CachedResponse
    cache_state: str
    duration_ms: float
    network_requests: int


def fetch(url: str, cache: ResponseCache, max_bytes: int) -> FetchResult:
    cached = cache.get(url)
    if cached is not None:
        return FetchResult(cached, "warm", 0.0, 0)

    started = perf_counter_ns()
    request = Request(url, headers={"User-Agent": "EDDI-M0/0.1 (public, no-auth instrumentation)"})
    try:
        with urlopen(request, timeout=30) as result:  # noqa: S310 - URLs are committed public endpoints.
            body = result.read(max_bytes)
            response = CachedResponse(body, result.status, None, datetime.now(UTC).isoformat())
    except HTTPError as error:
        response = CachedResponse(error.read(max_bytes), error.code, "http_error", datetime.now(UTC).isoformat())
    except URLError as error:
        response = CachedResponse(b"", None, type(error.reason).__name__, datetime.now(UTC).isoformat())
    elapsed = (perf_counter_ns() - started) / 1_000_000
    cache.put(url, response)
    return FetchResult(response, "cold", elapsed, 1)


def fetch_bounded_lines(
    url: str, cache: ResponseCache, *, max_records: int, max_bytes: int, arff: bool
) -> FetchResult:
    """Read no more than the configured textual sample, retaining only its records.

    This intentionally stores the bounded record fragment rather than a complete
    remote file. It is used only for M0's direct flat-file sample paths.
    """
    cache_identity = f"m0-bounded-lines-v1:{url}"
    cached = cache.get(cache_identity)
    if cached is not None:
        return FetchResult(cached, "warm", 0.0, 0)

    started = perf_counter_ns()
    request = Request(url, headers={"User-Agent": "EDDI-M0/0.1 (public, no-auth instrumentation)"})
    records: list[bytes] = []
    total = 0
    in_data = not arff
    try:
        with urlopen(request, timeout=30) as result:  # noqa: S310 - committed public endpoint.
            while len(records) < max_records and total < max_bytes:
                line = result.readline(max_bytes - total)
                if not line:
                    break
                total += len(line)
                if arff and line.strip().lower() == b"@data":
                    in_data = True
                    continue
                if in_data and line.strip():
                    records.append(line)
            response = CachedResponse(b"".join(records), result.status, None, datetime.now(UTC).isoformat())
    except HTTPError as error:
        response = CachedResponse(error.read(min(max_bytes, 65536)), error.code, "http_error", datetime.now(UTC).isoformat())
    except URLError as error:
        response = CachedResponse(b"", None, type(error.reason).__name__, datetime.now(UTC).isoformat())
    elapsed = (perf_counter_ns() - started) / 1_000_000
    cache.put(cache_identity, response)
    return FetchResult(response, "cold", elapsed, 1)
