# Деплой

## Локально

```bash
pip install -r requirements.txt
python server.py
```

- URL: http://localhost:8080/
- `HOST` не задан → `localhost`
- `PORT` не задан → `8080`

## Docker

```bash
docker build -t neonshadow .
docker run -p 10000:10000 -e PORT=10000 -e HOST=0.0.0.0 neonshadow
```

### Dockerfile

- Базовый образ: `python:3.14-slim`
- `WORKDIR /app`, `HOST=0.0.0.0` в `ENV`
- `EXPOSE 10000` — документация порта (не открывает его сам по себе)
- `CMD ["python", "server.py"]`

Важно: без `-e PORT=10000` сервер слушает **8080** (дефолт из `server_config.py`), а `EXPOSE` указывает 10000.

### .dockerignore

Исключает `.git`, `.venv`, `*.db`, `app.log`, `.pytest_cache`, `.cursor/`.

## Render

Файл `render.yaml` — Blueprint для [Render](https://render.com):

- `runtime: docker`
- `HOST=0.0.0.0`
- `PORT` задаётся платформой (часто `10000`)
- `healthCheckPath: /` (нужна сессия для главной — учитывайте при настройке health check)

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `HOST` | `localhost` | Адрес привязки сервера |
| `PORT` | `8080` | Порт HTTP |
| `PYTHONUNBUFFERED` | — | Логи в Docker без буферизации |

## Зависимости

`requirements.txt`:

```
httpx>=0.28,<1
rich>=13,<15
```

`pytest` нужен только для разработки (не в `requirements.txt` production-образа).
