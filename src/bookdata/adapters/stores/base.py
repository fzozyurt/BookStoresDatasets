"""Mağaza port'u (adapter arayüzü): BKM ve Kitapyurdu bu arayüzü uygular.

Adapter'lar sadece siteye özel olan işleri yapar:
- Kategori listesini çekmek
- Sayfalama dahil sayfa HTML'lerini üretmek
- Sayfa içinden ham ürün verilerini çıkarmak

Veri temizleme (fiyat, URL, kopya) bağımsız bir standardizasyon aşamasında yapılır.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from bs4 import BeautifulSoup

from bookdata.adapters.http import AsyncHTTPClient
from bookdata.config import Settings
from bookdata.models import Category

logger = logging.getLogger(__name__)


class StorePort(ABC):
    """Bir kitap sitesinin web arayüzünü modelleyen soyut port."""

    store: str
    display_name: str
    site_url: str

    def __init__(self, http: AsyncHTTPClient, settings: Settings) -> None:
        self.http = http
        self.settings = settings
        self._fetch_count = 0
        self._fail_count = 0

    async def get_soup(self, url: str) -> BeautifulSoup:
        self._fetch_count += 1
        try:
            response = await self.http.get(url)
            return BeautifulSoup(response.content, "html.parser")
        except Exception as exc:  # noqa: BLE001 — tek kategori hatası pipeline'ı durdurmamalı
            self._fail_count += 1
            logger.warning("Sayfa alınamadı (%s): %s", self.store, exc)
            raise

    @abstractmethod
    async def fetch_categories(self) -> list[Category]:
        """Sitedeki tüm kitap kategorilerini döndürür."""

    @abstractmethod
    def iter_pages(self, category: Category) -> AsyncIterator[BeautifulSoup]:
        """Kategoriye ait tüm sayfa HTML'lerini (sayfalama dahil) üretir."""

    @abstractmethod
    def parse_products(self, soup: BeautifulSoup, category: Category) -> list[dict]:
        """Sayfadan ham ürün dict'leri çıkarır."""

    @property
    def stats(self) -> dict[str, int]:
        return {"fetch": self._fetch_count, "fail": self._fail_count}
