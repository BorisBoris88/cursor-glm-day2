"""Общие HTTP-хелперы: JSON, CORS, запрет служебной статики."""

import json
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

ALLOWED_ORIGINS = frozenset({
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "null",
})
MAX_BODY_BYTES = 4096
FORBIDDEN_STATIC_SUFFIXES: tuple[str, ...] = (".db", ".sqlite", ".sqlite3")


class NoStoreHeadersMixin:
    """Добавляет Cache-Control: no-store ко всем ответам."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def allowed_origin(handler: SimpleHTTPRequestHandler) -> str | None:
    """Возвращает Origin, если он в белом списке."""
    origin = handler.headers.get("Origin")
    if origin is not None and origin in ALLOWED_ORIGINS:
        return origin
    return None


def apply_cors(handler: SimpleHTTPRequestHandler) -> None:
    """Пишет CORS-заголовки только для разрешённых origin."""
    origin = allowed_origin(handler)
    if origin is None:
        return
    handler.send_header("Access-Control-Allow-Origin", origin)
    handler.send_header("Vary", "Origin")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")


def send_json(
    handler: SimpleHTTPRequestHandler,
    payload: object,
    status: int = 200,
    extra_headers: dict[str, str] | None = None,
    set_cookies: list[str] | None = None,
) -> None:
    """Отправляет JSON-ответ с CORS для разрешённых origin."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    apply_cors(handler)
    if extra_headers is not None:
        for name, value in extra_headers.items():
            handler.send_header(name, value)
    if set_cookies is not None:
        for cookie in set_cookies:
            handler.send_header("Set-Cookie", cookie)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json_body(
    handler: SimpleHTTPRequestHandler,
    max_bytes: int = MAX_BODY_BYTES,
) -> dict[str, object]:
    """Читает JSON-объект из тела POST с лимитом размера."""
    length_header = handler.headers.get("Content-Length", "0")
    try:
        length = int(length_header)
    except ValueError as extra:
        raise ValueError("Некорректный Content-Length") from extra
    if length < 0 or length > max_bytes:
        raise OSError("Тело запроса слишком большое")
    raw = handler.rfile.read(length)
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Ожидался JSON-объект")
    return data


def is_forbidden_static(request_path: str) -> bool:
    """Запрещает раздавать базу и sqlite-файлы из корня."""
    raw_path = unquote(request_path.split("?", 1)[0])
    name = Path(raw_path).name.lower()
    return name.endswith(FORBIDDEN_STATIC_SUFFIXES)
