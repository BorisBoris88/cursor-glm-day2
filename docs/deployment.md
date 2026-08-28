# Деплой

## Локально

```bash
pip install -r requirements.txt
python server.py
```

- URL: http://localhost:8080/
- `HOST` не задан → `0.0.0.0` (см. `server_config.py`)
- `PORT` не задан → `8080`

Ограничить доступ только с этой машины:

```bash
# PowerShell
$env:HOST="127.0.0.1"; python server.py
```

## Docker

```bash
docker build -t neonshadow .
docker run -p 10000:10000 -e PORT=10000 neonshadow
```

`HOST=0.0.0.0` уже задан в `Dockerfile`. Без `-e PORT=...` сервер слушает **8080** (дефолт из `server_config.py`).

### Dockerfile

- Базовый образ: `python:3.14-slim`
- `WORKDIR /app`, `HOST=0.0.0.0` и `PYTHONUNBUFFERED=1` в `ENV`
- `EXPOSE 10000` — документация порта для Render (не открывает порт сам по себе)
- `CMD ["python", "server.py"]`

### .dockerignore

Исключает `.git`, `.venv`, `*.db`, `app.log`, `.pytest_cache`, `.cursor/`.

## Render.com

Поддерживаются два способа: **Blueprint** (`render.yaml`) или ручная настройка в Dashboard.

### Blueprint (рекомендуется)

1. Render → **New** → **Blueprint**
2. Подключите репозиторий — подтянется `render.yaml`
3. Деплой запустится автоматически

### Dashboard вручную (Web Service + Docker)

| Поле | Значение |
|------|----------|
| **Environment** | Docker |
| **Dockerfile Path** | `./Dockerfile` |
| **Docker Context** | `.` |
| **Build Command** | *(пусто)* |
| **Start Command** | *(пусто)* |
| **Pre-Deploy Command** | *(пусто)* |
| **Health Check Path** | `/login` |

Build Command, Start Command и Pre-Deploy Command **оставьте пустыми**: сборка идёт через `docker build`, старт — `CMD ["python", "server.py"]` из Dockerfile. База SQLite создаётся при старте (`init_db()` в `server.py`), отдельная миграция не нужна.

### Переменные среды на Render

Задаются в **Environment → Environment Variables**. Можно вставить блок из `.env.example` (без комментариев `#`).

| Переменная | Задавать вручную? | Назначение |
|------------|-------------------|------------|
| `PORT` | **Нет** — Render подставляет сам | Порт HTTP (`server_config.py`) |
| `HOST` | Уже в Dockerfile; можно дублировать | `0.0.0.0` — слушать все интерфейсы |
| `PYTHONUNBUFFERED` | Уже в Dockerfile | Логи без буферизации |
| `RENDER_EXTERNAL_URL` | **Нет** — Render обычно задаёт сам | CORS для вашего URL |
| `CORS_ORIGINS` | Опционально | Доп. origin через запятую |

Минимальный набор в Dashboard (если не используете Blueprint):

```
HOST=0.0.0.0
PYTHONUNBUFFERED=1
```

Файл `.env` в репозитории **не используется** приложением (нет `python-dotenv`). Секреты и настройки — только через Dashboard или `render.yaml`.

### Health check

Главная `/` без сессии отдаёт **302** на `/login`. Для проверки живости укажите **`/login`** или **`/login.html`** (ответ **200**).

В `render.yaml` задано `healthCheckPath: /login`.

### Ограничения production на Render

- **SQLite** (`hackathon.db`) хранится в эфемерной файловой системе контейнера — при перезапуске или новом деплое данные пользователей и сообщений могут пропасть. Для постоянного хранения нужен Render Disk или внешняя БД.
- **Free plan** — сервис «засыпает» после простоя; первый запрос может занять десятки секунд.

## Переменные окружения (справочник)

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `HOST` | `0.0.0.0` | Адрес привязки сервера |
| `PORT` | `8080` | Порт HTTP |
| `PYTHONUNBUFFERED` | — | Логи в Docker/Render без буферизации |
| `RENDER_EXTERNAL_URL` | — | URL сервиса на Render (CORS) |
| `CORS_ORIGINS` | — | Дополнительные origin через запятую |

Шаблон для копирования: `.env.example`.

## Зависимости

`requirements.txt`:

```
httpx>=0.28,<1
rich>=13,<15
```

`pytest` нужен только для разработки (не в `requirements.txt` production-образа).
