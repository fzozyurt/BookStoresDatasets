"""Kitapyurdu adapter'ı.

- Kategoriler: ana sayfa menüsündeki `/kategori/kitap-{slug}/{id}.html` linkleri
- Sayfalama: `route=product/list&category_id={id}&limit=100&page={n}` (sayfa boşalana dek)
- Ürün kartı: `div.ky-product`
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator

from bs4 import BeautifulSoup

from bookdata.adapters.stores.base import StorePort
from bookdata.models import Category

_PRODUCT_CARD = "ky-product"


class KitapYurduAdapter(StorePort):
    store = "kitapyurdu"
    display_name = "Kitap Yurdu"
    site_url = "https://www.kitapyurdu.com"
    domain = "www.kitapyurdu.com"

    async def fetch_categories(self) -> list[Category]:
        soup = await self.get_soup(f"{self.site_url}/")
        categories: list[Category] = []
        seen: set[str] = set()
        for link in soup.select('a[href*="/kategori/kitap-"]'):
            href = link.get("href", "")
            category_id = re.search(r"/kategori/[^/]+/(\d+)\.html", href)
            if not category_id or href in seen:
                continue
            seen.add(href)
            categories.append(
                Category(
                    name=link.get_text(strip=True) or href.rsplit("/", 1)[-1].split(".")[0],
                    url=href,
                )
            )
        return categories

    async def iter_pages(self, category: Category) -> AsyncIterator[BeautifulSoup]:
        category_id = re.search(r"/(\d+)\.html$", category.url)
        if not category_id:
            return
        base = (
            f"{self.site_url}/index.php?route=product/list"
            f"&category_id={category_id.group(1)}&limit=100"
        )
        for page in range(1, self.settings.per_category_max_pages + 1):
            url = f"{base}&page={page}"
            soup = await self.get_soup(url)
            if not soup.select(f".{_PRODUCT_CARD}"):
                break
            yield soup

    def parse_dom_products(self, soup: BeautifulSoup, category: Category) -> list[dict]:
        raw: list[dict] = []
        for card in soup.select(f"div.{_PRODUCT_CARD}"):
            title = card.select_one(".ky-product-title")
            price = card.select_one(".ky-product-sell-price")
            cover = card.select_one("a.ky-product-cover")
            author = card.select_one(".ky-product-author a")
            publisher = card.select_one(".ky-product-publisher a")
            img = cover.find("img") if cover else None

            if not title or not price or not cover:
                continue

            url = re.sub(r"[\?&].*$", "", cover.get("href", ""))
            raw.append(
                {
                    "title": title.get_text(strip=True),
                    "author": author.get_text(strip=True) if author else "",
                    "publisher": publisher.get_text(strip=True) if publisher else "",
                    "category": category.name,
                    "price_text": price.get_text(strip=True).replace("TL", "").strip(),
                    "url": url if url.startswith("http") else f"{self.site_url}{url}",
                    "image_url": img.get("src") if img else None,
                }
            )
        return raw
