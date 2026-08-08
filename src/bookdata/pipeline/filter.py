"""Kategori filtre aşaması: ignore_categories.txt'teki desenlere uyan kategorileri atlar."""

from __future__ import annotations

import logging
import unicodedata

from bookdata.models import Category

logger = logging.getLogger(__name__)

_TURKISH_TO_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def _normalize(text: str) -> str:
    """Türkçe karakterleri ASCII'ye çevirir ve küçültür (ı↔i eşleşmesi için)."""
    text = text.translate(_TURKISH_TO_ASCII)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def apply_ignore(categories: list[Category], patterns: list[str]) -> list[Category]:
    """Kategori adı veya URL'sinde desen geçenleri (büyük/küçük duyarsız) çıkarır."""
    if not patterns:
        return categories

    normalized_patterns = [_normalize(p) for p in patterns]

    def ignored(category: Category) -> bool:
        haystack = _normalize(f"{category.name} {category.url}")
        return any(pattern in haystack for pattern in normalized_patterns)

    kept = [c for c in categories if not ignored(c)]
    skipped = len(categories) - len(kept)
    if skipped:
        logger.info(
            "Ignore kuralları gereği %s kategori atlandı (%s desen)", skipped, len(patterns)
        )
    return kept
