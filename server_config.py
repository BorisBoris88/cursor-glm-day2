"""Настройки запуска HTTP-сервера из переменных окружения."""

import os

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080


def server_host() -> str:
    """Адрес привязки: по умолчанию 0.0.0.0 для доступа извне (Docker, Render)."""
    return os.getenv("HOST", DEFAULT_HOST)


def server_port() -> int:
    """Порт HTTP-сервера (Render и другие PaaS задают PORT автоматически)."""
    raw = os.getenv("PORT", "8080")
    try:
        port = int(raw)
    except ValueError as exc:
        raise ValueError(f"Некорректное значение PORT: {raw!r}") from exc
    if port < 1 or port > 65535:
        raise ValueError(f"PORT вне диапазона 1–65535: {port}")
    return port
