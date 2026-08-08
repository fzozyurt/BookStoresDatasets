import pandas as pd

from bookdata.dashboard import render_dashboard

COLS = ["Tarih", "URL", "Fiyat", "Kitap İsmi", "Site", "Kategori"]


def _frame(rows):
    df = pd.DataFrame(rows, columns=COLS)
    df["Tarih"] = pd.to_datetime(df["Tarih"])
    return df


def test_render_dashboard_basic_structure():
    df = _frame(
        [
            ["2026-01-01", "/a", 100, "A", "bkm", "Roman"],
            ["2026-02-01", "/a", 120, "A", "bkm", "Roman"],
            ["2026-01-01", "/b", 50, "B", "kitapyurdu", "Tarih"],
            ["2026-02-01", "/b", 40, "B", "kitapyurdu", "Tarih"],
        ]
    )
    html = render_dashboard(df)
    assert html.startswith("<!DOCTYPE html>")
    assert "Kitap Fiyatları Dashboard" in html
    assert "Artan ürün" in html
    assert "Azalan ürün" in html
    assert "plotly" in html


def test_render_dashboard_empty_data_returns_valid_html():
    df = pd.DataFrame(columns=COLS)
    df["Tarih"] = pd.to_datetime(df["Tarih"])
    html = render_dashboard(df)
    assert html.startswith("<!DOCTYPE html>")
    assert "4 kayıt" not in html
