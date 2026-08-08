from urllib.robotparser import RobotFileParser

import httpx

from bookdata.adapters.http import classify_status, is_retryable
from bookdata.errors import (
    BlockedResponseError,
    RateLimitedError,
    RobotsDeniedError,
    TemporaryServerError,
)


def test_classify_status_maps_codes():
    assert isinstance(classify_status("https://x.com", 429), RateLimitedError)
    assert isinstance(classify_status("https://x.com", 408), RateLimitedError)
    assert isinstance(classify_status("https://x.com", 503), TemporaryServerError)
    assert isinstance(classify_status("https://x.com", 500), TemporaryServerError)
    assert isinstance(classify_status("https://x.com", 403), BlockedResponseError)
    assert isinstance(classify_status("https://x.com", 404), BlockedResponseError)


def test_classify_status_unknown_returns_fetch_error():
    exc = classify_status("https://x.com", 302)
    assert exc.__class__.__name__ == "FetchError"


def test_is_retryable():
    assert is_retryable(RateLimitedError("u", status=429))
    assert is_retryable(TemporaryServerError("u", status=503))
    assert is_retryable(httpx.TimeoutException("u"))
    assert not is_retryable(BlockedResponseError("u", status=404))
    assert not is_retryable(RobotsDeniedError("u"))
    assert not is_retryable(ValueError("u"))


def test_robots_parse_and_can_fetch():
    parser = RobotFileParser()
    parser.parse(
        [
            "User-agent: *",
            "Disallow: /kitapyurdu-uygulamasi",
            "Allow: /",
        ]
    )
    assert parser.can_fetch("bookdata-bot/0.1", "https://www.kitapyurdu.com/kategori")
    assert not parser.can_fetch(
        "bookdata-bot/0.1", "https://www.kitapyurdu.com/kitapyurdu-uygulamasi"
    )
