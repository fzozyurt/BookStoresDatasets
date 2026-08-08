"""Yapılandırılmış veri (JSON-LD) odaklı ürün çıkarma.

İlke: "structured data first, DOM fallback". Sayfa içindeki `application/ld+json`
bloklarındaki `Product`/`Book`/`ItemList` verisi okunur; bu, DOM değişimlerine
karşı daha dayanıklıdır. DOM çıktısı hiçbir zaman atılmaz, `merge_products` ile
zenginleştirilir — böylece veri kaybı olmaz.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from bs4 import BeautifulSoup

_ISBN13 = re.compile(r"97[89]\d{10}")
_ISBN10 = re.compile(r"(?<!\d)\d{9}[\dX](?!\d)")


def _as_list(value: object) -> list[dict]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, dict)]
    return []


def parse_json_ld(soup: BeautifulSoup) -> list[dict]:
    """Sayfadaki tüm JSON-LD bloklarını ayrıştırıp dict listesi döndürür.

    Bozuk veya JSON olmayan bloklar sessizce atlanır; `@graph` düzleştirilir.
    """
    results: list[dict] = []
    for script in soup.select('script[type="application/ld+json"]'):
        text = script.string or ""
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            results.append(data)
            results.extend(_as_list(data.get("@graph")))
        elif isinstance(data, list):
            results.extend(v for v in data if isinstance(v, dict))
    return results


def _type_name(data: dict) -> list[str]:
    t = data.get("@type")
    if isinstance(t, list):
        return [str(x) for x in t]
    return [str(t)] if t else []


def _offers(data: dict) -> tuple[float | None, str, str]:
    """offers (dict/list/AggregateOffer) içinden ilk uygun fiyatı seçer."""
    offers = data.get("offers")
    for offer in _as_list(offers):
        price = offer.get("price") or offer.get("lowPrice")
        if price is None:
            continue
        try:
            value = float(str(price).replace(",", "."))
        except ValueError:
            continue
        if value <= 0:
            continue
        currency = offer.get("priceCurrency", "TRY")
        availability = _availability(str(offer.get("availability", "")))
        return value, str(currency), availability
    return None, "TRY", ""


def _availability(value: str) -> str:
    key = re.sub(r"[^a-z]", "", value.lower())
    if "outofstock" in key:
        return "Stokta yok"
    if "preorder" in key:
        return "Ön sipariş"
    if "instock" in key:
        return "Stokta"
    return ""


def _image(data: dict) -> str | None:
    img = data.get("image")
    if isinstance(img, str) and img:
        return img
    if isinstance(img, list) and img:
        return str(img[0]) if img[0] else None
    return None


def _text(value: object) -> str:
    """JSON-LD alanındaki metni çıkarır (Person/Organization dict ise name)."""
    if isinstance(value, dict):
        return str(value.get("name") or value.get("title") or "").strip()
    if isinstance(value, list):
        return _text(value[0]) if value else ""
    return str(value or "").strip()


def extract_isbn(text: str) -> str:
    """Metin içinde ISBN-13/ISBN-10 arar (önce ISBN-13)."""
    m = _ISBN13.search(text)
    if m:
        return m.group(0)
    m = _ISBN10.search(text)
    if m:
        return m.group(0)
    return ""


def product_from_ld(data: dict, category: str) -> dict | None:
    """Tek bir JSON-LD bloğundan ham ürün dict'i üretir; fiyat yoksa None."""
    if not {"Product", "Book"}.intersection(_type_name(data)):
        return None
    title = data.get("name") or data.get("headline")
    if not title:
        return None
    price, currency, availability = _offers(data)
    if price is None:
        return None
    url = data.get("url") or data.get("@id") or ""
    isbn = (
        str(data["isbn"])
        if data.get("isbn")
        else str(data.get("gtin13") or data.get("gtin14") or data.get("sku") or "")
    )
    return {
        "title": str(title).strip(),
        "author": _text(data.get("author")),
        "publisher": _text(data.get("publisher")),
        "category": category,
        "price_text": str(price),
        "price": price,
        "currency": str(currency).upper(),
        "availability": availability,
        "isbn": extract_isbn(isbn) or extract_isbn(str(title)),
        "url": url,
        "image_url": _image(data),
    }


def products_from_json_ld(soup: BeautifulSoup, category: str) -> list[dict]:
    """Sayfadaki JSON-LD verisinden fiyatı olan ürünleri döndürür."""
    items: list[dict] = []
    for data in parse_json_ld(soup):
        for t in _type_name(data):
            if t == "ItemList":
                for entry in _as_list(data.get("itemListElement")):
                    item = entry.get("item") if isinstance(entry, dict) else None
                    product = product_from_ld(item, category) if isinstance(item, dict) else None
                    if product:
                        items.append(product)
            elif t in {"Product", "Book"}:
                product = product_from_ld(data, category)
                if product:
                    items.append(product)
    return items


def merge_products(dom_items: Iterable[dict], ld_items: Iterable[dict]) -> list[dict]:
    """DOM ürünlerini JSON-LD verisiyle zenginleştirir; DOM boşsa JSON-LD kullanılır.

    - DOM ve JSON-LD'de aynı URL varsa: eksik alanlar (isbn/currency/availability/
      image) JSON-LD'den doldurulur.
    - Yalnızca JSON-LD'de olan ürünler (fiyatı olanlar) sona eklenir.
    - DOM sırası korunur; veri kaybı olmaz.
    """
    merged = list(dom_items)
    by_url = {str(item.get("url", "")).split("?")[0]: item for item in merged}
    for ld in ld_items:
        key = str(ld.get("url", "")).split("?")[0]
        target = by_url.get(key)
        if target is not None:
            for field in ("isbn", "currency", "availability"):
                if not target.get(field) and ld.get(field):
                    target[field] = ld[field]
            if not target.get("image_url") and ld.get("image_url"):
                target["image_url"] = ld["image_url"]
            continue
        if ld.get("price") is not None or ld.get("price_text"):
            merged.append(ld)
    return merged
