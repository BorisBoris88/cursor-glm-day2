# Документация NeonShadow

Индекс документации проекта. Подключите папку `docs/` или корневой `README.md` в **Cursor → Settings → Features → Docs → Add documentation**, чтобы агент использовал актуальный контекст.

## Разделы

| Документ | Содержание |
|----------|------------|
| [architecture.md](architecture.md) | Структура модулей, потоки данных |
| [api.md](api.md) | HTTP API, коды ответов, авторизация |
| [auth.md](auth.md) | Вход, регистрация, куки, ограничения безопасности |
| [deployment.md](deployment.md) | Docker, Render, переменные окружения |

## Быстрые ссылки

- Запуск локально: `python server.py` → http://localhost:8080/
- Тесты: `python -m pytest tests/ -q`
- Зависимости: `pip install -r requirements.txt`
- Первый вход: регистрация на `/login`

## Источники истины

1. **Поведение API** — `server.py`, `auth.py`, `database.py`
2. **Правила для агента** — `.cursorrules` и `.cursor/rules/`
3. **Обзор для людей** — корневой `README.md`
