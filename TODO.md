# NeonShadow — рекомендации по улучшению структуры

Документ зафиксирован по результатам анализа проекта. Вернуться к пунктам после доработки текущих задач.

## Текущая карта

```
/workspace
├── server.py              # HTTP-сервер + вся маршрутизация (~320 строк)
├── auth.py, database.py   # сессии и SQLite
├── http_utils.py, rate_limit.py, logging_config.py
├── backend.py             # генерация алиасов (имя вводит в заблуждение)
├── api_client.py, translate.py, weather.py
├── bot_replies.py, users.py
├── *.html                 # 5 страниц в корне
├── css/style.css          # ~1255 строк, один файл
├── js/                    # 8 скриптов
├── tests/                 # 4 модуля тестов
└── data.json              # снимок алиасов (только CLI)
```

## Что уже хорошо

- **Разделение по зонам ответственности** на уровне модулей: `auth`, `database`, `http_utils`, `rate_limit`, виджеты в отдельных JS-файлах.
- **Строгая типизация** в Python, t-strings в `backend.py`, тесты на хелперы без поднятия сервера.
- **БЭМ** в CSS и разметке в целом соблюдается.
- **Безопасность базовая**: PBKDF2 для паролей, запрет раздачи `.db`, rate limit на POST, HttpOnly-куки.

---

## Проблемы и предложения

### 1. `server.py` стал «бог-объектом» (высокий приоритет)

Сейчас в одном классе `Handler` смешаны: статика, авторизация, 10+ API-эндпоинтов, валидация JSON, rate limit.

**Предложение** — вынести маршрутизацию без фреймворков:

```
handlers/
  __init__.py
  hackers.py      # GET /api/hackers
  news.py         # GET /api/news
  auth_routes.py  # login/register/logout/me
  messages.py     # GET/POST /api/messages
router.py         # match path + method → handler
```

`server.py` остаётся точкой входа: `HTTPServer` + тонкий `Handler`, который делегирует в `router.dispatch(self)`.

Повторяющийся блок rate limit в каждом POST можно свернуть в декоратор/хелпер:

```python
def require_post_allowed(handler: Handler) -> bool:
    if not allow_post(handler.client_address[0]):
        send_json(handler, {"error": "Слишком много запросов"}, status=429)
        return False
    return True
```

### 2. Расхождение документации с кодом (средний приоритет)

`.cursorrules` и часть README описывают проект без auth, SQLite, чата и `login.html`. В README API полный, в `.cursorrules` — только 2 эндпоинта.

**Предложение:** синхронизировать `.cursorrules` с фактической структурой или сделать его ссылкой на README как единый источник истины.

### 3. Дублирование HTML (средний приоритет)

Шапка, навигация, фон (`cyber-grid`, `matrix-rain`), футер копируются на 5 страниц. При этом:

- на `index.html` есть `#headerUsername` и `session.js`;
- на `about.html` / `contact.html` — нет ни элемента, ни скрипта;
- на `about`/`contact` нет единого брендинга `NeonShadow` в шапке.

**Варианты без сборщика:**

| Подход | Плюсы | Минусы |
|--------|-------|--------|
| Серверный include (шаблон в `server.py`) | DRY, один источник шапки | Нужна простая подстановка HTML |
| JS-инъекция шапки (`js/layout.js`) | Без правок сервера | FOUC, хуже для SEO/a11y |
| Копипаст + чеклист | Минимум изменений | Дрейф при каждой правке |

Для этого проекта оптимален **серверный фрагмент** (`templates/_header.html`) с подстановкой активной ссылки — без npm и без фреймворка.

### 4. Несогласованность данных пользователей (средний приоритет)

- `database.py` — реальные пользователи (логин/регистрация).
- `users.py` — захардкоженный демо-список для `GET /api/users`.
- Фронтенд нигде не использует `/api/users`.

**Предложение:** либо убрать `users.py` и эндпоинт, либо отдавать из SQLite (без паролей) и использовать на странице «О нас».

### 5. Безопасность чата (высокий приоритет)

