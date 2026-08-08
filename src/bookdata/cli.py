"""Kitap fiyat izleme CLI'sı.

Kullanım (uv):
    uv run bookdata scrape bkm
    uv run bookdata scrape kitapyurdu
    uv run bookdata publish bkm
    uv run bookdata categories bkm
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import Annotated

import typer

from bookdata.config import Settings
from bookdata.logging_setup import get_logger, setup_logging
from bookdata.pipeline import get_store_class, run_scrape

logger = get_logger(__name__)

app = typer.Typer(help="BKM ve Kitapyurdu kitap fiyatı izleme aracı.")

_STORE_ALIASES = {"KY": "kitapyurdu", "BKM": "bkm"}


def _store_name(value: str) -> str:
    name = _STORE_ALIASES.get(value.upper(), value.lower())
    if name not in ("bkm", "kitapyurdu"):
        raise typer.BadParameter(f"Bilinmeyen mağaza: {value}")
    return name


def _settings(store: str | None = None) -> Settings:
    base = Settings.from_env()
    if store:
        return replace(base, store=_store_name(store))
    return base


@app.command()
def scrape(
    store: Annotated[str, typer.Argument(help="bkm veya kitapyurdu (KY/BKM de kabul edilir)")],
    log_file: Annotated[str | None, typer.Option("--log-file", help="Log dosyası adı")] = None,
) -> None:
    """Kategori çek → filtrele → ürünleri çek → standardize → fiyat diff → veri setine ekle."""
    settings = _settings(store)
    setup_logging(settings.log_dir, settings.log_level, log_file or f"{settings.store}.log")
    result = asyncio.run(run_scrape(settings))
    typer.echo(
        f"{settings.store}: {result.rows_written} yeni kayıt "
        f"({result.products_scraped} ürün / {result.categories_scraped} kategori)"
    )


@app.command()
def categories(
    store: Annotated[str, typer.Argument(help="bkm veya kitapyurdu")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Gösterilecek kategori sayısı")] = 100,
) -> None:
    """Mağazadan kategorileri çekip listeler (ignore kuralları hariç)."""
    settings = _settings(store)
    setup_logging(settings.log_dir, settings.log_level, f"{settings.store}-categories.log")

    async def _list() -> None:
        from bookdata.adapters.http import AsyncHTTPClient

        async with AsyncHTTPClient(settings) as http:
            adapter_cls = get_store_class(settings)
            store = adapter_cls(http, settings)
            cats = await store.fetch_categories()
        from bookdata.pipeline.filter import apply_ignore

        kept = apply_ignore(cats, settings.load_ignore_patterns())
        for c in kept[:limit]:
            typer.echo(f"{c.name}\t{c.url}")

    asyncio.run(_list())


@app.command()
def publish(
    store: Annotated[str, typer.Argument(help="bkm veya kitapyurdu")],
) -> None:
    """Veri setini Kaggle'a yükler (BOOKDATA_KAGGLE_DATASET ENV'den okunur)."""
    settings = _settings(store)
    setup_logging(settings.log_dir, settings.log_level, f"{settings.store}.log")

    from bookdata.adapters.kaggle import KagglePublisher

    publisher = KagglePublisher(settings.kaggle_dataset)
    if not publisher.can_publish():
        typer.echo("BOOKDATA_KAGGLE_DATASET ayarlanmamış; yayın atlandı.", err=True)
        raise typer.Exit(code=1)
    from datetime import date

    publisher.publish(settings.dataset_file, settings.store, str(date.today()))


@app.command()
def report(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", "-o", help="HTML çıktı yolu (varsayılan: Report/dashboard_{tarih}.html)"
        ),
    ] = None,
) -> None:
    """Tüm veri setlerinden interaktif fiyat dashboard'u üretir (plotly gerektirir)."""
    settings = _settings()
    setup_logging(settings.log_dir, settings.log_level, "report.log")

    try:
        import plotly  # noqa: F401
    except ImportError:
        plotly_available = False
    else:
        plotly_available = True

    if not plotly_available:
        typer.echo("Dashboard için plotly gerekli: `uv sync --extra report`", err=True)
        raise typer.Exit(code=1)

    from datetime import date

    from bookdata.analyze import load_datasets
    from bookdata.dashboard import save_dashboard

    df = load_datasets(settings.data_dir)
    if df.empty:
        typer.echo("Veri seti bulunamadı veya boş.", err=True)
        raise typer.Exit(code=1)

    out = output or settings.data_dir.parent / "Report" / f"dashboard_{date.today():%Y%m%d}.html"
    save_dashboard(df, out)
    typer.echo(f"Dashboard oluşturuldu: {out}")


@app.command()
def stores() -> None:
    """Kayıtlı mağaza adapter'larını listeler."""
    typer.echo("bkm          → BKM Kitap")
    typer.echo("kitapyurdu   → Kitap Yurdu")


if __name__ == "__main__":
    app()
