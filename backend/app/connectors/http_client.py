"""Async HTTP client helper for ethical platform queries."""
import httpx
from typing import Optional, Dict, Any
from app.config.settings import get_settings

settings = get_settings()

DEFAULT_HEADERS = {
    "User-Agent": settings.USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


async def fetch_page(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None
) -> Optional[httpx.Response]:
    """Perform safe, non-blocking HTTP GET with user-configured timeouts and polite headers."""
    effective_headers = {**DEFAULT_HEADERS, **(headers or {})}
    effective_timeout = timeout or settings.REQUEST_TIMEOUT_SECONDS
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=effective_timeout) as client:
            response = await client.get(url, headers=effective_headers, params=params)
            return response
    except Exception as exc:
        # Network errors, timeouts, or DNS failures handled gracefully
        return None
