"""Работа с SQLite: messages и users в файле hackathon.db."""

import hashlib
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH: Path = Path(__file__).resolve().parent / "hackathon.db"
MESSAGES_LIMIT = 200
CONNECT_TIMEOUT_SEC = 5.0
PBKDF2_ITERATIONS = 120_000


class UserExistsError(Exception):
    """Пользователь с таким логином уже существует."""


def _connect() -> sqlite3.Connection:
    """Открывает соединение с таймаутом ожидания блокировки."""
    connection = sqlite3.connect(DB_PATH, timeout=CONNECT_TIMEOUT_SEC)
    connection.row_factory = sqlite3.Row
    return connection


def hash_password(password: str) -> str:
    """Хеширует пароль через PBKDF2-HMAC-SHA256 (hashlib)."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Сверяет пароль с сохранённым хешем."""
    try:
        salt, stored_hex = password_hash.split("$", maxsplit=1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return secrets.compare_digest(digest.hex(), stored_hex)


def init_db() -> None:
    """Создаёт таблицы messages и users, если их ещё нет."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )


def create_user(username: str, password: str) -> int:
    """Регистрирует пользователя и возвращает его id."""
    password_hash = hash_password(password)
    try:
        with _connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """,
                (username, password_hash),
            )
            return int(cursor.lastrowid or 0)
    except sqlite3.IntegrityError as extra:
        raise UserExistsError("Логин уже занят") from extra


def check_user(username: str, password: str) -> bool:
    """Проверяет логин и пароль по таблице users."""
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT password_hash
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()
    if row is None:
        return False
    stored_hash = str(row["password_hash"])
    return verify_password(password, stored_hash)


def save_message(username: str, text: str) -> int:
    """Сохраняет сообщение и возвращает его id."""
    timestamp: str = datetime.now().isoformat(timespec="seconds")
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO messages (username, text, timestamp)
            VALUES (?, ?, ?)
            """,
            (username, text, timestamp),
        )
        return int(cursor.lastrowid or 0)


def get_messages(limit: int = MESSAGES_LIMIT) -> list[dict[str, str | int]]:
    """Возвращает последние сообщения в порядке добавления."""
    safe_limit = max(1, min(limit, MESSAGES_LIMIT))
    with _connect() as connection:
        cursor = connection.execute(
            """
            SELECT id, username, text, timestamp
            FROM (
                SELECT id, username, text, timestamp
                FROM messages
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (safe_limit,),
        )
        return [
            {
                "id": int(row["id"]),
                "username": str(row["username"]),
                "text": str(row["text"]),
                "timestamp": str(row["timestamp"]),
            }
            for row in cursor.fetchall()
        ]
