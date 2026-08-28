"""Сессионные куки и проверка публичных маршрутов."""

from http.server import SimpleHTTPRequestHandler
from urllib.parse import quote, unquote

SESSION_COOKIE = "session=logged_in; HttpOnly; SameSite=Strict; Path=/"
SESSION_CLEAR_COOKIE = "session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"
SESSION_COOKIE_VALUE = "session=logged_in"
AUTH_USER_COOKIE_NAME = "auth_user"
AUTH_USER_CLEAR_COOKIE = (
    f"{AUTH_USER_COOKIE_NAME}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"
)
LOGIN_GET_PATHS = frozenset({"/login", "/login.html"})
PROTECTED_PAGE_PATHS = frozenset({
    "/",
    "/index.html",
    "/about.html",
    "/contact.html",
})


def normalize_path(path: str) -> str:
    """Возвращает путь без query-string."""
    return path.split("?", 1)[0]


def build_auth_user_cookie(username: str) -> str:
    """Собирает HttpOnly-куку с логином авторизованного пользователя."""
    encoded = quote(username, safe="")
    return (
        f"{AUTH_USER_COOKIE_NAME}={encoded}; HttpOnly; SameSite=Strict; Path=/"
    )


def build_session_cookies(username: str) -> list[str]:
    """Куки сессии после успешного входа или регистрации."""
    return [SESSION_COOKIE, build_auth_user_cookie(username)]


def build_clear_session_cookies() -> list[str]:
    """Сбрасывает куки сессии при выходе."""
    return [SESSION_CLEAR_COOKIE, AUTH_USER_CLEAR_COOKIE]


def _parse_cookie_map(handler: SimpleHTTPRequestHandler) -> dict[str, str]:
    """Разбирает заголовок Cookie в словарь name -> value."""
    cookie_header = handler.headers.get("Cookie")
    if cookie_header is None:
        return {}
    parsed: dict[str, str] = {}
    for part in cookie_header.split(";"):
        if "=" not in part:
            continue
        name, value = part.split("=", maxsplit=1)
        parsed[name.strip()] = value.strip()
    return parsed


def has_session_cookie(handler: SimpleHTTPRequestHandler) -> bool:
    """Проверяет наличие session=logged_in в заголовке Cookie."""
    cookies = _parse_cookie_map(handler)
    return cookies.get("session") == "logged_in"


def get_session_username(handler: SimpleHTTPRequestHandler) -> str | None:
    """Возвращает логин из куки auth_user, если сессия активна."""
    if not has_session_cookie(handler):
        return None
    raw_username = _parse_cookie_map(handler).get(AUTH_USER_COOKIE_NAME)
    if raw_username is None or raw_username == "":
        return None
    return unquote(raw_username)


def is_login_get_path(path: str) -> bool:
    """Возвращает True, если GET-запрос идёт на страницу входа."""
    return normalize_path(path) in LOGIN_GET_PATHS


def is_public_static_path(path: str) -> bool:
    """CSS, JS и favicon доступны без сессии."""
    clean = normalize_path(path)
    if clean in ("/favicon.svg", "/favicon.ico"):
        return True
    return clean.startswith("/css/") or clean.startswith("/js/")


def is_protected_page(path: str) -> bool:
    """HTML-страницы, требующие сессии."""
    return normalize_path(path) in PROTECTED_PAGE_PATHS


def requires_session(path: str) -> bool:
    """True, если GET-запрос должен быть с сессионной кукой."""
    return not is_login_get_path(path) and not is_public_static_path(path)
