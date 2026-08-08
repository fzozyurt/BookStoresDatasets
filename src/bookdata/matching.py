"""Mağazalar arası kitap eşleştirme motoru (LLM'siz, fuzzy matching).

Akış (identifier-first):
    1. ISBN varsa ve eşitse  → MATCH  (deterministic)
    2. ISBN yoksa:
         a. Yayınevi (Brand) normalize edilip eşleşirse aynı aday havuzu
         b. Başlık (Model) fuzzy benzerliği + yazar (fuzzy) onayı
         c. 0.95+  → MATCH
           0.75+  → REVIEW
           aksi   → DIFFERENT
         d. Aynı başlık ama farklı yayınevi → baskı varyantı → REVIEW

Yazar da fuzzy katılır: isimler mağazalar arasında farklı yazılabilir
("Rowling, J.K." vs "J. K. Rowling", "Doç. Dr." önekleri, yazım farkları).

Eşikler `bookdata match --match-threshold` / `--review-threshold` / env ile
ayarlanabilir (varsayılanlar 0.95 / 0.75 / 0.85).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

import pandas as pd
from rapidfuzz import fuzz

MATCH_THRESHOLD = 0.95
REVIEW_THRESHOLD = 0.75
AUTHOR_MATCH_THRESHOLD = 0.85

_WS = re.compile(r"\s+")


def _ascii_fold(text: str) -> str:
    """Türkçe karakterleri ve aksanları söker: Ş→s, Ğ→g, ı→i, ü→u …"""
    decomposed = unicodedata.normalize("NFKD", text)
    folded = "".join(c for c in decomposed if not unicodedata.combining(c))
    return folded.lower()


def normalize_text(text: object) -> str:
    """ASCII-katlamalı, noktalama temizli yapılmış, tek-boşluklu normalize metin."""
    cleaned = re.sub(r"[^a-z0-9]+", " ", _ascii_fold(str(text or "")))
    return _WS.sub(" ", cleaned).strip()


def isbn_key(text: object) -> str:
    """ISBN'i karşılaştırılabilir anahtara çevirir (rakamlar + sonda X)."""
    value = str(text or "").strip().upper()
    digits = re.sub(r"[^0-9X]", "", value)
    return digits if len(digits) >= 10 else ""


def title_similarity(left: object, right: object) -> float:
    """Başlık benzerliği 0–1: WRatio (alt-başlık/ek ibareleri MATCH bandına itmez)."""
    a, b = normalize_text(left), normalize_text(right)
    if not a or not b:
        return 0.0
    return fuzz.WRatio(a, b) / 100.0


def author_similarity(left: object, right: object) -> float | None:
    """Yazar benzerliği 0–1; iki taraftan biri boşsa None (ceza uygulanmaz).

    WRatio + token_sort: ad/soyad sıralaması ve yazım farklarını tolere eder.
    """
    a, b = normalize_text(left), normalize_text(right)
    if not a or not b:
        return None
    return max(fuzz.WRatio(a, b), fuzz.token_sort_ratio(a, b)) / 100.0


class Confidence(StrEnum):
    MATCH = "MATCH"
    REVIEW = "REVIEW"
    DIFFERENT = "DIFFERENT"


@dataclass(frozen=True)
class MatchDecision:
    """İki liste arasında verilen eşleştirme kararı (MATCH veya REVIEW)."""

    left: dict
    right: dict
    method: str  # "isbn" | "title" | "title-variant"
    score: float
    confidence: Confidence
    author_score: float | None = None


@dataclass
class MatchGroup:
    """Bağlantılı bileşen: aynı kitaba ait liste kümesi."""

    urls: list[str]
    title: str
    isbn: str
    method: str
    confidence: Confidence

    @property
    def stores(self) -> set[str]:
        return {d.get("Site", "") for d in self._members}

    _members: list[dict] = field(default_factory=list, init=False, repr=False)


@dataclass
class MatchResult:
    decisions: list[MatchDecision]
    groups: list[MatchGroup]
    different_count: int = 0

    @property
    def matched(self) -> list[MatchDecision]:
        return [d for d in self.decisions if d.confidence is Confidence.MATCH]

    @property
    def review(self) -> list[MatchDecision]:
        return [d for d in self.decisions if d.confidence is Confidence.REVIEW]


def decide_pair(
    left: dict,
    right: dict,
    *,
    publisher_equal: bool,
    match_threshold: float = MATCH_THRESHOLD,
    review_threshold: float = REVIEW_THRESHOLD,
    author_match_threshold: float = AUTHOR_MATCH_THRESHOLD,
) -> MatchDecision | None:
    """İki ürün satırı arasındaki kararı üretir; yeterince benzer değilse None (DIFFERENT)."""
    isbn_l, isbn_r = isbn_key(left.get("ISBN")), isbn_key(right.get("ISBN"))
    if isbn_l and isbn_r and isbn_l == isbn_r:
        return MatchDecision(left, right, method="isbn", score=1.0, confidence=Confidence.MATCH)

    score = title_similarity(left.get("Kitap İsmi"), right.get("Kitap İsmi"))
    author = author_similarity(left.get("Yazar"), right.get("Yazar"))

    if publisher_equal:
        if score >= match_threshold:
            if author is not None and author < author_match_threshold:
                return MatchDecision(
                    left, right, "title", score, Confidence.REVIEW, author_score=author
                )
            return MatchDecision(left, right, "title", score, Confidence.MATCH, author_score=author)
        if score >= review_threshold:
            return MatchDecision(
                left, right, "title", score, Confidence.REVIEW, author_score=author
            )
        return None  # DIFFERENT

    # Yayınevi farklı/eksik → baskı varyantı: yalnızca başlık çok benzer VE yazar onaylıyorsa
    if score >= match_threshold and author is not None and author >= author_match_threshold:
        return MatchDecision(
            left, right, "title-variant", score, Confidence.REVIEW, author_score=author
        )
    return None


