"""Ограничение частоты POST с одного IP."""

import time

POST_WINDOW_SEC = 60.0
POST_MAX_PER_WINDOW = 30

_post_hits: dict[str, list[float]] = {}


def allow_post(client_ip: str) -> bool:
    """True, если с этого IP ещё можно принять POST в текущем окне."""
    now = time.monotonic()
    hits = _post_hits.setdefault(client_ip, [])
    hits[:] = [stamp for stamp in hits if now - stamp < POST_WINDOW_SEC]
    if len(hits) >= POST_MAX_PER_WINDOW:
        return False
    hits.append(now)
    return True
