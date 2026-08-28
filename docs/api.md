# HTTP API

Базовый URL локально: `http://localhost:8080`. JSON в UTF-8.

## Авторизация

Защищённые `GET` (кроме `/login`, `/login.html`, `/css/*`, `/js/*`) требуют куку:

```
Cookie: session=logged_in; auth_user=<логин>
```

`POST /api/login` и `POST /api/register` публичны (с rate limit).

## Эндпоинты

### Публичные (без сессии)

| Метод | Путь | Тело | Ответ |
|-------|------|------|-------|
| `POST` | `/api/login` | `{"username","password"}` | `200` + Set-Cookie; `401` при ошибке; `429` после 3 неудачных попыток с IP за 60 с |
| `POST` | `/api/register` | `{"username","password"}` | `201` + Set-Cookie; `409` если логин занят |

### Требуют сессию

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/me` | `{"username": "..."}` |
| `POST` | `/api/logout` | `{"ok": true}`, сброс кук |
| `GET` | `/api/hackers` | `{"aliases": string[]}` |
| `GET` | `/api/weather` | `{"temperature": number, ...}` |
| `GET` | `/api/news` | `{"articles": [{id, title, url}]}`, кэш 30 с |
| `GET` | `/api/messages` | `{"messages": [...]}` |
| `POST` | `/api/messages` | `{"text"}` → `201`; `username` берётся из сессии |
| `GET` | `/api/users` | Демо-список из `users.py` |

### Коды ошибок

| Код | Когда |
|-----|-------|
| `400` | Некорректный JSON или поля |
| `401` | Неверный логин/пароль или нет сессии (`/api/me`) |
| `403` | API без сессии |
| `413` | Слишком большое тело |
| `429` | Превышен лимит POST с IP |
| `500` | Ошибка SQLite |
| `502` | Погода или новости недоступны |

## Rate limit

`rate_limit.py`: не более 30 POST с одного IP за 60 секунд.

## CORS

Разрешённые origin: `http://localhost:8080`, `http://127.0.0.1:8080`, `null` (file://).
