# NeonShadow

Киберпанк-сайт с бэкендом на стандартной библиотеке Python: тёмная неоновая тема, виджеты в реальном времени, чат-бот и авторизация через SQLite.

## Возможности

- **Главная** — профиль хакера, генерация фейковых алиасов, лента Hacker News с переводом заголовков на русский
- **Погода** — виджет текущей температуры в Москве (Open-Meteo)
- **Чат NeonBot** — сообщения сохраняются в SQLite, бот отвечает по ключевому слову
- **Авторизация** — вход и регистрация, сессионные HttpOnly-куки, отображение `@логин` в шапке
- **Страницы** — «О нас», «Контакты», защищённые маршруты с редиректом на `/login`

## Стек

| Слой | Технологии |
|------|------------|
| Бэкенд | Python 3.14, `http.server`, SQLite |
| Фронтенд | HTML, ванильный CSS (БЭМ), ванильный JS |
| Сеть | `httpx` (Hacker News, перевод), `urllib` (погода) |
| CLI | `rich` (генерация алиасов в `backend.py`) |

Без фреймворков (Flask, FastAPI, React), без npm и сборщиков.

## Быстрый старт

### Требования

- Python 3.14+
- Зависимости: `httpx`, `rich`, `pytest` (для тестов)

```bash
pip install httpx rich pytest
```

### Запуск

```bash
pip install -r requirements.txt
python server.py
```

Сайт: [http://localhost:8080/](http://localhost:8080/) (`PORT` и `HOST` — см. `server_config.py`).

### Docker

```bash
docker build -t neonshadow .
docker run -p 10000:10000 -e PORT=10000 -e HOST=0.0.0.0 neonshadow
```

Деплой на Render: `render.yaml`. Подробнее — [docs/deployment.md](docs/deployment.md).

### Демо-учётка

После инициализации БД доступен пользователь:

| Логин | Пароль |
|-------|--------|
| `neo` | `mat123` |

Новых пользователей можно зарегистрировать на странице входа (`/login`).

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/hackers` | Список сгенерированных хакерских алиасов |
| `GET` | `/api/weather` | Текущая погода в Москве |
| `GET` | `/api/news` | Топ статей Hacker News (заголовки на русском) |
| `GET` | `/api/messages` | История сообщений чата |
| `POST` | `/api/messages` | Отправить сообщение в чат |
| `GET` | `/api/users` | Демо-список пользователей сайта |
| `GET` | `/api/me` | Логин авторизованного пользователя |
| `POST` | `/api/login` | Вход (`username`, `password`) |
| `POST` | `/api/register` | Регистрация |
| `POST` | `/api/logout` | Выход, сброс сессии |

Защищённые страницы и API требуют куку `session=logged_in`. Пароли в БД хранятся как PBKDF2-HMAC-SHA256 хеши (`hashlib`).

## Документация

Подробные разделы в папке **[docs/](docs/README.md)**:

- [Архитектура](docs/architecture.md)
- [HTTP API](docs/api.md)
- [Авторизация](docs/auth.md)
- [Деплой](docs/deployment.md)

Для **Cursor Docs**: Settings → Features → Docs → Add documentation → укажите папку `docs/` или корневой `README.md`.

## Структура проекта

```
├── server.py          # HTTP-сервер, маршрутизация API
├── database.py        # SQLite: users, messages
├── auth.py            # Сессионные куки, проверка доступа
├── http_utils.py      # JSON-ответы, CORS
├── api_client.py      # Клиент Hacker News
├── translate.py       # Перевод заголовков новостей
├── weather.py         # Погода Open-Meteo
├── backend.py         # Генерация алиасов (CLI + API)
├── bot_replies.py     # Ответы NeonBot
├── server_config.py   # HOST, PORT из env
├── Dockerfile         # Docker-образ
├── render.yaml        # Blueprint Render
├── requirements.txt
├── docs/              # Документация проекта
├── index.html         # Главная
├── login.html         # Вход и регистрация
├── about.html         # О нас
├── contact.html       # Контакты
├── css/style.css      # Стили (БЭМ)
├── js/                # Виджеты и API-клиент
└── tests/             # pytest-тесты
```

## Тесты

```bash
python -m pytest tests/ -q
```

## Лицензия

Учебный проект. Используйте свободно в образовательных целях.
