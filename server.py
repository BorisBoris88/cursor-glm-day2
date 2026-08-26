import asyncio
import json
import logging
import sqlite3
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

from api_client import NewsApiError, fetch_top_articles
from auth import (
    build_clear_session_cookies,
    build_session_cookies,
    get_session_username,
    has_session_cookie,
    is_login_get_path,
    is_protected_page,
    normalize_path,
    requires_session,
)
from backend import generate_hacker_aliases
from bot_replies import BOT_USERNAME, reply_for
from database import (
    UserExistsError,
    check_user,
    create_user,
    get_messages,
    init_db,
    save_message,
)
from http_utils import (
    NoStoreHeadersMixin,
    allowed_origin,
    apply_cors,
    is_forbidden_static,
    read_json_body,
    send_json,
)
from logging_config import setup_logging
from rate_limit import allow_post
from server_config import server_host, server_port
from translate import translate_article_titles
from users import SITE_USERS
from weather import current_weather_snapshot

logger = logging.getLogger(__name__)

DIRECTORY = Path(__file__).resolve().parent
MAX_MESSAGE_LENGTH = 500
MAX_USERNAME_LENGTH = 64
MAX_PASSWORD_LENGTH = 128


async def _load_news_articles() -> list[dict[str, str | int]]:
    """Топ Hacker News, затем перевод заголовков на русский."""
    articles = await fetch_top_articles()
    return await translate_article_titles(articles)


