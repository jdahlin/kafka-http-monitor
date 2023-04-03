"""A module to probe a URL and return the response time and status code."""
import http
import logging
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from re import Pattern

import httpx

logger = logging.getLogger(__name__)


@dataclass
class UrlStats:

    """A dataclass to hold the stats for a URL."""

    url: str
    method: str
    response_time_in_milliseconds: int
    # None indicates that the request failed
    response_status_code: http.HTTPStatus | None
    regex: Pattern[str] | None = None
    response_matched_regex: bool = False


@lru_cache(maxsize=100)
def get_client() -> httpx.AsyncClient:
    """Create a new client and reuse it across requests in the same process.

    This will allow the client to reuse a single TCP connection for multiple requests.

    See https://www.python-httpx.org/advanced/#client-instances for more information.

    :return: the client
    """
    return httpx.AsyncClient()


async def probe_url(
    url: str,
    method: str,
    regex: str,
) -> UrlStats:
    """Probe a URL and return the response time and status code."""
    response_matched_regex = False
    regex_compiled = None
    http_client = get_client()
    start = time.perf_counter_ns()
    try:
        response = await http_client.request(method, url, follow_redirects=False)
    except (httpx.HTTPError, httpx.ConnectError) as e:
        end = time.perf_counter_ns()
        response_time_in_milliseconds = (end - start) // 1_000_000
        logger.info(f"ERROR: {e} for {url} with method {method}")
        response_status_code = None
    else:
        end = time.perf_counter_ns()
        response_time_in_milliseconds = (end - start) // 1_000_000
        response_status_code = http.HTTPStatus(response.status_code)
        if regex is not None:
            regex_compiled = re.compile(regex)
            response_matched_regex = regex_compiled.match(response.text) is not None

    return UrlStats(
        method=method,
        regex=regex_compiled if regex is not None else None,
        response_matched_regex=response_matched_regex,
        response_status_code=response_status_code,
        response_time_in_milliseconds=response_time_in_milliseconds,
        url=url,
    )
