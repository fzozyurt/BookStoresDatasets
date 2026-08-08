from datetime import UTC, datetime

from bookdata.models import Product
from bookdata.pipeline.merge import diff_products


def make_product(url: str, price: float) -> Product:
    return Product(
        title="Kitap",
        author="Yazar",
        publisher="Yayın",
        category="Edebiyat",
        price=price,
        url=url,
        store="BKM Kitap",
        scraped_at=datetime.now(UTC),
    )


def test_diff_keeps_new_and_changed():
    products = [make_product("a", 10.0), make_product("b", 20.0)]
    last = {"a": 10.0, "b": 25.0}
    changed = diff_products(products, last)
    assert {p.url for p in changed} == {"b"}


def test_diff_keeps_new_urls():
    changed = diff_products([make_product("yeni", 5.0)], {})
    assert len(changed) == 1


def test_diff_skips_unchanged():
    changed = diff_products([make_product("a", 10.0)], {"a": 10.0})
    assert changed == []