class Handler(NoStoreHeadersMixin, SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def do_OPTIONS(self) -> None:
        if allowed_origin(self) is None:
            self.send_error(403, "Origin не разрешён")
            return
        self.send_response(204)
        apply_cors(self)
        self.end_headers()

    def do_GET(self) -> None:
        if is_forbidden_static(self.path):
            self.send_error(404, "Not Found")
            return

        if requires_session(self.path) and not has_session_cookie(self):
            if is_protected_page(self.path):
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            self.send_error(403, "Forbidden")
            return

        if normalize_path(self.path) == "/":
            self.path = "/index.html"
            return super().do_GET()

        if is_login_get_path(self.path) and normalize_path(self.path) == "/login":
            self.path = "/login.html"
            return super().do_GET()

        if self.path == "/api/hackers":
            try:
                aliases = generate_hacker_aliases()
            except Exception:
                logger.exception("Не удалось сгенерировать алиасы")
                send_json(self, {"error": "Не удалось сгенерировать алиасы"}, status=500)
                return
            send_json(self, {"aliases": aliases})
            return

        if self.path == "/api/users":
            send_json(self, {"users": SITE_USERS})
            return

        if self.path == "/api/me":
            username = get_session_username(self)
            if username is None:
                send_json(self, {"error": "Не авторизован"}, status=401)
                return
            send_json(self, {"username": username})
            return

        if self.path == "/api/weather":
            try:
                snapshot = current_weather_snapshot()
            except (urllib.error.URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
                logger.exception("Погода недоступна")
                send_json(self, {"error": "Погода недоступна"}, status=502)
                return
            send_json(self, snapshot)
            return

        if self.path == "/api/news":
            try:
                articles = asyncio.run(_load_news_articles())
            except (NewsApiError, ValueError, RuntimeError, OSError):
                logger.exception("Новости недоступны")
                send_json(self, {"error": "Новости недоступны"}, status=502)
                return
            send_json(self, {"articles": articles})
            return

        if self.path == "/api/messages":
            try:
                messages = get_messages()
            except sqlite3.Error:
                logger.exception("Ошибка чтения сообщений из базы")
                send_json(self, {"error": "Ошибка базы данных"}, status=500)
                return
            send_json(self, {"messages": messages})
            return

        return super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/login":
            self._handle_login_post()
            return
        if self.path == "/api/register":
            self._handle_register_post()
            return
        if self.path == "/api/logout":
            self._handle_logout_post()
            return
        if self.path == "/api/messages":
            self._handle_messages_post()
            return
        self.send_error(404, "Not Found")

    def _parse_credentials(self) -> tuple[str, str] | None:
        """Читает username и password из JSON-тела POST."""
        try:
            data = read_json_body(self)
        except OSError:
            send_json(self, {"error": "Слишком большое тело запроса"}, status=413)
            return None
        except (ValueError, json.JSONDecodeError):
            send_json(self, {"error": "Некорректный JSON"}, status=400)
            return None

        username = data.get("username")
        password = data.get("password")
        if not isinstance(username, str) or not username.strip():
            send_json(self, {"error": "Нужно поле username"}, status=400)
            return None
        if not isinstance(password, str) or not password:
            send_json(self, {"error": "Нужно поле password"}, status=400)
            return None

        username = username.strip()
        if len(username) > MAX_USERNAME_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            send_json(self, {"error": "Слишком длинные учётные данные"}, status=400)
            return None
        return username, password

    def _handle_logout_post(self) -> None:
        client_ip = self.client_address[0]
        if not allow_post(client_ip):
            logger.warning("Лимит POST превышен для %s", client_ip)
            send_json(self, {"error": "Слишком много запросов"}, status=429)
            return

        send_json(
            self,
            {"ok": True},
            set_cookies=build_clear_session_cookies(),
        )

    def _handle_login_post(self) -> None:
        client_ip = self.client_address[0]
        if not allow_post(client_ip):
            logger.warning("Лимит POST превышен для %s", client_ip)
            send_json(self, {"error": "Слишком много запросов"}, status=429)
            return

        credentials = self._parse_credentials()
        if credentials is None:
            return
        username, password = credentials

        try:
            if not check_user(username, password):
                send_json(self, {"error": "Доступ запрещен"}, status=401)
                return
        except sqlite3.Error:
            logger.exception("Ошибка проверки пользователя")
            send_json(self, {"error": "Ошибка базы данных"}, status=500)
            return

        send_json(
            self,
            {"ok": True},
            set_cookies=build_session_cookies(username),
        )

    def _handle_register_post(self) -> None:
        client_ip = self.client_address[0]
        if not allow_post(client_ip):
            logger.warning("Лимит POST превышен для %s", client_ip)
            send_json(self, {"error": "Слишком много запросов"}, status=429)
            return

        credentials = self._parse_credentials()
        if credentials is None:
            return
        username, password = credentials

        try:
            user_id = create_user(username, password)
        except UserExistsError:
            send_json(self, {"error": "Логин уже занят"}, status=409)
            return
        except sqlite3.Error:
            logger.exception("Ошибка регистрации пользователя")
            send_json(self, {"error": "Ошибка базы данных"}, status=500)
            return

        send_json(
            self,
            {"ok": True, "id": user_id},
            status=201,
            set_cookies=build_session_cookies(username),
        )

    def _handle_messages_post(self) -> None:
        client_ip = self.client_address[0]
        if not allow_post(client_ip):
            logger.warning("Лимит POST превышен для %s", client_ip)
            send_json(self, {"error": "Слишком много запросов"}, status=429)
            return

        try:
            data = read_json_body(self)
        except OSError:
            send_json(self, {"error": "Слишком большое тело запроса"}, status=413)
            return
        except (ValueError, json.JSONDecodeError):
            send_json(self, {"error": "Некорректный JSON"}, status=400)
            return

        username = data.get("username")
        text = data.get("text")
        if not isinstance(username, str) or not username.strip():
            send_json(self, {"error": "Нужно поле username"}, status=400)
            return
        if not isinstance(text, str) or not text.strip():
            send_json(self, {"error": "Нужно поле text"}, status=400)
            return

        username = username.strip()
        text = text.strip()
        if len(username) > MAX_USERNAME_LENGTH:
            send_json(self, {"error": "Слишком длинное имя"}, status=400)
            return
        if len(text) > MAX_MESSAGE_LENGTH:
            send_json(self, {"error": "Слишком длинное сообщение"}, status=400)
            return

        try:
            message_id = save_message(username, text)
            response_messages: list[dict[str, str | int]] = [
                {"id": message_id, "username": username, "text": text},
            ]
            bot_text = reply_for(text)
            if bot_text is not None:
                bot_id = save_message(BOT_USERNAME, bot_text)
                response_messages.append(
                    {"id": bot_id, "username": BOT_USERNAME, "text": bot_text}
                )
        except sqlite3.Error:
            logger.exception("Ошибка записи сообщения в базу")
            send_json(self, {"error": "Ошибка базы данных"}, status=500)
            return

        send_json(self, {"messages": response_messages}, status=201)

    def log_message(self, fmt: str, *args: object) -> None:
        """Пишет access-лог http.server через модуль logging."""
        logger.info("%s - %s", self.address_string(), fmt % args)


if __name__ == "__main__":
    setup_logging()
    init_db()
    host = server_host()
    port = server_port()
    server = HTTPServer((host, port), Handler)
    logger.info("Сервер запущен: http://%s:%s/", host, port)
    logger.info("Нажмите Ctrl+C для остановки.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен.")
