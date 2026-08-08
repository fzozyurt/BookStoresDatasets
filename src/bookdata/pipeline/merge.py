"""Birleştirme aşaması: yeni çekilen fiyatları mevcut geçmişle karşılaştırır.

Sadece fiyatı değişen (veya yeni eklenen) ürünler veri setine gider.
Değişmeyen ürünler tekrar yazılmaz → veri seti şişmez, çalışma hızlıdır.
"""

from __future__ import annotations

import logging

from bookdata.models import Product

logger = logging.getLogger(__name__)


def diff_products(products: list[Product], last_prices: dict[str, float]) -> list[Product]:
    changed: list[Product] = []
    for product in products:
        last = last_prices.get(product.url)
        if last is None or abs(last - product.price) > 1e-6:
            changed.append(product)
    logger.info(
        "Fiyat karşılaştırması: %s ürünün %s tanesinde değişiklik/yeni kayıt",
        len(products),
        len(changed),
    )
    return changed
