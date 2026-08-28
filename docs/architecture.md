# Архитектура

## Обзор

NeonShadow — статический киберпанк-сайт с бэкендом на `http.server` (без Flask/FastAPI). Статика и API отдаются из корня проекта.

```
Браузер
   │  HTML/CSS/JS (корень)
   │  fetch /api/*
   ▼
server.py (Handler)
   ├── auth.py          — куки, публичные маршруты
   ├── database.py      — SQLite (users, messages)
   ├── http_utils.py    — JSON, CORS
   ├── rate_limit.py    — лимит POST
   ├── api_client.py    — Hacker News (httpx, async)
   ├── translate.py     — перевод заголовков (httpx)
   ├── weather.py       — Open-Meteo (urllib)
   ├── backend.py       — генерация алиасов
   └── bot_replies.py   — ответы NeonBot
```

## Страницы

| Файл | Назначение |
|------|------------|
| `index.html` | Главная: алиасы, новости, погода, чат |
| `login.html` | Вход и регистрация |
| `about.html`, `contact.html` | Информационные страницы |

Защищённые страницы требуют куку `session=logged_in`. Без сессии — редирект на `/login`.

## JavaScript

| Файл | Зона ответственности |
|------|----------------------|
| `js/api.js` | `apiUrl`, `apiFetch`, `sessionStorage` для логина |
| `js/session.js` | `@логин` в шапке (`GET /api/me`) |
| `js/login.js` | Вход / регистрация |
| `js/logout.js` | Выход |
| `js/weather.js` | Виджет погоды |
| `js/news.js` | Лента Hacker News |
| `js/aliases.js` | Кнопка «Взломать базу» |
| `js/chat.js` | Чат NeonBot |

## Конфигурация сервера

`server_config.py` читает из окружения:

- `HOST` — по умолчанию `0.0.0.0`; локально можно `127.0.0.1`
- `PORT` — по умолчанию `8080`; на Render обычно `10000`

## База данных

Файл `hackathon.db` в корне (в `.gitignore`).

- **users** — `id`, `username`, `password_hash` (PBKDF2-HMAC-SHA256)
- **messages** — чат: `username`, `text`, `timestamp`

Таблица `users` изначально пуста — учётные записи только через регистрацию.
