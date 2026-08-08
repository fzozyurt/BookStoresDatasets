"""Dashboard üretici: analiz sonuçlarını interaktif HTML'e çevirir (plotly)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px

from bookdata.analyze import price_changes, summary, weekly_trends
from bookdata.matching import cross_store_prices, match_products, unique_listings


def _bar(df: pd.DataFrame, x: str, y: str, color: str, title: str) -> str:
    fig = px.bar(df, x=x, y=y, color=color, title=title, text_auto=".1f")
    return fig.to_html(full_html=False, include_plotlyjs=False)


def _horizontal_grouped_bar(df: pd.DataFrame, title: str, limit: int = 15) -> str:
    fig = px.bar(
        df,
        x="Fiyat",
        y="Kitap",
        color="Site",
        title=title,
        orientation="h",
        barmode="group",
        text_auto=".2f",
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def _compare_chart(products: list[dict]) -> tuple[str, int, int]:
    """Mağazalar arası eşleşen kitapların fiyat karşılaştırmasını üretir."""
    result = match_products(products)
    comp = cross_store_prices(products, result=result)
    if comp.empty:
        return "", len(result.groups), len(result.review)
    wide = (
        comp.pivot_table(index=["Anahtar", "Kitap"], columns="Site", values="Fiyat", aggfunc="min")
        .reset_index()
        .dropna()
    )
    store_cols = [c for c in wide.columns if c not in ("Anahtar", "Kitap")]
    if len(store_cols) < 2:
        return "", len(result.groups), len(result.review)
    wide["Fark %"] = (
        (wide[store_cols].max(axis=1) - wide[store_cols].min(axis=1))
        / wide[store_cols].min(axis=1)
        * 100
    )
    top = wide.reindex(wide["Fark %"].abs().sort_values(ascending=False).index).head(15)
    long = top.melt(id_vars=["Kitap"], value_vars=store_cols, var_name="Site", value_name="Fiyat")
    chart = _horizontal_grouped_bar(
        long, "Eşleşen Kitaplar: Mağaza Fiyat Karşılaştırması (en büyük fark)"
    )
    return chart, len(result.groups), len(result.review)


def _line(df: pd.DataFrame, title: str) -> str:
    fig = px.line(df, x="Hafta", y="Fiyat", color="Site", title=title, markers=True)
    return fig.to_html(full_html=False, include_plotlyjs=False)


def render_dashboard(df: pd.DataFrame) -> str:
    """Veri setinden tek sayfalık interaktif dashboard HTML'i üretir."""
    changes = price_changes(df)
    stats = summary(df, changes)
    trends = weekly_trends(df)

    site_stats = (
        changes.groupby("Site")
        .agg(Ortalama=("Değişim %", "mean"), Ürün=("URL", "count"))
        .reset_index()
    )
    category_stats = (
        changes.groupby(["Kategori", "Site"]).agg(Ortalama=("Değişim %", "mean")).reset_index()
    )

    top_up = changes.nlargest(10, "Değişim %")
    top_down = changes.nsmallest(10, "Değişim %")

    listings = unique_listings(df)
    chart_compare, matched_groups, review_count = _compare_chart(listings.to_dict("records"))

    last_view = (
        f"{stats['son_goruntuleme']:%d.%m.%Y}" if not pd.isna(stats["son_goruntuleme"]) else "—"
    )
    up = f"{stats['ortalama_artis']:.1f}"
    down = f"{stats['ortalama_azalis']:.1f}"
    chart_site = _bar(site_stats, "Site", "Ortalama", "Site", "Site Bazında Ortalama Değişim %")
    chart_cat = _bar(category_stats, "Kategori", "Ortalama", "Site", "Kategori Bazında Değişim %")
    chart_trend = _line(trends, "Haftalık Ortalama Fiyat")
    chart_up = _bar(top_up, "Kitap", "Değişim %", "Site", "En Çok Artan 10 Kitap")
    chart_down = _bar(top_down, "Kitap", "Değişim %", "Site", "En Çok Düşen 10 Kitap")

    compare_section = (
        f'<div class="chart">{chart_compare}</div>'
        if chart_compare
        else '<div class="chart">Eşleşen çoklu mağaza kitabı bulunamadı.</div>'
    )
    compare_stat = (
        f'<div class="stat">Eşleşen kitap <b>{matched_groups}</b> incelemede {review_count}</div>'
    )

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kitap Fiyatları Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; background: #f5f6f8; color: #222; }}
  header {{ background: #1f2937; color: #fff; padding: 20px; }}
  .stats {{ display: flex; gap: 16px; padding: 16px; flex-wrap: wrap; }}
  .stat {{ background: #fff; border-radius: 10px; padding: 16px 24px; flex: 1;
           min-width: 150px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .stat b {{ font-size: 26px; display: block; }}
  .chart {{ background: #fff; margin: 0 16px 16px; border-radius: 10px; padding: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .up {{ color: #dc2626; }} .down {{ color: #16a34a; }}
</style>
</head>
<body>
<header><h1>📚 Kitap Fiyatları Dashboard</h1>
<p>{stats["kayit_sayisi"]} kayıt · {stats["toplam_urun"]} ürün · son görüntüleme {last_view}
</p></header>
<div class="stats">
  <div class="stat">Artan ürün <b class="up">{stats["artan"]}</b> ort. %{up}</div>
  <div class="stat">Azalan ürün <b class="down">{stats["azalan"]}</b> ort. %{down}</div>
  {compare_stat}
</div>
<div class="chart">{chart_site}</div>
<div class="chart">{chart_cat}</div>
<div class="chart">{chart_trend}</div>
<div class="chart">{chart_up}</div>
<div class="chart">{chart_down}</div>
{compare_section}
</body>
</html>"""


def save_dashboard(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dashboard(df), encoding="utf-8")
    return path
