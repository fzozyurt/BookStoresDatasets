from pathlib import Path

import pandas as pd
import pytest

from bookdata.analyze import load_datasets, price_changes, summary, weekly_trends

COLS = ["Tarih", "URL", "Fiyat", "Kitap İsmi", "Site", "Kategori"]


def _frame(rows):
    df = pd.DataFrame(rows, columns=COLS)
    df["Tarih"] = pd.to_datetime(df["Tarih"])
    return df


def test_price_changes_returns_last_two():
    df = _frame(
        [
            ["2026-01-01", "/a", 100, "Kitap A", "bkm", "Roman"],
            ["2026-02-01", "/a", 120, "Kitap A", "bkm", "Roman"],
            ["2026-03-01", "/a", 110, "Kitap A", "bkm", "Roman"],
        ]
    )
    ch = price_changes(df)
    assert len(ch) == 1
    row = ch.iloc[0]
    assert row["İlkFiyat"] == 120
    assert row["SonFiyat"] == 110
    assert row["Değişim"] == -10


def test_price_changes_skips_single_record_and_unchanged():
    df = _frame(
        [
            ["2026-01-01", "/tek", 100, "Tek", "bkm", "Roman"],
            ["2026-01-01", "/sabit", 50, "Sabit", "bkm", "Roman"],
            ["2026-02-01", "/sabit", 50, "Sabit", "bkm", "Roman"],
        ]
    )
    ch = price_changes(df)
    assert ch.empty


def test_price_changes_multiple_urls_and_ordering():
    df = _frame(
        [
            ["2026-02-01", "/b", 200, "B", "bkm", "Roman"],
            ["2026-01-01", "/b", 150, "B", "bkm", "Roman"],
            ["2026-01-01", "/a", 10, "A", "bkm", "Roman"],
            ["2026-02-01", "/a", 15, "A", "bkm", "Roman"],
        ]
    )
    ch = price_changes(df).set_index("URL")
    assert ch.loc["/a", "SonFiyat"] == 15
    assert ch.loc["/b", "SonFiyat"] == 200
    assert len(ch) == 2


def test_weekly_trends_groups_by_week_and_site():
    df = _frame(
        [
            ["2026-01-01", "/a", 100, "A", "bkm", "Roman"],
            ["2026-01-02", "/b", 200, "B", "kitapyurdu", "Roman"],
            ["2026-01-08", "/a", 120, "A", "bkm", "Roman"],
        ]
    )
    trends = weekly_trends(df)
    assert set(trends["Site"]) == {"bkm", "kitapyurdu"}
    assert len(trends) == 3


def test_summary_counts():
    df = _frame(
        [
            ["2026-01-01", "/a", 100, "A", "bkm", "Roman"],
            ["2026-02-01", "/a", 120, "A", "bkm", "Roman"],
            ["2026-01-01", "/b", 50, "B", "bkm", "Roman"],
            ["2026-02-01", "/b", 40, "B", "bkm", "Roman"],
        ]
    )
    s = summary(df, price_changes(df))
    assert s["kayit_sayisi"] == 4
    assert s["toplam_urun"] == 2
    assert s["artan"] == 1
    assert s["azalan"] == 1
    assert s["son_goruntuleme"] == pd.Timestamp("2026-02-01")


def test_load_datasets_combines_files(tmp_path: Path):
    (tmp_path / "bkm_Datasets.csv").write_text(
        "Tarih;URL;Fiyat;Kitap İsmi;Site;Kategori\n2026-01-01;/a;100;A;bkm;Roman\n",
        encoding="utf-8",
    )
    (tmp_path / "ky_Datasets.csv").write_text(
        "Tarih;URL;Fiyat;Kitap İsmi;Site;Kategori\n2026-01-02;/b;50;B;kitapyurdu;Tarih\n",
        encoding="utf-8",
    )
    df = load_datasets(tmp_path)
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["Tarih"])
    assert set(df["Site"]) == {"bkm", "kitapyurdu"}


def test_load_datasets_ignores_non_matching_files(tmp_path: Path):
    (tmp_path / "nota_dataset.csv").write_text("x;y\n1;2\n", encoding="utf-8")
    df = load_datasets(tmp_path)
    assert df.empty
    assert list(df.columns) == COLS


def test_load_datasets_missing_column_raises(tmp_path: Path):
    (tmp_path / "bkm_Datasets.csv").write_text(
        "Tarih;URL;Fiyat;Kitap İsmi;Site\n2026-01-01;/a;100;A;bkm\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="eksik sütunlar"):
        load_datasets(tmp_path)
