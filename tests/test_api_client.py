"""Тесты клиента Hacker News: без реальных HTTP-запросов."""

import asyncio
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_client import (  # noqa: E402
    NewsApiError,
    fetch_top_articles,
    fetch_top_story_ids,
)

FAKE_STORY_IDS = [101, 202, 303, 404, 505, 606]


def _topstories_transport(payload: object, status_code: int = 200) -> httpx.MockTransport:
    """Мок: отвечает только на topstories.json."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/topstories.json"):
            return httpx.Response(status_code, json=payload)
        return httpx.Response(404, json={"error": "not found"})

    return httpx.MockTransport(handler)


def _news_transport() -> httpx.MockTransport:
    """Мок: topstories + карточки item/{id}.json."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/topstories.json"):
            return httpx.Response(200, json=FAKE_STORY_IDS)
        if "/item/" in path and path.endswith(".json"):
            raw_id = path.rsplit("/", 1)[-1].removesuffix(".json")
            story_id = int(raw_id)
            return httpx.Response(
                200,
                json={
                    "id": story_id,
                    "title": f"Статья {story_id}",
                    "url": f"https://example.com/{story_id}",
                },
            )
        return httpx.Response(404, json={"error": "not found"})

    return httpx.MockTransport(handler)


@pytest.fixture
def patched_http_client() -> Iterator[None]:
    """Подменяет AsyncClient так, чтобы httpx не ходил в сеть."""
    transport = _news_transport()
    real_async_client = httpx.AsyncClient

    def factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return real_async_client(*args, **kwargs)

    with patch("api_client.httpx.AsyncClient", side_effect=factory):
        yield


def test_fetch_top_story_ids_returns_non_empty_int_list() -> None:
    """fetch_top_story_ids возвращает непустой список целых ID."""

    async def _run() -> list[int]:
        transport = _topstories_transport(FAKE_STORY_IDS)
        async with httpx.AsyncClient(transport=transport) as client:
            return await fetch_top_story_ids(limit=5, client=client)

    story_ids = asyncio.run(_run())

    assert isinstance(story_ids, list)
    assert story_ids != []
    assert len(story_ids) == 5
    for story_id in story_ids:
        assert type(story_id) is int


def test_fetch_top_articles_uses_mocked_http(patched_http_client: None) -> None:
    """fetch_top_articles собирает заголовки и ссылки из моков item API."""
    articles = asyncio.run(fetch_top_articles())

    assert isinstance(articles, list)
    assert articles != []
    assert len(articles) == 5
    for article in articles:
        assert isinstance(article["id"], int)
        assert type(article["id"]) is int
        assert isinstance(article["title"], str)
        assert isinstance(article["url"], str)


def test_fetch_top_story_ids_http_error() -> None:
    """Сетевой/HTTP сбой превращается в NewsApiError."""

    async def _run() -> list[int]:
        transport = _topstories_transport({"error": "fail"}, status_code=503)
        async with httpx.AsyncClient(transport=transport) as client:
            return await fetch_top_story_ids(client=client)

    with pytest.raises(NewsApiError):
        asyncio.run(_run())
