"""Dashboard üretici: analiz sonuçlarını interaktif HTML'e çevirir (plotly)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px

from bookdata.analyze import price_changes, summary, weekly_trends


def _bar(df: pd.DataFrame, x: str, y: str, color: str, title: str) -> str:
    fig = px.bar(df, x=x, y=y, color=color, title=title, text_auto=".1f")
    return fig.to_html(full_html=False, include_plotlyjs=False)


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
</div>
<div class="chart">{chart_site}</div>
<div class="chart">{chart_cat}</div>
<div class="chart">{chart_trend}</div>
<div class="chart">{chart_up}</div>
<div class="chart">{chart_down}</div>
</body>
</html>"""


def save_dashboard(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dashboard(df), encoding="utf-8")
    return path
