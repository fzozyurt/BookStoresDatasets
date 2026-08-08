"""Veri deposu: veri setini CSV olarak okur/yazar ve fiyat geçmişini tutar."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from bookdata.models import Product

logger = logging.getLogger(__name__)

HEADER = ["Kitap İsmi", "Yazar", "Yayınevi", "Kategori", "Fiyat", "URL", "Site", "Tarih", "Resim"]


class DatasetStore:
    """Standart şemadaki CSV veri setini yönetir.

    - `load()`: geçmiş kayıtları okur
    - `last_price_by_url()`: her URL için son bilinen fiyatı O(n) döndürür
    - `append()`: yeni kayıtları dosyaya ekler
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh, delimiter=";"))

    def last_price_by_url(self) -> dict[str, float]:
        """Her URL için son kayıttaki fiyatı döndürür (Tarih'e göre en güncel)."""
        latest: dict[str, tuple[str, float]] = {}
        for row in self.load():
            url = row.get("URL", "")
            if not url:
                continue
            try:
                price = float(row.get("Fiyat", "0"))
            except ValueError:
                continue
            scraped_at = row.get("Tarih", "")
            if url not in latest or scraped_at >= latest[url][0]:
                latest[url] = (scraped_at, price)
        return {url: price for url, (_, price) in latest.items()}

    def append(self, products: list[Product]) -> int:
        if not products:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.path.exists()
        with self.path.open(mode="a", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh, delimiter=";")
            if not exists:
                writer.writerow(HEADER)
            for product in products:
                writer.writerow(product.to_csv_row())
        logger.info("Veri setine %s yeni kayıt eklendi: %s", len(products), self.path)
        return len(products)

    def row_count(self) -> int:
        if not self.path.exists():
            return 0
        with self.path.open(encoding="utf-8", newline="") as fh:
            return sum(1 for _ in fh) - 1
