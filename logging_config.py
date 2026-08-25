"""Базовая настройка логирования: консоль и файл."""

import logging
from pathlib import Path

LOG_FILE: Path = Path(__file__).resolve().parent / "app.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """Вешает на корневой логгер обработчики: stderr и app.log.

    Повторные вызовы не дублируют обработчики.
    """
    global _configured
    if _configured:
        return

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    _configured = True
