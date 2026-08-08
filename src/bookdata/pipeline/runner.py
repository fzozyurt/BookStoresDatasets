"""Pipeline orkestrasyonu: aşamaları sırayla çalıştırır.

1. Kategorileri çek (StorePort.fetch_categories)
2. Ignore kurallarına göre filtrele (filter.apply_ignore)
3. Kategori bazlı ürün sayfalarını çek (products.collect_products)
4. Veriyi standart şemaya dönüştür (standardize.standardize)
5. Mevcut fiyat geçmişiyle karşılaştır (merge.diff_products)
6. Değişen kayıtları veri setine ekle (DatasetStore.append)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from bookdata.adapters.http import AsyncHTTPClient
from bookdata.adapters.storage import DatasetStore
from bookdata.adapters.stores.base import StorePort
from bookdata.adapters.stores.bkm import BkmKitapAdapter
from bookdata.adapters.stores.kitapyurdu import KitapYurduAdapter
from bookdata.config import Settings
from bookdata.pipeline import filter as category_filter
from bookdata.pipeline import merge, products, standardize

logger = logging.getLogger(__name__)

STORE_REGISTRY: dict[str, type[StorePort]] = {
    "bkm": BkmKitapAdapter,
    "kitapyurdu": KitapYurduAdapter,
}


@dataclass
class ScrapeResult:
    categories_found: int
    categories_scraped: int
    products_scraped: int
    rows_written: int
    total_rows: int
    fetch_count: int
    fail_count: int


def get_store_class(settings: Settings) -> type[StorePort]:
    adapter_cls = STORE_REGISTRY.get(settings.store)
    if adapter_cls is None:
        options = ", ".join(STORE_REGISTRY)
        raise KeyError(f"Bilinmeyen mağaza: {settings.store}. Seçenekler: {options}")
    return adapter_cls


async def run_scrape(settings: Settings) -> ScrapeResult:
    async with AsyncHTTPClient(settings) as http:
        adapter_cls = get_store_class(settings)
        store = adapter_cls(http, settings)
        dataset = DatasetStore(settings.dataset_file)

        raw_categories = await store.fetch_categories()
        categories = category_filter.apply_ignore(raw_categories, settings.load_ignore_patterns())

        raw_items = await products.collect_products(store, categories, settings.concurrency)
        normalized = standardize.standardize(raw_items, store.store, store.display_name)
        last_prices = dataset.last_price_by_url()
        changed = merge.diff_products(normalized, last_prices)
        written = dataset.append(changed)

        result = ScrapeResult(
            categories_found=len(raw_categories),
            categories_scraped=len(categories),
            products_scraped=len(normalized),
            rows_written=written,
            total_rows=dataset.row_count(),
            fetch_count=store.stats["fetch"],
            fail_count=store.stats["fail"],
        )
        logger.info(
            "Özet: %s kategori bulundu, %s işlendi; %s ürün → %s kayıt eklendi (toplam %s). "
            "İstek: %s, hata: %s",
            result.categories_found,
            result.categories_scraped,
            result.products_scraped,
            result.rows_written,
            result.total_rows,
            result.fetch_count,
            result.fail_count,
        )
        return result
