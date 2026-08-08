from bookdata.pipeline.standardize import parse_price


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
