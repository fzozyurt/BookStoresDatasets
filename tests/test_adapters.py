from pathlib import Path

from bs4 import BeautifulSoup

from bookdata.adapters.stores.bkm import BkmKitapAdapter
from bookdata.adapters.stores.kitapyurdu import KitapYurduAdapter
from bookdata.config import Settings
from bookdata.models import Category
from bookdata.pipeline.runner import resolve_adapter

FIXTURES = Path(__file__).parent / "fixtures"


def soup(name: str) -> BeautifulSoup:
    return BeautifulSoup((FIXTURES / name).read_text(encoding="utf-8"), "html.parser")


def make_bkm() -> BkmKitapAdapter:
    return BkmKitapAdapter(http=None, settings=Settings())


def make_ky() -> KitapYurduAdapter:
    return KitapYurduAdapter(http=None, settings=Settings())


def test_bkm_dom_parsing_without_json_ld():
    category = Category(name="Edebiyat", url="https://www.bkmkitap.com/edebiyat")
    items = make_bkm().parse_dom_products(soup("bkm_card.html"), category)
    assert len(items) == 1
    item = items[0]
    assert item["title"] == "Güneşi Uyandıralım"
    assert item["price_text"] == "199,60"
    assert item["author"] == "Sabahattin Ali"
    assert item["publisher"] == "Yapı Kredi Yayınları"
    assert item["url"] == "https://www.bkmkitap.com/gunesi-uyandiralim"


def test_bkm_parse_products_merges_json_ld():
    category = Category(name="Edebiyat", url="https://www.bkmkitap.com/edebiyat")
    items = make_bkm().parse_products(soup("product_jsonld.html"), category)
    assert len(items) == 1
    assert items[0]["isbn"] == "9789753638029"
    assert items[0]["currency"] == "TRY"
    assert items[0]["availability"] == "Stokta"
    assert items[0]["price_text"] == "199,60"


def test_ky_dom_parsing():
    category = Category(name="Roman", url="https://www.kitapyurdu.com/kategori/kitap/roman/1.html")
    items = make_ky().parse_dom_products(soup("ky_card.html"), category)
    assert len(items) == 1
    item = items[0]
    assert item["title"] == "Kürk Mantolu Madonna"
    assert item["price_text"] == "89,90"
    assert item["author"] == "Sabahattin Ali"
    assert item["url"] == "https://www.kitapyurdu.com/kitap/kurk-mantolu-madonna/123.html"
    assert item["image_url"]


def test_resolve_adapter_bkm():
    assert resolve_adapter("https://www.bkmkitap.com/gunesi-uyandiralim") is BkmKitapAdapter


def test_resolve_adapter_kitapyurdu():
    assert resolve_adapter("https://www.kitapyurdu.com/kitap/roman/1.html") is KitapYurduAdapter


def test_resolve_adapter_unknown():
    assert resolve_adapter("https://example.com/x") is None
