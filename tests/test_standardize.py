from bookdata.pipeline.standardize import normalize, parse_price


def test_parse_price_turkish_comma():
    assert parse_price("53,30") == 53.3


def test_parse_price_thousands():
    assert parse_price("1.234,50") == 1234.5


def test_parse_price_tl_suffix():
    assert parse_price("199,60TL") == 199.6


def test_parse_price_invalid():
    assert parse_price("") is None
    assert parse_price("abc") is None
    assert parse_price("0,00") is None


def test_normalize_keeps_json_ld_fields():
    raw = {
        "title": "Güneşi Uyandıralım",
        "url": "https://x.com/kitap",
        "price": 199.6,
        "isbn": "9789753638029",
        "currency": "TRY",
        "availability": "Stokta",
    }
    p = normalize(raw, "bkm", "BKM Kitap")
    assert p is not None
    assert p.price == 199.6
    assert p.isbn == "9789753638029"
    assert p.currency == "TRY"
    assert p.availability == "Stokta"


def test_normalize_numeric_price_without_text():
    p = normalize({"title": "K", "url": "u", "price": 1234.5}, "bkm", "BKM")
    assert p is not None
    assert p.price == 1234.5


def test_normalize_defaults():
    p = normalize({"title": "K", "url": "u", "price_text": "10,00"}, "bkm", "BKM")
    assert p is not None
    assert p.currency == "TRY"
    assert p.isbn == ""
    assert p.availability == ""


def test_normalize_skips_without_title_or_url():
    assert normalize({"price": 10.0}, "bkm", "BKM") is None
    assert normalize({"title": "K", "price": 10.0}, "bkm", "BKM") is None
