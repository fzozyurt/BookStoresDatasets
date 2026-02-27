import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging(
    log_file=None,
    log_format="%(asctime)s - %(levelname)s - %(message)s",
    log_level=None,
    log_dir=None,
    max_bytes=None,
    backup_count=None,
    console_level=None,
):
    """
    Central logging setup.
    Uses rotating file handler and avoids duplicate handlers.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    log_dir = log_dir or os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = log_file or os.getenv("LOG_FILE", "app.log")
    log_path = os.path.join(log_dir, log_file)

    log_level = (log_level or os.getenv("LOG_LEVEL", "WARNING")).upper()
    max_bytes = int(max_bytes or os.getenv("LOG_MAX_BYTES", "5242880"))  # 5MB
    backup_count = int(backup_count or os.getenv("LOG_BACKUP_COUNT", "3"))
    console_level = (console_level or os.getenv("CONSOLE_LOG_LEVEL", "INFO")).upper()

    root_logger.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, log_level, logging.WARNING))

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(getattr(logging, console_level, logging.INFO))

    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
