"""Тесты SQLite: изолированная in-memory база, hackathon.db не трогаем."""

import sqlite3
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import database  # noqa: E402


@pytest.fixture
def memory_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Подменяет соединение на общую in-memory БД (аналог :memory:).

    Обычный sqlite3.connect(':memory:') нельзя: каждый with _connect()
    закрывает соединение и уничтожает базу. Именованная memory-URI
    с cache=shared видна всем новым соединениям в этом тесте.
    """
    uri = f"file:testdb_{uuid.uuid4().hex}?mode=memory&cache=shared"

    def connect() -> sqlite3.Connection:
        connection = sqlite3.connect(uri, uri=True, timeout=5.0)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr(database, "_connect", connect)
    database.init_db()
    yield


def test_get_messages_returns_list(memory_db: None) -> None:
    """get_messages() всегда возвращает список."""
    messages = database.get_messages()
    assert isinstance(messages, list)


def test_save_message_persists_row(memory_db: None) -> None:
    """save_message() записывает строку, get_messages() её читает."""
    message_id = database.save_message("Neo", "Привет из теста")

    assert isinstance(message_id, int)
    assert message_id > 0

    messages = database.get_messages()
    assert isinstance(messages, list)
    assert messages != []

    saved = messages[-1]
    assert saved["id"] == message_id
    assert saved["username"] == "Neo"
    assert saved["text"] == "Привет из теста"
    assert isinstance(saved["timestamp"], str)
    assert saved["timestamp"] != ""


def test_get_messages_empty_after_init(memory_db: None) -> None:
    """После init_db таблица пустая, но это всё ещё list."""
    messages = database.get_messages()
    assert isinstance(messages, list)
    assert messages == []


def test_create_user_and_check_user(memory_db: None) -> None:
    """Пользователь сохраняется с хешем, check_user проверяет пароль."""
    user_id = database.create_user("shadow", "secret42")

    assert isinstance(user_id, int)
    assert user_id > 0
    assert database.check_user("shadow", "secret42") is True
    assert database.check_user("shadow", "wrong") is False
    assert database.check_user("ghost", "secret42") is False


def test_create_user_rejects_duplicate_username(memory_db: None) -> None:
    """Повторная регистрация того же логина вызывает UserExistsError."""
    database.create_user("shadow", "first-pass")

    with pytest.raises(database.UserExistsError):
        database.create_user("shadow", "second-pass")


def test_demo_user_seeded_after_init(memory_db: None) -> None:
    """После init_db доступен демо-пользователь neo."""
    assert database.check_user("neo", "mat123") is True


def test_hash_password_uses_unique_salts() -> None:
    """Одинаковые пароли получают разные хеши из-за соли."""
    first = database.hash_password("same-password")
    second = database.hash_password("same-password")
    assert first != second
    assert database.verify_password("same-password", first) is True
    assert database.verify_password("same-password", second) is True
