"""Кэш GET /api/news: TTL 30 секунд, без реального HTTP."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from news_cache import NEWS_CACHE_TTL_SEC, get_cached_news, news_cache  # noqa: E402

FAKE_ARTICLES: list[dict[str, str | int]] = [
    {"id": 1, "title": "Тест", "url": "https://example.com/1"},
]


@pytest.fixture(autouse=True)
def reset_news_cache() -> None:
    """Сбрасывает глобальный кэш между тестами."""
    news_cache["data"] = None
    news_cache["timestamp"] = 0.0


def test_news_cache_hit_within_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    """Повторный запрос младше 30 секунд не вызывает loader."""
    calls = {"n": 0}

    def loader() -> list[dict[str, str | int]]:
        calls["n"] += 1
        return FAKE_ARTICLES

    monkeypatch.setattr("news_cache.time.time", lambda: 1_000.0)

    first = get_cached_news(loader)
    second = get_cached_news(loader)

    assert calls["n"] == 1
    assert first == FAKE_ARTICLES
    assert second == FAKE_ARTICLES
    assert news_cache["data"] == FAKE_ARTICLES


def test_news_cache_miss_after_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    """После истечения TTL кэш обновляется новым запросом."""
    calls = {"n": 0}

    def loader() -> list[dict[str, str | int]]:
        calls["n"] += 1
        return FAKE_ARTICLES

    clock = {"now": 1_000.0}

    def fake_time() -> float:
        return clock["now"]

    monkeypatch.setattr("news_cache.time.time", fake_time)

    get_cached_news(loader)
    clock["now"] = 1_000.0 + NEWS_CACHE_TTL_SEC
    get_cached_news(loader)

    assert calls["n"] == 2
    assert news_cache["timestamp"] == clock["now"]
