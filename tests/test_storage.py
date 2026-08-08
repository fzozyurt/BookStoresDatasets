from datetime import UTC, datetime
from pathlib import Path

from bookdata.adapters.storage import HEADER, DatasetStore
from bookdata.models import Product


def make_product(url: str, price: float, title: str = "Kitap") -> Product:
    return Product(
        title=title,
        author="Yazar",
        publisher="Yayın",
        category="Edebiyat",
        price=price,
        url=url,
        store="BKM Kitap",
        scraped_at=datetime.now(UTC),
    )


def test_append_and_load(tmp_path: Path):
    store = DatasetStore(tmp_path / "bkm_Datasets.csv")
    assert store.append([make_product("a", 10.0)]) == 1
    rows = store.load()
    assert len(rows) == 1
    assert rows[0]["URL"] == "a"
    assert float(rows[0]["Fiyat"]) == 10.0
    assert rows[0]["Site"] == "BKM Kitap"


def test_last_price_by_url_takes_latest(tmp_path: Path):
    store = DatasetStore(tmp_path / "bkm_Datasets.csv")
    older = make_product("a", 10.0)
    older.scraped_at = datetime(2025, 1, 1, tzinfo=UTC)
    newer = make_product("a", 15.0)
    newer.scraped_at = datetime(2025, 1, 2, tzinfo=UTC)
    store.append([older, newer])
    result = store.last_price_by_url()
    assert result == {"a": 15.0}


def test_header_contains_new_columns():
    assert "ISBN" in HEADER
    assert "Para Birimi" in HEADER
    assert "Stok Durumu" in HEADER


def test_roundtrip_new_fields(tmp_path: Path):
    store = DatasetStore(tmp_path / "bkm_Datasets.csv")
    product = Product(
        title="Güneşi Uyandıralım",
        author="Sabahattin Ali",
        publisher="YKY",
        category="Edebiyat",
        price=199.6,
        url="https://x.com/kitap",
        store="BKM Kitap",
        scraped_at=datetime(2025, 1, 1, tzinfo=UTC),
        isbn="9789753638029",
        currency="TRY",
        availability="Stokta",
    )
    assert store.append([product]) == 1
    rows = store.load()
    assert rows[0]["ISBN"] == "9789753638029"
    assert rows[0]["Para Birimi"] == "TRY"
    assert rows[0]["Stok Durumu"] == "Stokta"
