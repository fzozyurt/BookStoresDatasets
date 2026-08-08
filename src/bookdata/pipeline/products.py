"""Ürün toplama aşaması: kategori port'u üzerinden tüm kategorilerin ürünlerini çeker."""

from __future__ import annotations

import asyncio
import logging
import random

from bookdata.adapters.stores.base import StorePort
from bookdata.models import Category

logger = logging.getLogger(__name__)


async def scrape_category(store: StorePort, category: Category) -> list[dict]:
    """Tek kategori için sayfaları gezer, ham ürün listesini toplar."""
    raw_items: list[dict] = []
    pages = 0
    try:
        async for soup in store.iter_pages(category):
            pages += 1
            raw_items.extend(store.parse_products(soup, category))
    except Exception as exc:  # noqa: BLE001 — tek kategori hatası diğerlerini etkilememeli
        logger.warning("Kategori işlenirken hata (%s): %s", category.name, exc)

    if raw_items:
        logger.info("Kategori '%s': %s sayfa, %s ürün", category.name, pages, len(raw_items))
    else:
        logger.info("Kategori '%s': ürün bulunamadı (%s sayfa)", category.name, pages)
    return raw_items


async def collect_products(
    store: StorePort, categories: list[Category], task_limit: int
) -> list[dict]:
    """Kategorileri sınırlı eşzamanlılıkla, karışık sırada işler.

    Sıralamayı her çalıştırmada rastgele karıştırmak, site tarafında
    öngörülebilir (bot benzeri) istek deseni oluşmasını engeller.
    """
    shuffled = list(categories)
    random.shuffle(shuffled)

    semaphore = asyncio.Semaphore(task_limit)

    async def _run(category: Category) -> list[dict]:
        async with semaphore:
            return await scrape_category(store, category)

    batches = await asyncio.gather(*(_run(c) for c in shuffled))
    return [item for batch in batches for item in batch]