`POST /api/messages` принимает `username` из тела запроса и **не сверяет** его с сессией. Любой авторизованный клиент может писать от чужого имени.

**Предложение:** брать `username` из `get_session_username(self)`; поле `username` в JSON убрать или игнорировать.

Аналогично: сессия — это `session=logged_in` + `auth_user=...` без подписи. Пользователь теоретически может подставить чужой `auth_user`. Для учебного проекта допустимо, но стоит задокументировать; для усиления — HMAC-подпись сессии в одной куке.

### 6. `asyncio.run()` внутри синхронного GET (средний приоритет)

В `server.py` для `/api/news` на каждый запрос создаётся новый event loop — дорого и может ломаться при параллельных запросах.

**Предложение:** синхронная обёртка в `api_client.py` / `translate.py` через `httpx` sync client, либо один общий loop в отдельном потоке. Плюс **кэш новостей** (TTL 5–10 мин) в памяти или SQLite.

### 7. Монолитный CSS (~1255 строк)

**Предложение** — разбить по блокам БЭМ без препроцессора:

```
css/
  base.css          # :root, reset, body
  layout.css        # site-header, site-nav, page-container
  components/
    weather-widget.css
    chat-panel.css
    news-feed.css
    login-form.css
```

На страницах — несколько `<link>`, или сервер отдаёт один «склеенный» файл (простая конкатенация в Python).

### 8. Инфраструктура разработки (низкий приоритет, быстрый выигрыш)

| Чего нет | Зачем |
|----------|-------|
| `requirements.txt` / `pyproject.toml` | Воспроизводимая установка (`httpx`, `rich`, `pytest`) |
| `Makefile` или `scripts/dev.sh` | `run`, `test`, `lint` одной командой |
| CI (GitHub Actions) | `pytest` на push |
| Тесты auth/messages/server | Сейчас покрыты хелперы, но не интеграция |

### 9. Мелкие несоответствия

- **`backend.py`** — по сути `aliases.py` или `hacker_aliases.py`.
- **Имена в чате:** `chat.js` шлёт `Neo`, бот сохраняется как `Bot` (`bot_replies.BOT_USERNAME`), в UI тип сообщения определяется сравнением с `Neo` — баг отображения ответов бота.
- **Инлайн-стили** в `index.html` (строки 49–50) — нарушают правила БЭМ; вынести в `.hacker-desc__access`, `.hacker-desc__danger`.
- **`app.log` и `__pycache__`** в рабочей директории — в `.gitignore` есть, но артефакты лежат рядом с кодом; для БД лучше `data/hackathon.db`.
- **Смешение HTTP-клиентов:** `httpx` (новости) + `urllib` (погода) — унифицировать на `urllib` (без зависимостей) или на `httpx` (единый стиль).

---

## Предлагаемая целевая структура

Без фреймворков, с минимальной реорганизацией:

```
/workspace
├── server.py                 # точка входа
├── router.py                 # маршрутизация
├── handlers/                 # обработчики API
├── services/                 # бизнес-логика
│   ├── aliases.py            # бывший backend.py
│   ├── news.py               # api_client + translate
│   ├── weather.py
│   └── auth.py               # куки + проверки
├── db/
│   ├── database.py
│   └── hackathon.db          # или data/
├── static/                   # опционально: html, css, js
│   ├── index.html
│   ├── css/
│   └── js/
├── templates/                # фрагменты шапки/футера
├── tests/
├── requirements.txt
└── README.md
```

Перенос статики в `static/` потребует смены `DIRECTORY` в `Handler` и путей в HTML — это отдельный шаг; остальное можно внедрять постепенно.

---

## Приоритетный план (по эффективности / затратам)

1. **Быстро:** починить username в чате (сервер + `Bot`/`Neo`), добавить `requirements.txt`.
2. **Важно:** привязать `POST /api/messages` к сессии; убрать `asyncio.run` из hot path.
3. **Структура:** вынести API-хендлеры из `server.py`, DRY для rate limit.
4. **Фронт:** общий шаблон шапки; `session.js` на всех защищённых страницах.
5. **Позже:** разбить CSS, кэш новостей, унификация HTTP-клиента, CI.
