"""Yapılandırma: ortam değişkenleri ve komut satırı üzerinden ayarlanır."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("Data")
    log_dir: Path = Path("logs")
    log_level: str = "INFO"
    ignore_file: Path = Path("ignore_categories.txt")

    concurrency: int = 12
    request_timeout: float = 20.0
    retry_attempts: int = 3
    retry_backoff_base: float = 2.0
    min_request_interval: float = 0.2

    per_category_max_pages: int = 50
    kaggle_dataset: str | None = None

    store: str = "bkm"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            data_dir=Path(os.getenv("BOOKDATA_DATA_DIR", "Data")),
            log_dir=Path(os.getenv("BOOKDATA_LOG_DIR", "logs")),
            log_level=os.getenv("BOOKDATA_LOG_LEVEL", "INFO"),
            ignore_file=Path(os.getenv("BOOKDATA_IGNORE_FILE", "ignore_categories.txt")),
            concurrency=int(os.getenv("BOOKDATA_CONCURRENCY", "12")),
            request_timeout=float(os.getenv("BOOKDATA_TIMEOUT", "20")),
            retry_attempts=int(os.getenv("BOOKDATA_RETRY_ATTEMPTS", "3")),
            min_request_interval=float(os.getenv("BOOKDATA_MIN_INTERVAL", "0.2")),
            per_category_max_pages=int(os.getenv("BOOKDATA_MAX_PAGES", "50")),
            kaggle_dataset=os.getenv("BOOKDATA_KAGGLE_DATASET"),
            store=os.getenv("BOOKDATA_STORE", "bkm"),
        )

    @property
    def dataset_file(self) -> Path:
        return self.data_dir / f"{self.store}_Datasets.csv"

    def load_ignore_patterns(self) -> list[str]:
        """Git'te commit'li ignore dosyasından (her satır bir desen) kuralları okur."""
        if not self.ignore_file.exists():
            return []
        return [
            line.strip()
            for line in self.ignore_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
