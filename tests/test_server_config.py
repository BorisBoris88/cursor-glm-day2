"""Тесты настроек запуска сервера из переменных окружения."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server_config import DEFAULT_HOST, DEFAULT_PORT, server_host, server_port  # noqa: E402


def test_server_host_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Без HOST используется 0.0.0.0."""
    monkeypatch.delenv("HOST", raising=False)
    assert server_host() == DEFAULT_HOST
    assert server_host() == "0.0.0.0"


def test_server_host_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """HOST читается из окружения."""
    monkeypatch.setenv("HOST", "127.0.0.1")
    assert server_host() == "127.0.0.1"


def test_server_port_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Без PORT используется 8080."""
    monkeypatch.delenv("PORT", raising=False)
    assert server_port() == DEFAULT_PORT


def test_server_port_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """PORT читается из окружения (как на Render)."""
    monkeypatch.setenv("PORT", "10000")
    assert server_port() == 10000


def test_server_port_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Некорректный PORT вызывает ValueError."""
    monkeypatch.setenv("PORT", "not-a-port")
    with pytest.raises(ValueError, match="Некорректное значение PORT"):
        server_port()


def test_server_port_out_of_range(monkeypatch: pytest.MonkeyPatch) -> None:
    """PORT вне диапазона вызывает ValueError."""
    monkeypatch.setenv("PORT", "70000")
    with pytest.raises(ValueError, match="PORT вне диапазона"):
        server_port()
