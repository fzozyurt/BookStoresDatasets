from pathlib import Path

from bs4 import BeautifulSoup

from bookdata.pipeline.extract import (
    extract_isbn,
    merge_products,
    parse_json_ld,
    product_from_ld,
    products_from_json_ld,
)

FIXTURES = Path(__file__).parent / "fixtures"


def soup(name: str) -> BeautifulSoup:
    return BeautifulSoup((FIXTURES / name).read_text(encoding="utf-8"), "html.parser")


def test_parse_json_ld_returns_blocks():
    blocks = parse_json_ld(soup("product_jsonld.html"))
    assert len(blocks) == 1
    assert blocks[0]["@type"] == "Book"


def test_parse_json_ld_flattens_graph():
    blocks = parse_json_ld(soup("broken_jsonld.html"))
    assert len(blocks) == 2
    assert any(b.get("@type") == "Product" for b in blocks)


def test_parse_json_ld_skips_broken_block():
    blocks = parse_json_ld(soup("broken_jsonld.html"))
    assert all(isinstance(b, dict) for b in blocks)


def test_parse_json_ld_empty_without_scripts():
    assert parse_json_ld(soup("bkm_card.html")) == []


def test_products_from_book_json_ld():
    products = products_from_json_ld(soup("product_jsonld.html"), "Edebiyat")
    assert len(products) == 1
    p = products[0]
    assert p["title"] == "Güneşi Uyandıralım"
    assert p["price"] == 199.6
    assert p["currency"] == "TRY"
    assert p["availability"] == "Stokta"
    assert p["isbn"] == "9789753638029"
    assert p["url"] == "https://www.bkmkitap.com/gunesi-uyandiralim"
    assert p["image_url"]


def test_products_from_itemlist_skips_zero_price():
    products = products_from_json_ld(soup("itemlist_jsonld.html"), "Kategori")
    assert len(products) == 1
    assert products[0]["title"] == "Kitap A"
    assert products[0]["availability"] == "Stokta yok"


def test_products_none_without_json_ld():
    assert products_from_json_ld(soup("bkm_card.html"), "Edebiyat") == []


def test_extract_isbn():
    assert extract_isbn("ISBN 9789753638029 yanı") == "9789753638029"
    assert extract_isbn("9753638027") == "9753638027"
    assert extract_isbn("hiçbir şey") == ""


def test_availability_mapping():
    items = products_from_json_ld(soup("itemlist_jsonld.html"), "x")
    assert items[0]["availability"] == "Stokta yok"


def test_product_from_ld_requires_type_and_price():
    assert product_from_ld({"@type": "WebSite", "name": "x"}, "k") is None
    assert product_from_ld({"@type": "Product", "name": "x"}, "k") is None
    assert product_from_ld({"@type": "Product", "name": "x", "offers": {"price": "0"}}, "k") is None


def test_product_from_ld_aggregate_offer_lowprice():
    data = {
        "@type": "Product",
        "name": "Kitap",
        "offers": {"@type": "AggregateOffer", "lowPrice": "25.50", "priceCurrency": "TRY"},
    }
    p = product_from_ld(data, "k")
    assert p is not None
    assert p["price"] == 25.5


def test_product_from_ld_offers_list_form():
    data = {
        "@type": "Product",
        "name": "Kitap",
        "offers": [
            {"@type": "Offer", "price": "0"},
            {"@type": "Offer", "price": "12,75", "priceCurrency": "TRY"},
        ],
    }
    p = product_from_ld(data, "k")
    assert p is not None
    assert p["price"] == 12.75


def test_merge_products_enriches_dom_by_url():
    dom = [
        {
            "title": "Kitap",
            "price_text": "199,60",
            "url": "https://x.com/kitap",
            "category": "Edebiyat",
        }
    ]
    ld = [
        {
            "title": "Kitap",
            "price": 199.6,
            "url": "https://x.com/kitap",
            "isbn": "9789753638029",
            "currency": "TRY",
            "availability": "Stokta",
            "image_url": "https://img/x.jpg",
        }
    ]
    merged = merge_products(dom, ld)
    assert len(merged) == 1
    assert merged[0]["isbn"] == "9789753638029"
    assert merged[0]["currency"] == "TRY"
    assert merged[0]["availability"] == "Stokta"
    assert merged[0]["image_url"] == "https://img/x.jpg"


def test_merge_products_appends_ld_only_items():
    dom = [{"title": "A", "url": "https://x.com/a", "price_text": "10"}]
    ld = [
        {"title": "B", "price": 20.0, "url": "https://x.com/b", "price_text": "20"},
        {"title": "C", "price_text": "30", "url": "https://x.com/c"},
        {"title": "D", "url": "https://x.com/d"},
    ]
    merged = merge_products(dom, ld)
    assert [p["title"] for p in merged] == ["A", "B", "C"]
