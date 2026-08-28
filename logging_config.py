"""Базовая настройка логирования: консоль и файл."""

import logging
import re
from pathlib import Path

LOG_FILE: Path = Path(__file__).resolve().parent / "app.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
ACCESS_LOGGER_NAME = "neonshadow.access"
_ACCESS_ERROR_RE = re.compile(r'" (4\d\d|5\d\d) ')

_configured = False


class ConsoleQuietFilter(logging.Filter):
    """Пропускает в консоль только старт, API-запросы и предупреждения/ошибки."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            return True
        if record.levelno < logging.INFO:
            return False
        if record.name == "__main__":
            return True
        if record.name != ACCESS_LOGGER_NAME:
            return True
        message = record.getMessage()
        if "/api/" in message:
            return True
        return _ACCESS_ERROR_RE.search(message) is not None


def setup_logging(level: int = logging.INFO) -> None:
    """Вешает на корневой логгер обработчики: stderr и app.log.

    В консоль попадают старт сервера, запросы к /api/ и ошибки HTTP;
    полный access-лог пишется только в app.log.
    Повторные вызовы не дублируют обработчики.
    """
    global _configured
    if _configured:
        return

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ConsoleQuietFilter())

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    _configured = True
