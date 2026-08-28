"""Асинхронный клиент Hacker News через httpx."""

import asyncio
from urllib.parse import urlparse

import httpx

TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL_TEMPLATE = "https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
HN_DISCUSSION_URL = "https://news.ycombinator.com/item?id={story_id}"
DEFAULT_LIMIT = 5
REQUEST_TIMEOUT_SEC = 10.0


class NewsApiError(Exception):
    """Ошибка запроса или разбора ответа Hacker News."""


def _parse_story_ids(payload: object, limit: int) -> list[int]:
    """Проверяет JSON и возвращает первые limit идентификаторов."""
    if not isinstance(payload, list):
        raise NewsApiError("Ожидался JSON-массив идентификаторов")

    story_ids: list[int] = []
    for item in payload[:limit]:
        if not isinstance(item, int) or isinstance(item, bool):
            raise NewsApiError("Идентификатор статьи должен быть целым числом")
        story_ids.append(item)
    return story_ids


def _item_url(story_id: int) -> str:
    return ITEM_URL_TEMPLATE.format(story_id=story_id)


def _discussion_url(story_id: int) -> str:
    return HN_DISCUSSION_URL.format(story_id=story_id)


def is_http_url(url: str) -> bool:
    """True, если URL с схемой http/https и непустым хостом."""
    parsed = urlparse(url.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _parse_article(payload: object, story_id: int) -> dict[str, str | int] | None:
    """Достаёт заголовок и ссылку; пропускает удалённые записи."""
    if not isinstance(payload, dict):
        return None
    if payload.get("deleted") or payload.get("dead"):
        return None
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return None

    raw_url = payload.get("url")
    if isinstance(raw_url, str) and is_http_url(raw_url):
        url = raw_url.strip()
    else:
        url = _discussion_url(story_id)

    return {"id": story_id, "title": title.strip(), "url": url}


async def _request_json(client: httpx.AsyncClient, url: str) -> object:
    """GET JSON с обработкой сетевых и HTTP-ошибок."""
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException as exc:
        raise NewsApiError("Истекло время ожидания Hacker News") from exc
    except httpx.HTTPStatusError as extra:
        raise NewsApiError("Hacker News вернул ошибку HTTP") from extra
    except httpx.RequestError as extra:
        raise NewsApiError("Сетевая ошибка при запросе к Hacker News") from extra
    except ValueError as extra:
        raise NewsApiError("Некорректный JSON от Hacker News") from extra


async def fetch_top_story_ids(
    limit: int = DEFAULT_LIMIT,
    client: httpx.AsyncClient | None = None,
) -> list[int]:
    """Делает GET к topstories.json и возвращает список ID статей."""
    if limit < 1:
        raise ValueError("limit должен быть положительным")

    async def _load(active_client: httpx.AsyncClient) -> list[int]:
        payload = await _request_json(active_client, TOP_STORIES_URL)
        return _parse_story_ids(payload, limit)

    if client is not None:
        return await _load(client)

    timeout = httpx.Timeout(REQUEST_TIMEOUT_SEC)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as owned:
        return await _load(owned)


async def fetch_story_item(
    story_id: int,
    client: httpx.AsyncClient,
) -> dict[str, str | int] | None:
    """Загружает одну статью: GET /v0/item/{id}.json."""
    payload = await _request_json(client, _item_url(story_id))
    return _parse_article(payload, story_id)


async def fetch_top_articles(limit: int = DEFAULT_LIMIT) -> list[dict[str, str | int]]:
    """Возвращает заголовки и ссылки последних статей Hacker News."""
    timeout = httpx.Timeout(REQUEST_TIMEOUT_SEC)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        story_ids = await fetch_top_story_ids(limit, client=client)
        items = await asyncio.gather(
            *[fetch_story_item(story_id, client) for story_id in story_ids]
        )
    return [item for item in items if item is not None]
