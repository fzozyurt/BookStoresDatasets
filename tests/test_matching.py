import pandas as pd

from bookdata.matching import (
    Confidence,
    author_similarity,
    cross_store_prices,
    decide_pair,
    isbn_key,
    match_products,
    normalize_text,
    title_similarity,
    unique_listings,
)


def row(
    url="u1",
    title="Güneşi Uyandıralım",
    author="Sabahattin Ali",
    publisher="Yapı Kredi",
    isbn="",
    site="BKM Kitap",
    price=199.6,
):
    return {
        "URL": url,
        "Kitap İsmi": title,
        "Yazar": author,
        "Yayınevi": publisher,
        "ISBN": isbn,
        "Site": site,
        "Fiyat": price,
    }


def test_normalize_text_folds_turkish():
    assert normalize_text("Şehir Şiirleri Ğüzel") == "sehir siirleri guzel"
    assert normalize_text("J. K. Rowling!") == "j k rowling"


def test_isbn_key_strips_separators():
    assert isbn_key("978-975-363-8029") == "9789753638029"
    assert isbn_key(" 9789753638029 ") == "9789753638029"
    assert isbn_key("kısa") == ""


def test_author_similarity_handles_spelling_and_order():
    assert author_similarity("Sabahattin Ali", "Sabahattin Ali") == 1.0
    assert author_similarity("Rowling, J.K.", "J. K. Rowling") >= 0.9
    assert author_similarity("Ahmet Güneş", "") is None


def test_title_similarity_handles_typos():
    assert title_similarity("Kürk Mantolu Madonna", "Kürk Mantalu Madonna") >= 0.95
    assert title_similarity("Kürk Mantolu Madonna", "Sokrates'in Savunması") < 0.75


def test_isbn_match_is_deterministic():
    decision = decide_pair(
        row(isbn="9789753638029"), row(url="u2", isbn="978-975-363-8029"), publisher_equal=False
    )
    assert decision is not None
    assert decision.method == "isbn"
    assert decision.confidence is Confidence.MATCH
    assert decision.score == 1.0


def test_same_publisher_identical_title_matches():
    decision = decide_pair(row(), row(url="u2", publisher="yapı kredi"), publisher_equal=True)
    assert decision is not None
    assert decision.confidence is Confidence.MATCH
    assert decision.method == "title"


def test_same_publisher_typo_title_matches():
    decision = decide_pair(
        row(title="Kürk Mantolu Madonna"),
        row(url="u2", title="Kürk Mantalu Madonna"),
        publisher_equal=True,
    )
    assert decision is not None
    assert decision.confidence is Confidence.MATCH


def test_same_publisher_moderate_title_is_review():
    decision = decide_pair(
        row(title="Güneşi Uyandıralım"),
        row(url="u2", title="Güneşi Uyandıralım (2 Cilt Takım)"),
        publisher_equal=True,
    )
    assert decision is not None
    assert decision.confidence is Confidence.REVIEW


def test_same_publisher_different_title_is_different():
    assert (
        decide_pair(
            row(title="Güneşi Uyandıralım"),
            row(url="u2", title="Sokrates'in Savunması"),
            publisher_equal=True,
        )
        is None
    )


def test_author_conflict_blocks_match():
    decision = decide_pair(
        row(title="Matematik 1", author="Ahmet Demir"),
        row(url="u2", title="Matematik 1", author="Ayşe Yılmaz"),
        publisher_equal=True,
    )
    assert decision is not None
    assert decision.confidence is Confidence.REVIEW


def test_same_title_different_publisher_is_variant_review():
    decision = decide_pair(
        row(title="Kürk Mantolu Madonna", publisher="YKY"),
        row(url="u2", title="Kürk Mantolu Madonna", publisher="İş Bankası"),
        publisher_equal=False,
    )
    assert decision is not None
    assert decision.confidence is Confidence.REVIEW
    assert decision.method == "title-variant"


def test_match_products_isbn_connects_stores():
    products = [
        row("bkm-1", isbn="9789753638029"),
        row("ky-1", site="Kitap Yurdu", isbn="9789753638029"),
    ]
    result = match_products(products)
    assert len(result.matched) == 1
    assert len(result.groups) == 1
    assert result.groups[0].stores == {"BKM Kitap", "Kitap Yurdu"}


def test_match_products_groups_three_listings():
    products = [
        row("bkm-1", title="Kürk Mantolu Madonna"),
        row("ky-1", site="Kitap Yurdu", title="Kürk Mantolu Madonna"),
        row("ky-2", site="Kitap Yurdu", title="Kürk Mantalu Madonna"),
    ]
    result = match_products(products)
    assert len(result.groups) == 1
    assert set(result.groups[0].urls) == {"bkm-1", "ky-1", "ky-2"}


def test_match_products_no_cross_publisher_compare():
    products = [
        row("a", title="Farklı Kitap", publisher="Yayın A", author="Yazar A"),
        row("b", title="Başka Kitap", publisher="Yayın B", author="Yazar B"),
    ]
    result = match_products(products)
    assert result.decisions == []
    assert result.different_count == 0


def test_match_products_empty():
    result = match_products([])
    assert result.decisions == []
    assert result.groups == []
    assert result.different_count == 0


def test_unique_listings_keeps_latest():
    df = pd.DataFrame(
        {
            "URL": ["u1", "u1"],
            "Fiyat": [10.0, 20.0],
            "Tarih": pd.to_datetime(["2025-01-01", "2025-01-02"]),
        }
    )
    out = unique_listings(df)
    assert len(out) == 1
    assert out.iloc[0]["Fiyat"] == 20.0


def test_cross_store_prices_only_confident_groups():
    products = [
        row("bkm-1", isbn="9789753638029", price=199.6),
        row("ky-1", site="Kitap Yurdu", isbn="9789753638029", price=189.0),
        row("ky-2", site="Kitap Yurdu", title="Başka Kitap", author="Başka Yazar", publisher="X"),
    ]
    comp = cross_store_prices(products)
    assert {"BKM Kitap", "Kitap Yurdu"} <= set(comp["Site"])
    assert len(comp) == 2
    assert comp.loc[comp["Site"] == "Kitap Yurdu", "Fiyat"].iloc[0] == 189.0
