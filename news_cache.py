"""In-memory кэш ленты новостей для GET /api/news."""

import logging
import threading
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

NEWS_CACHE_TTL_SEC = 30.0
news_cache: dict[str, object] = {
    "data": None,
    "timestamp": 0.0,
}
_cache_lock = threading.Lock()


def get_cached_news(
    loader: Callable[[], list[dict[str, str | int]]],
) -> list[dict[str, str | int]]:
    """Отдаёт новости из кэша, если они младше TTL, иначе вызывает loader."""
    with _cache_lock:
        now = time.time()
        cached_data = news_cache["data"]
        cached_ts = news_cache["timestamp"]
        if (
            isinstance(cached_data, list)
            and isinstance(cached_ts, (int, float))
            and now - float(cached_ts) < NEWS_CACHE_TTL_SEC
        ):
            logger.info(
                "Новости: кэш HIT, возраст %.1f с",
                now - float(cached_ts),
            )
            return cached_data

        logger.info("Новости: кэш MISS, загрузка ленты")
        articles = loader()
        news_cache["data"] = articles
        news_cache["timestamp"] = time.time()
        return articles
