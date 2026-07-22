"""Logging bootstrap for Alarmcast."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from alarmcast.core.config import get_config_dir

_LOG_FORMAT = "%(levelname)s %(name)s: %(message)s"
_FILE_MAX_BYTES = 512_000
_FILE_BACKUP_COUNT = 3


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once for the process."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        return

    logging.basicConfig(level=level, format=_LOG_FORMAT)
    _add_file_handler(root_logger, level)


def _add_file_handler(root_logger: logging.Logger, level: int) -> None:
    log_path = get_config_dir() / "alarmcast.log"
    try:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=_FILE_MAX_BYTES,
            backupCount=_FILE_BACKUP_COUNT,
            encoding="utf-8",
        )
    except OSError:
        return
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root_logger.addHandler(handler)