class _UnionFind:
    def __init__(self, size: int) -> None:
        self._parent = list(range(size))

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[rb] = ra


def match_products(
    products: Iterable[dict],
    *,
    match_threshold: float = MATCH_THRESHOLD,
    review_threshold: float = REVIEW_THRESHOLD,
    author_match_threshold: float = AUTHOR_MATCH_THRESHOLD,
) -> MatchResult:
    """Listeleri eşleştirir: ISBN → yayınevi havuzu → başlık+yazar fuzzy.

    Aday tespiti O(n): ISBN indeksi, yayınevi havuzu ve normalize başlık indeksi
    üzerinden; yalnızca aynı gruptakiler karşılaştırılır (O(n²) karşılaştırma yok).
    """
    rows = list(products)
    seen: set[tuple[int, int]] = set()
    decisions: list[MatchDecision] = []
    different = 0

    def consider(i: int, j: int, publisher_equal: bool) -> None:
        nonlocal different
        key = (i, j) if i < j else (j, i)
        if key in seen:
            return
        seen.add(key)
        decision = decide_pair(
            rows[i],
            rows[j],
            publisher_equal=publisher_equal,
            match_threshold=match_threshold,
            review_threshold=review_threshold,
            author_match_threshold=author_match_threshold,
        )
        if decision is None:
            different += 1
        else:
            decisions.append(decision)

    # 1) ISBN indeksi
    isbn_index: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        key = isbn_key(row.get("ISBN"))
        if key:
            isbn_index.setdefault(key, []).append(i)
    for indices in isbn_index.values():
        for k in range(len(indices)):
            for j in range(k + 1, len(indices)):
                consider(indices[k], indices[j], publisher_equal=False)

    # 2) Yayınevi (Brand) havuzu → başlık+yazar fuzzy
    pub_index: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        pub = normalize_text(row.get("Yayınevi"))
        if pub:
            pub_index.setdefault(pub, []).append(i)
    for indices in pub_index.values():
        for k in range(len(indices)):
            for j in range(k + 1, len(indices)):
                consider(indices[k], indices[j], publisher_equal=True)

    # 3) Normalize başlık indeksi → farklı yayınevi/baskı varyantları
    title_index: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        title = normalize_text(row.get("Kitap İsmi"))
        if title:
            title_index.setdefault(title, []).append(i)
    for indices in title_index.values():
        for k in range(len(indices)):
            for j in range(k + 1, len(indices)):
                consider(indices[k], indices[j], publisher_equal=False)

    groups = _build_groups(rows, decisions)
    return MatchResult(decisions=decisions, groups=groups, different_count=different)


def _build_groups(rows: list[dict], decisions: list[MatchDecision]) -> list[MatchGroup]:
    if not decisions:
        return []
    index_by_url = {row.get("URL", ""): i for i, row in enumerate(rows)}
    uf = _UnionFind(len(rows))
    for d in decisions:
        li = index_by_url.get(d.left.get("URL", ""))
        ri = index_by_url.get(d.right.get("URL", ""))
        if li is not None and ri is not None:
            uf.union(li, ri)

    clusters: dict[int, list[int]] = {}
    for i in range(len(rows)):
        clusters.setdefault(uf.find(i), []).append(i)

    groups: list[MatchGroup] = []
    for members in clusters.values():
        if len(members) < 2:
            continue
        member_rows = [rows[i] for i in members]
        member_urls = sorted({r.get("URL", "") for r in member_rows})
        edges = [
            d
            for d in decisions
            if d.left.get("URL") in member_urls and d.right.get("URL") in member_urls
        ]
        all_match = all(d.confidence is Confidence.MATCH for d in edges)
        group = MatchGroup(
            urls=member_urls,
            title=max((r.get("Kitap İsmi", "") for r in member_rows), key=len),
            isbn=next((r.get("ISBN", "") for r in member_rows if r.get("ISBN")), ""),
            method="isbn" if any(d.method == "isbn" for d in edges) else edges[0].method,
            confidence=Confidence.MATCH if all_match else Confidence.REVIEW,
        )
        group._members = member_rows
        groups.append(group)
    return groups


def unique_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Her URL için son kaydı bırakır (fiyat geçmişi → güncel liste görünümü)."""
    if df.empty:
        return df
    return df.sort_values("Tarih").drop_duplicates(subset="URL", keep="last").reset_index(drop=True)


def cross_store_prices(products: list[dict], result: MatchResult | None = None) -> pd.DataFrame:
    """MATCH gruplarından mağazalar arası fiyat karşılaştırma DataFrame'i üretir.

    Çıktı uzun formattadır: her (grup, mağaza) satırı için en iyi fiyat.
    """
    result = result or match_products(products)
    rows: list[dict] = []
    for group in result.groups:
        if group.confidence is not Confidence.MATCH or len(group.stores) < 2:
            continue
        best: dict[str, tuple[float, str]] = {}
        for member in group._members:
            url = member.get("URL", "")
            try:
                price = float(member.get("Fiyat"))
            except (TypeError, ValueError):
                continue
            store = str(member.get("Site", ""))
            if store not in best or price < best[store][0]:
                best[store] = (price, url)
        for store, (price, url) in best.items():
            rows.append(
                {
                    "Anahtar": group.isbn or normalize_text(group.title),
                    "Kitap": group.title,
                    "ISBN": group.isbn,
                    "Site": store,
                    "Fiyat": price,
                    "URL": url,
                }
            )
    return pd.DataFrame(rows, columns=["Anahtar", "Kitap", "ISBN", "Site", "Fiyat", "URL"])
