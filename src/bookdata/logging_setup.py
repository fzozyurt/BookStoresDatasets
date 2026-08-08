"""Merkezi loglama: yapılandırılmış, tek sefer kurulum, rotasyonlu dosya + console."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"

_logger_configured = False


def setup_logging(log_dir: Path, level: str = "INFO", log_file: str | None = None) -> None:
    """Root logger'ı bir kez yapılandırır (tekrar çağrıldığında no-op)."""
    global _logger_configured
    if _logger_configured:
        return

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, level.upper(), logging.INFO))
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_file:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # Üçüncü taraf kütüphanelerin gürültüsünü bastır
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _logger_configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
