"""Тесты перевода заголовков: без реальных HTTP-запросов."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import translate as translate_module  # noqa: E402
from translate import (  # noqa: E402
    already_russian,
    is_acceptable_translation,
    parse_google_dict_translation,
    parse_google_translation,
    parse_mymemory_translation,
    translate_article_titles,
)


def test_parse_google_translation_joins_chunks() -> None:
    """Парсер Google gtx склеивает куски перевода."""
    payload: object = [[["Привет, ", "Hello, "], ["мир", "world"]]]
    assert parse_google_translation(payload) == "Привет, мир"


def test_already_russian_detects_cyrillic() -> None:
    """Кириллица в заголовке не отправляется в переводчик."""
    assert already_russian("Статья 101") is True
    assert already_russian("OpenLogi") is False


def test_mymemory_quota_message_ignored() -> None:
    """Предупреждение MyMemory о квоте не считается переводом."""
    payload: object = {"responseData": {"translatedText": "MYMEMORY WARNING: quota"}}
    assert parse_mymemory_translation(payload) is None


def test_is_acceptable_translation_rejects_unchanged_english() -> None:
    """Оригинал без кириллицы не принимается как перевод."""
    assert is_acceptable_translation("Omakase Computing", "Omakase Computing") is False
    assert is_acceptable_translation("Hello", "Привет") is True


def test_parse_google_dict_translation_reads_string_list() -> None:
    """Парсер dict-chrome-ex читает первую строку ответа."""
    assert parse_google_dict_translation(["Омакасе Компьютинг"]) == "Омакасе Компьютинг"


def test_english_titles_are_translated() -> None:
    """Английский title заменяется русским из мока Google."""

    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host or ""
        if "translate.googleapis.com" in host:
            return httpx.Response(200, json=[[["Привет мир", "Hello world"]]])
        if "clients5.google.com" in host:
            return httpx.Response(200, json=["Привет мир"])
        return httpx.Response(404, json={"error": "not found"})

    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    def factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return real_async_client(*args, **kwargs)

    articles: list[dict[str, str | int]] = [
        {"id": 101, "title": "Hello world", "url": "https://example.com/101"},
    ]
    translate_module._title_ru_cache.clear()
    with patch("translate.httpx.AsyncClient", side_effect=factory):
        result = asyncio.run(translate_article_titles(articles))

    assert result[0]["id"] == 101
    assert result[0]["url"] == "https://example.com/101"
    assert result[0]["title"] == "Привет мир"
