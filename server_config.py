"""Настройки запуска HTTP-сервера из переменных окружения."""

import os

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8080


def server_host() -> str:
    """Адрес привязки: localhost для разработки, 0.0.0.0 для контейнера."""
    return os.environ.get("HOST", DEFAULT_HOST)


def server_port() -> int:
    """Порт HTTP-сервера (Render задаёт PORT автоматически)."""
    raw = os.environ.get("PORT", str(DEFAULT_PORT))
    try:
        port = int(raw)
    except ValueError as exc:
        raise ValueError(f"Некорректное значение PORT: {raw!r}") from exc
    if port < 1 or port > 65535:
        raise ValueError(f"PORT вне диапазона 1–65535: {port}")
    return port
