"""Перевод заголовков на русский: Google gtx, dict-chrome-ex, MyMemory."""

import asyncio
import re

import httpx

GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
GOOGLE_DICT_TRANSLATE_URL = "https://clients5.google.com/translate_a/t"
MYMEMORY_TRANSLATE_URL = "https://api.mymemory.translated.net/get"
REQUEST_TIMEOUT_SEC = 10.0
TRANSLATION_RETRIES = 3
TRANSLATION_RETRY_DELAY_SEC = 0.6
TRANSLATION_INTER_TITLE_DELAY_SEC = 0.35
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
_title_ru_cache: dict[str, str] = {}


def already_russian(text: str) -> bool:
    """Считает заголовок русским, если в нём есть кириллица."""
    return _CYRILLIC_RE.search(text) is not None


def is_acceptable_translation(original: str, translated: str | None) -> bool:
    """Перевод принят, если в нём есть кириллица и он не пустой."""
    if not translated:
        return False
    cleaned = translated.strip()
    if not cleaned:
        return False
    if not already_russian(cleaned):
        return False
    return cleaned.casefold() != original.strip().casefold() or already_russian(original)


def parse_google_translation(payload: object) -> str | None:
    """Разбирает ответ translate.googleapis.com (client=gtx)."""
    if not isinstance(payload, list) or not payload:
        return None
    chunks = payload[0]
    if not isinstance(chunks, list):
        return None
    parts: list[str] = []
    for chunk in chunks:
        if isinstance(chunk, list) and chunk and isinstance(chunk[0], str):
            parts.append(chunk[0])
    text = "".join(parts).strip()
    return text or None


def parse_google_dict_translation(payload: object) -> str | None:
    """Разбирает ответ clients5.google.com/translate_a/t (dict-chrome-ex)."""
    if isinstance(payload, list) and payload and isinstance(payload[0], str):
        text = payload[0].strip()
        return text or None
    return None


def parse_mymemory_translation(payload: object) -> str | None:
    """Разбирает ответ MyMemory; отбрасывает сообщения о квоте."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("responseData")
    if not isinstance(data, dict):
        return None
    text = data.get("translatedText")
    if not isinstance(text, str):
        return None
    cleaned = text.strip()
    if not cleaned or cleaned.upper().startswith("MYMEMORY"):
        return None
    return cleaned


async def _google_gtx_translate(client: httpx.AsyncClient, title: str) -> str | None:
    """Перевод через translate.googleapis.com (client=gtx)."""
    try:
        response = await client.get(
            GOOGLE_TRANSLATE_URL,
            params={"client": "gtx", "sl": "auto", "tl": "ru", "dt": "t", "q": title},
        )
        if response.status_code == 429:
            return None
        response.raise_for_status()
        return parse_google_translation(response.json())
    except (httpx.HTTPError, ValueError):
        return None


async def _google_dict_translate(client: httpx.AsyncClient, title: str) -> str | None:
    """Запасной Google-перевод через dict-chrome-ex (устойчивее к 429)."""
    try:
        response = await client.get(
            GOOGLE_DICT_TRANSLATE_URL,
            params={"client": "dict-chrome-ex", "sl": "en", "tl": "ru", "q": title},
        )
        if response.status_code == 429:
            return None
        response.raise_for_status()
        return parse_google_dict_translation(response.json())
    except (httpx.HTTPError, ValueError):
        return None


async def _mymemory_translate(client: httpx.AsyncClient, title: str) -> str | None:
    """Перевод через MyMemory."""
    try:
        response = await client.get(
            MYMEMORY_TRANSLATE_URL,
            params={"q": title, "langpair": "en|ru"},
        )
        response.raise_for_status()
        return parse_mymemory_translation(response.json())
    except (httpx.HTTPError, ValueError):
        return None


async def _translate_with_providers(client: httpx.AsyncClient, title: str) -> str | None:
    """Пробует все провайдеры по очереди."""
    for provider in (_google_gtx_translate, _google_dict_translate, _mymemory_translate):
        translated = await provider(client, title)
        if is_acceptable_translation(title, translated):
            return translated.strip()
    return None


async def translate_title(client: httpx.AsyncClient, title: str) -> str:
    """Переводит заголовок на русский; при сбое оставляет оригинал."""
    if already_russian(title):
        return title

    cached = _title_ru_cache.get(title)
    if cached is not None:
        return cached

    translated: str | None = None
    for attempt in range(TRANSLATION_RETRIES):
        if attempt > 0:
            await asyncio.sleep(TRANSLATION_RETRY_DELAY_SEC * attempt)
        translated = await _translate_with_providers(client, title)
        if translated is not None:
            break

    result = translated if translated is not None else title
    if translated is not None:
        _title_ru_cache[title] = result
    return result


async def translate_article_titles(
    articles: list[dict[str, str | int]],
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, str | int]]:
    """Копирует статьи с переведёнными title; id и url не меняет."""

    async def _run(active_client: httpx.AsyncClient) -> list[dict[str, str | int]]:
        translated_articles: list[dict[str, str | int]] = []
        for article in articles:
            title_ru = await translate_title(active_client, str(article["title"]))
            translated_articles.append(
                {"id": article["id"], "title": title_ru, "url": article["url"]}
            )
            await asyncio.sleep(TRANSLATION_INTER_TITLE_DELAY_SEC)
        return translated_articles

    if client is not None:
        return await _run(client)

    timeout = httpx.Timeout(REQUEST_TIMEOUT_SEC)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as owned:
        return await _run(owned)
