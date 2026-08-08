"""BKM Kitap adapter'ı.

- Kategoriler: ana menüdeki (`#header-main`) kategori linkleri
- Sayfalama: sunucu sayfalama linki (`pg=`) varsa takip edilir; yoksa tek sayfa çekilir.
  (BKM sayfalama şu an JS tarafında çalıştığından, algılanamayan durumda sayfa-1 verisi
  alınır ve bu durum loga yazılır.)
- Ürün kartı: `div.product-item`
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator

from bs4 import BeautifulSoup

from bookdata.adapters.stores.base import StorePort
from bookdata.models import Category


class BkmKitapAdapter(StorePort):
    store = "bkm"
    display_name = "BKM Kitap"
    site_url = "https://www.bkmkitap.com"
    domain = "www.bkmkitap.com"

    async def fetch_categories(self) -> list[Category]:
        soup = await self.get_soup(f"{self.site_url}/kategori-listesi")
        categories: list[Category] = []
        seen: set[str] = set()
        for link in soup.select('#header-main a[id^="menu-"]'):
            href = link.get("href", "")
            if not href.startswith("http"):
                continue
            if href in seen:
                continue
            seen.add(href)
            title = link.get("title") or link.get_text(strip=True)
            categories.append(Category(name=title, url=href, parent=None))
        return categories

    async def iter_pages(self, category: Category) -> AsyncIterator[BeautifulSoup]:
        url = category.url
        soup = await self.get_soup(url)
        yield soup

        last_page = self._last_pg_link(soup)
        if last_page and last_page > 1:
            for page in range(2, min(last_page, self.settings.per_category_max_pages) + 1):
                sep = "&" if "?" in url else "?"
                yield await self.get_soup(f"{url}{sep}pg={page}")

    @staticmethod
    def _last_pg_link(soup: BeautifulSoup) -> int:
        pages = []
        for a in soup.select("div.pagination a[href*='pg=']"):
            match = re.search(r"pg=(\d+)", a.get("href", ""))
            if match:
                pages.append(int(match.group(1)))
        return max(pages, default=0)

    def parse_dom_products(self, soup: BeautifulSoup, category: Category) -> list[dict]:
        raw: list[dict] = []
        for item in soup.select("div.product-item"):
            title = item.select_one("a.product-title")
            price = item.select_one("span.product-price")
            author = item.select_one("a.model-title")
            publisher = item.select_one("a.brand-title")
            img = item.select_one("img[data-src]")

            if not title or not price:
                continue

            url = title.get("href", "")
            raw.append(
                {
                    "title": title.get_text(strip=True),
                    "author": author.get_text(strip=True) if author else "",
                    "publisher": publisher.get_text(strip=True) if publisher else "",
                    "category": category.name,
                    "price_text": price.get_text(strip=True).replace("TL", "").strip(),
                    "url": url if url.startswith("http") else f"{self.site_url}{url}",
                    "image_url": img.get("data-src") if img else None,
                }
            )
        return raw
