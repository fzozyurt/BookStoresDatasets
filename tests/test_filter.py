from pathlib import Path

from bookdata.config import Settings
from bookdata.models import Category
from bookdata.pipeline.filter import apply_ignore


def test_ignore_by_name():
    cats = [Category(name="Roman Kitapları", url="/roman"), Category(name="Hobi", url="/hobi")]
    kept = apply_ignore(cats, ["hobi"])
    assert [c.name for c in kept] == ["Roman Kitapları"]


def test_ignore_empty_patterns_keeps_all():
    cats = [Category(name="Hobi", url="/hobi")]
    assert apply_ignore(cats, []) == cats


def test_ignore_is_case_insensitive():
    cats = [Category(name="KIRTASIYE", url="/kirtasiye")]
    assert apply_ignore(cats, ["kırtasiye"]) == []


def test_ignore_file_covers_skip_keywords():
    keywords = [
        "Kırtasiye",
        "Hobi",
        "Aksesuar",
        "Puzzle",
        "Oyuncak",
        "Oyun",
        "Süpriz",
        "CD",
        "Müzik",
        "Film",
    ]
    cats = [Category(name=f"{k} Kitapları", url="/kategori") for k in keywords]
    repo_root = Path(__file__).resolve().parents[1]
    patterns = Settings(ignore_file=repo_root / "ignore_categories.txt").load_ignore_patterns()
    assert apply_ignore(cats, patterns) == []
