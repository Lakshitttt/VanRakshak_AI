"""
Centralized logging configuration for the VanRakshak AI backend.

Configures both console and rotating file logging so that application
behavior is observable locally and in production, without any module
outside this file touching the standard library `logging` module's
global configuration directly.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from app.core.settings import settings

LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """
    Configure the root logger with console and rotating file handlers.

    This should be called exactly once, during application startup (see
    the lifespan handler in app/main.py). Calling it multiple times in
    the same process is safe: it is guarded by checking whether the root
    logger already has handlers attached.
    """
    root_logger = logging.getLogger()

    if root_logger.handlers:
        # Logging has already been configured for this process.
        return

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    os.makedirs(settings.LOG_DIR, exist_ok=True)
    log_file_path = os.path.join(settings.LOG_DIR, settings.LOG_FILE_NAME)

    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB per log file
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    root_logger.info(
        "Logging configured | level=%s | log_file=%s",
        settings.LOG_LEVEL,
        log_file_path,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a module-scoped logger.

    Args:
        name: Typically `__name__` of the calling module, so log lines
            identify which module emitted them.

    Returns:
        A standard library Logger instance that inherits the handlers
        and level configured by `configure_logging`.
    """
    return logging.getLogger(name)