"""Hata sınıflandırması: HTTP hatalarını anlamlı kategorilere ayırır.

Retry mantığı hataları körü körüne denemez; her hata türü net bir kategoridedir:
- `RateLimitedError` (429/408) → geri çekilme ile tekrar dene
- `TemporaryServerError` (5xx) → tekrar dene
- `BlockedResponseError` (403/404/410/451) → tekrar deneme
- `FetchTimeoutError` / `FetchTransportError` → ağ hataları
- `RobotsDeniedError` → robots.txt kuralı gereği engelli
- `ParsingError` → HTML/JSON ayrıştırma başarısız
"""

from __future__ import annotations


class FetchError(Exception):
    """Tüm alım (fetch) hatalarının temeli."""

    def __init__(self, url: str, *, status: int | None = None) -> None:
        self.url = url
        self.status = status
        if status is not None:
            super().__init__(f"{url} → HTTP {status}")
        else:
            super().__init__(url)


class FetchTimeoutError(FetchError):
    pass


class FetchTransportError(FetchError):
    pass


class RateLimitedError(FetchError):
    pass


class TemporaryServerError(FetchError):
    pass


class BlockedResponseError(FetchError):
    pass


class RobotsDeniedError(FetchError):
    pass


class ParsingError(Exception):
    """Sayfa içeriği (HTML/JSON) çözümlenemedi."""


class UnsupportedPageError(Exception):
    """Beklenen sayfa türü bulunamadı (ör. ürün sayfası yerine başka sayfa)."""
