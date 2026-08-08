"""Kitap fiyat izleme CLI'sı.

Kullanım (uv):
    uv run bookdata scrape bkm
    uv run bookdata scrape kitapyurdu
    uv run bookdata publish bkm
    uv run bookdata categories bkm
    uv run bookdata inspect <url>
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Annotated

import httpx
import typer

from bookdata.config import Settings
from bookdata.logging_setup import get_logger, setup_logging
from bookdata.pipeline import STORE_REGISTRY, get_store_class, resolve_adapter, run_scrape

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
def inspect(
    url: Annotated[str, typer.Argument(help="İncelenecek URL (ürün/kategori sayfası)")],
) -> None:
    """Bir URL'yi analiz eder: adapter, HTTP durumu, JSON-LD ve ürün alanları."""

    async def _run() -> None:
        from bs4 import BeautifulSoup

        from bookdata.adapters.http import AsyncHTTPClient
        from bookdata.errors import FetchError
        from bookdata.pipeline.extract import parse_json_ld, products_from_json_ld

        adapter_cls = resolve_adapter(url)
        typer.echo(f"Domain: {httpx.URL(url).host}")
        typer.echo(f"Adapter: {adapter_cls.__name__ if adapter_cls else 'kayıtlı değil'}")
        typer.echo("Fetch stratejisi: HTTP")

        settings = _settings()
        async with AsyncHTTPClient(settings) as http:
            try:
                response = await http.get(url)
            except FetchError as exc:
                typer.echo(f"Durum: hata → {type(exc).__name__} ({exc})", err=True)
                raise typer.Exit(code=1) from exc
        typer.echo(f"Durum: {response.status_code}")

        soup = BeautifulSoup(response.content, "html.parser")
        blocks = parse_json_ld(soup)
        products = products_from_json_ld(soup, "?")
        typer.echo(f"JSON-LD: {len(blocks)} blok, {len(products)} ürün içeriyor")
        if products:
            first = products[0]
            typer.echo("Algılanan alanlar:")
            for key in ("title", "price", "currency", "availability", "isbn"):
                value = first.get(key)
                if value:
                    typer.echo(f"  {key}: {value}")
        else:
            typer.echo("Ürün alanı bulunamadı: bu sayfa JSON-LD ürün içermiyor.")

    asyncio.run(_run())


@app.command()
def match(
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="REVIEW eşleşmelerinin yazılacağı CSV yolu"),
    ] = None,
    match_threshold: Annotated[
        float, typer.Option("--match-threshold", help="MATCH bandı (varsayılan 0.95)")
    ] = 0.95,
    review_threshold: Annotated[
        float, typer.Option("--review-threshold", help="REVIEW bandı (varsayılan 0.75)")
    ] = 0.75,
) -> None:
    """Mağazalar arası aynı kitabı eşleştirir; REVIEW satırlarını CSV'ye yazar.

    Akış: ISBN → yayınevi havuzu → başlık+yazar fuzzy → MATCH/REVIEW/DIFFERENT.
    REVIEW satırları manuel karar için dışa aktarılır.
    """
    settings = _settings()
    setup_logging(settings.log_dir, settings.log_level, "match.log")

    import pandas as pd

    from bookdata.analyze import load_datasets
    from bookdata.matching import match_products, unique_listings

    df = load_datasets(settings.data_dir)
    if df.empty:
        typer.echo("Veri seti bulunamadı veya boş.", err=True)
        raise typer.Exit(code=1)

    listings = unique_listings(df)
    result = match_products(
        listings.to_dict("records"),
        match_threshold=match_threshold,
        review_threshold=review_threshold,
    )

    typer.echo(
        f"{len(listings)} liste · {len(result.decisions)} karar "
        f"({len(result.matched)} MATCH / {len(result.review)} REVIEW / "
        f"{result.different_count} DIFFERENT) · {len(result.groups)} grup"
    )

    if not result.review:
        typer.echo("İncelenecek (REVIEW) eşleşme yok.")
        return

    review_df = pd.DataFrame(
        [
            {
                "Sol Kitap": d.left.get("Kitap İsmi", ""),
                "Sol Yazar": d.left.get("Yazar", ""),
                "Sol Yayınevi": d.left.get("Yayınevi", ""),
                "Sol Site": d.left.get("Site", ""),
                "Sol URL": d.left.get("URL", ""),
                "Sağ Kitap": d.right.get("Kitap İsmi", ""),
                "Sağ Yazar": d.right.get("Yazar", ""),
                "Sağ Yayınevi": d.right.get("Yayınevi", ""),
                "Sağ Site": d.right.get("Site", ""),
                "Sağ URL": d.right.get("URL", ""),
                "Yöntem": d.method,
                "Skor": round(d.score, 3),
                "Yazar Skoru": round(d.author_score, 3) if d.author_score is not None else "",
                "Güven": d.confidence.value,
            }
            for d in result.review
        ]
    )
    out = output or settings.data_dir.parent / "Match" / f"review_{date.today():%Y%m%d}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    review_df.to_csv(out, index=False)
    typer.echo(f"İnceleme dosyası: {out} ({len(review_df)} satır)")


@app.command()
def stores() -> None:
    """Kayıtlı mağaza adapter'larını listeler."""
    for key, adapter_cls in STORE_REGISTRY.items():
        typer.echo(f"{key:<12} → {adapter_cls.display_name}")


if __name__ == "__main__":
    app()
