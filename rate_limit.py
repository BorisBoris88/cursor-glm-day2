"""Ограничение частоты POST с одного IP."""

import threading
import time

POST_WINDOW_SEC = 60.0
POST_MAX_PER_WINDOW = 30
LOGIN_FAILED_WINDOW_SEC = 60.0
LOGIN_FAILED_MAX = 3
LOGIN_RATE_LIMIT_ERROR = "Слишком много попыток входа. Попробуйте позже."

_post_hits: dict[str, list[float]] = {}
_login_failures: dict[str, list[float]] = {}
_rate_lock = threading.Lock()


def normalize_client_ip(client_ip: str) -> str:
    """Сводит localhost IPv6 к 127.0.0.1 для единого счётчика."""
    if client_ip in ("::1", "::ffff:127.0.0.1"):
        return "127.0.0.1"
    return client_ip


def _prune_hits(hits: list[float], window_sec: float, now: float) -> None:
    """Оставляет в списке только метки внутри скользящего окна."""
    hits[:] = [stamp for stamp in hits if now - stamp < window_sec]


def allow_post(client_ip: str) -> bool:
    """True, если с этого IP ещё можно принять POST в текущем окне."""
    client_ip = normalize_client_ip(client_ip)
    with _rate_lock:
        now = time.monotonic()
        hits = _post_hits.setdefault(client_ip, [])
        _prune_hits(hits, POST_WINDOW_SEC, now)
        if len(hits) >= POST_MAX_PER_WINDOW:
            return False
        hits.append(now)
        return True


def allow_login_attempt(client_ip: str) -> bool:
    """False, если с IP уже было 3 и более неудачных входов за 60 секунд."""
    client_ip = normalize_client_ip(client_ip)
    with _rate_lock:
        now = time.monotonic()
        hits = _login_failures.setdefault(client_ip, [])
        _prune_hits(hits, LOGIN_FAILED_WINDOW_SEC, now)
        return len(hits) < LOGIN_FAILED_MAX


def record_login_failure(client_ip: str) -> None:
    """Учитывает неудачную попытку POST /api/login."""
    client_ip = normalize_client_ip(client_ip)
    with _rate_lock:
        now = time.monotonic()
        hits = _login_failures.setdefault(client_ip, [])
        _prune_hits(hits, LOGIN_FAILED_WINDOW_SEC, now)
        hits.append(now)


def clear_login_failures(client_ip: str) -> None:
    """Сбрасывает счётчик неудачных входов после успешного логина."""
    client_ip = normalize_client_ip(client_ip)
    with _rate_lock:
        _login_failures.pop(client_ip, None)
