"""HTTP istemcisi: bot korumasına karşı savunmalı, nazik ve hızlı.

- Rotasyonlu User-Agent ve gerçekçi header'lar
- `httpx.AsyncClient` ile HTTP/2, redirect takibi, cookie kalıcılığı
- Alan adı başına eşzamanlılık semaforu + minimum istek aralığı (naziklik)
- 429/5xx ve ağ hatalarında üstel geri çekilme (tenacity) + jitter; 403/404 gibi
  kalıcı hatalarda retry yok (bkz. `bookdata.errors`)
- Opsiyonel robots.txt saygısı (`BOOKDATA_RESPECT_ROBOTS=true`): host başına bir kez
  çekilir, cache'lenir, yasaklıysa `RobotsDeniedError` fırlatılır
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
import urllib.robotparser

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from bookdata.config import Settings
from bookdata.errors import (
    BlockedResponseError,
    FetchError,
    FetchTimeoutError,
    FetchTransportError,
    RateLimitedError,
    RobotsDeniedError,
    TemporaryServerError,
)

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa: E501
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa: E501
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",  # noqa: E501
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",  # noqa: E501
]

BOT_USER_AGENT = "bookdata-bot/0.1 (+https://github.com/BookStoresDatasets)"

_RETRYABLE = (httpx.TimeoutException, httpx.TransportError)
_NON_RETRYABLE_STATUS = {403, 404, 410, 451}


def classify_status(url: str, status: int) -> FetchError:
    """HTTP durum kodunu anlamlı bir hata türüne eşler."""
    if status in {408, 429}:
        return RateLimitedError(url, status=status)
    if status >= 500:
        return TemporaryServerError(url, status=status)
    if status in _NON_RETRYABLE_STATUS:
        return BlockedResponseError(url, status=status)
    return FetchError(url, status=status)


def is_retryable(exc: BaseException) -> bool:
    """Hangi hataların tekrar denenmesi gerektiğine karar verir (kör retry yok)."""
    if isinstance(exc, (RateLimitedError, TemporaryServerError)):
        return True
    if isinstance(exc, (BlockedResponseError, RobotsDeniedError)):
        return False
    return isinstance(exc, _RETRYABLE)


class AsyncHTTPClient:
    """Tek sınıf, tek `httpx.Client`; tüm adapter'lar bu istemciyi paylaşır."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._semaphore = asyncio.Semaphore(settings.concurrency)
        self._last_request_at: dict[str, float] = {}
        self._robots_cache: dict[str, bool] = {}
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout),
            follow_redirects=True,
            http2=True,
            cookies=None,
            verify=True,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": random.choice(
                ["tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7", "tr-TR,tr;q=0.9", "tr,en-US;q=0.8,en;q=0.7"]
            ),
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "no-cache",
        }

    async def _polite(self, url: str) -> None:
        """Alan adı başına minimum istek aralığını rastgele jitter ile korur."""
        host = httpx.URL(url).host
        now = time.monotonic()
        last = self._last_request_at.get(host, 0.0)
        wait = max(0.0, self._settings.min_request_interval - (now - last))
        if wait:
            await asyncio.sleep(wait + random.uniform(0.0, 0.3))
        self._last_request_at[host] = time.monotonic()

    async def _robots_allowed(self, url: str) -> bool:
        """Host başına bir kez robots.txt çeker ve `can_fetch` sonucunu cache'ler."""
        if not self._settings.respect_robots:
            return True
        host = httpx.URL(url).host
        if host in self._robots_cache:
            return self._robots_cache[host]
        allowed = True
        try:
            robots_url = f"https://{host}/robots.txt"
            resp = await self._client.get(robots_url, headers={"User-Agent": BOT_USER_AGENT})
            if resp.status_code == 200:
                parser = urllib.robotparser.RobotFileParser()
                parser.parse(resp.text.splitlines())
                allowed = parser.can_fetch(BOT_USER_AGENT, url)
        except (httpx.HTTPError, OSError):
            allowed = True  # robots.txt alınamadıysa liberal davran
        self._robots_cache[host] = allowed
        if not allowed:
            logger.warning("robots.txt gereği erişim reddedildi: %s", url)
        return allowed

    async def get(self, url: str) -> httpx.Response:
        """Tek istek; hata yoksa `Response`, kalıcı hata varsa sınıflandırılmış hata fırlatır."""

        async def _attempt() -> httpx.Response:
            async with self._semaphore:
                await self._polite(url)
                if not await self._robots_allowed(url):
                    raise RobotsDeniedError(url)
                try:
                    resp = await self._client.get(url, headers=self._headers())
                except httpx.TimeoutException as exc:
                    raise FetchTimeoutError(url) from exc
                except httpx.TransportError as exc:
                    raise FetchTransportError(url) from exc
                if resp.status_code >= 400:
                    raise classify_status(url, resp.status_code)
                return resp

        retrier = AsyncRetrying(
            retry=retry_if_exception(is_retryable),
            wait=wait_exponential_jitter(
                initial=self._settings.retry_backoff_base,
                max=30.0,
                jitter=2.0,
            ),
            stop=stop_after_attempt(self._settings.retry_attempts),
            reraise=True,
            before_sleep=lambda state: logger.warning(
                "İstek yeniden deneniyor (%s/%s): %s",
                state.attempt_number,
                self._settings.retry_attempts,
                url,
            ),
        )

        async for attempt in retrier:
            with attempt:
                return await _attempt()
        raise FetchError(url)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTPClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()
