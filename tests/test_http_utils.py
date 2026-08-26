"""Тесты CORS-origins с учётом PORT и Render."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from http_utils import allowed_origins  # noqa: E402


def test_allowed_origins_includes_render_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """RENDER_EXTERNAL_URL попадает в белый список."""
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setenv(
        "RENDER_EXTERNAL_URL",
        "https://neonshadow.onrender.com/",
    )
    origins = allowed_origins()
    assert "https://neonshadow.onrender.com" in origins


def test_allowed_origins_custom_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """При нестандартном PORT добавляются локальные origin."""
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setenv("PORT", "10000")
    origins = allowed_origins()
    assert "http://localhost:10000" in origins
    assert "http://127.0.0.1:10000" in origins
