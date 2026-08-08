"""Standardizasyon aşaması: ham sayfa verisini ortak `Product` şemasına dönüştürür.

Fiyat metnini ("53,30 TL", "1.234,50") sayıya çevirir, URL'leri temizler ve
URL bazında kopya ürünleri ayıklar. Adapter'lar bu mantığı içermez.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

from bookdata.models import Product

logger = logging.getLogger(__name__)

_CLEAN_PRICE = re.compile(r"[^\d.,]")


def parse_price(text: str) -> float | None:
    """Türkçe sayı formatındaki fiyatı çözer. Geçersizse None döner."""
    cleaned = _CLEAN_PRICE.sub("", text)
    if not cleaned:
        return None
    try:
        if "," in cleaned:
            parts = cleaned.split(",")
            integer = parts[0].replace(".", "")
            value = float(f"{integer}.{parts[1]}")
        else:
            value = float(cleaned)
    except ValueError:
        return None
    return value if value > 0 else None


def _raw_price(raw: dict) -> str:
    """JSON-LD sayısal fiyatını text'e, metni olduğu gibi iletir."""
    price = raw.get("price")
    if isinstance(price, (int, float)):
        return f"{price:.2f}".replace(".", ",")
    return str(raw.get("price_text", ""))


def normalize(raw: dict, store: str, display_name: str) -> Product | None:
    price = parse_price(_raw_price(raw))
    if price is None or not raw.get("title") or not raw.get("url"):
        return None
    return Product(
        title=raw["title"],
        author=raw.get("author", ""),
        publisher=raw.get("publisher", ""),
        category=raw.get("category", "Genel"),
        price=price,
        url=raw["url"],
        store=display_name,
        scraped_at=datetime.now(UTC),
        image_url=raw.get("image_url"),
        isbn=raw.get("isbn", ""),
        currency=str(raw.get("currency", "TRY")).upper(),
        availability=raw.get("availability", ""),
    )


def standardize(raw_items: list[dict], store: str, display_name: str) -> list[Product]:
    products: list[Product] = []
    seen: set[str] = set()
    for raw in raw_items:
        product = normalize(raw, store, display_name)
        if product is None:
            continue
        if product.url in seen:
            continue
        seen.add(product.url)
        products.append(product)
    logger.info("Standardize edildi: %s ham → %s ürün", len(raw_items), len(products))
    return products
