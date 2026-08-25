"""Тесты вынесенных хелперов сервера: без поднятия HTTPServer."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auth import (  # noqa: E402
    build_session_cookies,
    get_session_username,
    has_session_cookie,
    is_login_get_path,
    is_protected_page,
    is_public_static_path,
    requires_session,
)
from bot_replies import reply_for  # noqa: E402
from http_utils import is_forbidden_static  # noqa: E402
from rate_limit import POST_MAX_PER_WINDOW, allow_post  # noqa: E402
import rate_limit as rate_limit_module  # noqa: E402


def test_forbidden_static_blocks_sqlite_files() -> None:
    """База из корня не должна раздаваться как статика."""
    assert is_forbidden_static("/hackathon.db") is True
    assert is_forbidden_static("/data/chat.sqlite?x=1") is True
    assert is_forbidden_static("/css/style.css") is False
    assert is_forbidden_static("/api/messages") is False


def test_bot_reply_only_on_trigger() -> None:
    """Бот отвечает только если в тексте есть neo."""
    assert reply_for("привет") is None
    phrase = reply_for("Привет, Neo!")
    assert isinstance(phrase, str)
    assert phrase != ""


def test_has_session_cookie_detects_logged_in_cookie() -> None:
    """Сессионная кука распознаётся в заголовке Cookie."""

    class FakeHandler:
        headers = {"Cookie": "theme=dark; session=logged_in; lang=ru"}

    assert has_session_cookie(FakeHandler()) is True


def test_has_session_cookie_missing_without_cookie() -> None:
    """Без session=logged_in доступ не считается авторизованным."""

    class FakeHandler:
        headers: dict[str, str] = {}

    assert has_session_cookie(FakeHandler()) is False


def test_is_login_get_path_matches_login_routes() -> None:
    """Публичные маршруты входа — /login и /login.html."""
    assert is_login_get_path("/login") is True
    assert is_login_get_path("/login?retry=1") is True
    assert is_login_get_path("/login.html") is True
    assert is_login_get_path("/index.html") is False


def test_is_public_static_path_allows_assets() -> None:
    """Статика css/js доступна без сессии."""
    assert is_public_static_path("/css/style.css") is True
    assert is_public_static_path("/js/weather.js?v=widgets") is True
    assert is_public_static_path("/api/weather") is False


def test_requires_session_for_pages_and_api() -> None:
    """Страницы и API требуют сессию, вход и статика — нет."""
    assert requires_session("/index.html") is True
    assert requires_session("/api/news") is True
    assert requires_session("/login.html") is False
    assert requires_session("/js/chat.js") is False


def test_is_protected_page_matches_site_pages() -> None:
    """Защищённые HTML-страницы перенаправляются на вход."""
    assert is_protected_page("/") is True
    assert is_protected_page("/index.html") is True
    assert is_protected_page("/login.html") is False


def test_get_session_username_reads_auth_user_cookie() -> None:
    """Логин берётся из куки auth_user при активной сессии."""

    class FakeHandler:
        headers = {
            "Cookie": "session=logged_in; auth_user=neo",
        }

    assert get_session_username(FakeHandler()) == "neo"


def test_get_session_username_requires_session() -> None:
    """Без session=logged_in логин не возвращается."""

    class FakeHandler:
        headers = {"Cookie": "auth_user=neo"}

    assert get_session_username(FakeHandler()) is None


def test_build_session_cookies_includes_username() -> None:
    """После входа выставляются обе куки сессии."""
    cookies = build_session_cookies("neo")
    assert len(cookies) == 2
    assert cookies[0] == "session=logged_in; HttpOnly; SameSite=Strict; Path=/"
    assert "auth_user=neo" in cookies[1]


def test_allow_post_blocks_after_limit() -> None:
    """После лимита запросов в окне allow_post возвращает False."""
    rate_limit_module._post_hits.clear()
    client = "203.0.113.10"
    for _ in range(POST_MAX_PER_WINDOW):
        assert allow_post(client) is True
    assert allow_post(client) is False
    rate_limit_module._post_hits.clear()
