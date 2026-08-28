"""Тесты фильтра консольного логирования."""

import logging

from logging_config import ACCESS_LOGGER_NAME, ConsoleQuietFilter


def _record(name: str, level: int, message: str) -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=level,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_console_filter_hides_static_access_log() -> None:
    """Статика и страницы в консоль не попадают."""
    quiet = ConsoleQuietFilter()
    static = _record(
        ACCESS_LOGGER_NAME,
        logging.INFO,
        '127.0.0.1 - "GET /login HTTP/1.1" 200 -',
    )
    assert quiet.filter(static) is False


def test_console_filter_shows_api_and_errors() -> None:
    """API и HTTP-ошибки остаются в консоли."""
    quiet = ConsoleQuietFilter()
    api = _record(
        ACCESS_LOGGER_NAME,
        logging.INFO,
        '127.0.0.1 - "POST /api/login HTTP/1.1" 401 -',
    )
    error = _record(
        ACCESS_LOGGER_NAME,
        logging.INFO,
        '127.0.0.1 - "GET /missing HTTP/1.1" 404 -',
    )
    warning = _record("__main__", logging.WARNING, "Лимит неудачных входов превышен")
    assert quiet.filter(api) is True
    assert quiet.filter(error) is True
    assert quiet.filter(warning) is True
