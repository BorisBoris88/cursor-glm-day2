# Авторизация

## Регистрация и вход

1. `POST /api/register` — `create_user()` в SQLite, пароль хешируется через `hashlib.pbkdf2_hmac` (120 000 итераций, соль в `password_hash`).
2. `POST /api/login` — `check_user(username, password)`.
3. При успехе выставляются две HttpOnly-куки (`Path=/`, `SameSite=Strict`):
   - `session=logged_in`
   - `auth_user=<url-encoded username>`

## Выход

`POST /api/logout` сбрасывает обе куки (`Max-Age=0`).

## Проверка на GET

В начале `do_GET` (`server.py`):

- публично: `/login`, `/login.html`, `/css/*`, `/js/*`
- HTML без сессии → редирект `302` на `/login`
- API без сессии → `403 Forbidden`

## Фронтенд

- `js/login.js` — вкладки «Вход» / «Регистрация», сохраняет логин в `sessionStorage` для мгновенного показа в шапке
- `js/session.js` — `GET /api/me`, элемент `#headerUsername` на `index.html`
- `js/logout.js` — очистка `sessionStorage` и редирект на `login.html`

## Ограничения (учебный проект)

- Сессия не подписана криптографически: клиент не может подделать `session`, но теоретически может подставить чужой `auth_user` вручную. Для продакшена нужна подписанная сессия (HMAC/JWT).
- `POST /api/messages` требует сессию; автор сообщения берётся из `auth_user`, поле `username` в JSON игнорируется.
- Демо-учётка `neo`/`mat123` создаётся при пустой таблице `users` — только для локальной разработки.
