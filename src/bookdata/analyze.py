"""Fiyat analizi: veri setinden fiyat değişimleri, trendler ve özetler üretir."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED = ["Tarih", "URL", "Fiyat", "Kitap İsmi", "Site", "Kategori"]


def load_datasets(data_dir: Path) -> pd.DataFrame:
    """Data dizinindeki tüm *_Datasets.csv dosyalarını tek DataFrame'de birleştirir."""
    frames: list[pd.DataFrame] = []
    for path in sorted(data_dir.glob("*_Datasets.csv")):
        df = pd.read_csv(path, sep=";", encoding="utf-8", parse_dates=["Tarih"])
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"{path.name}: eksik sütunlar {missing}")
        df = df.dropna(subset=["Tarih", "Fiyat"])
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=REQUIRED)


def price_changes(df: pd.DataFrame) -> pd.DataFrame:
    """Her URL için son iki kaydı alıp fiyat değişimini hesaplar.

    Vektörel `groupby().nth()` kullanır; yalnızca en az iki kaydı olan URL'ler döner.
    """
    data = df.sort_values(["URL", "Tarih"])
    g = data.groupby("URL", sort=False)
    prev = g.nth(-2)
    last = g.nth(-1)
    merged = prev.merge(last, on="URL", suffixes=("_ilk", "_son"), how="inner")

    result = pd.DataFrame(
        {
            "URL": merged["URL"],
            "İlkFiyat": merged["Fiyat_ilk"],
            "SonFiyat": merged["Fiyat_son"],
            "Kitap": merged["Kitap İsmi_son"],
            "Site": merged["Site_son"],
            "Kategori": merged["Kategori_son"],
            "Tarih": merged["Tarih_son"],
        }
    )
    result["Değişim"] = (result["SonFiyat"] - result["İlkFiyat"]).astype("float64")
    result["Değişim %"] = (result["Değişim"] / result["İlkFiyat"] * 100).astype("float64")
    return result[result["Değişim"].abs() > 1e-6]


def weekly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Haftalık ortalama fiyatları site bazında döndürür."""
    data = df.copy()
    data["Hafta"] = data["Tarih"].dt.isocalendar().week.astype(str) + ".Hafta"
    return data.groupby(["Hafta", "Site"], as_index=False)["Fiyat"].mean()


def summary(df: pd.DataFrame, changes: pd.DataFrame) -> dict[str, float | int]:
    up = changes[changes["Değişim"] > 0]
    down = changes[changes["Değişim"] < 0]
    return {
        "toplam_urun": int(changes["URL"].nunique()),
        "artan": int(len(up)),
        "azalan": int(len(down)),
        "ortalama_artis": float(up["Değişim %"].mean()) if not up.empty else 0.0,
        "ortalama_azalis": float(down["Değişim %"].mean()) if not down.empty else 0.0,
        "kayit_sayisi": int(len(df)),
        "son_goruntuleme": df["Tarih"].max(),
    }
