"""Интеграция: POST /api/login блокируется после 3 неудачных попыток."""

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import rate_limit  # noqa: E402
from rate_limit import LOGIN_RATE_LIMIT_ERROR  # noqa: E402
from server import Handler  # noqa: E402


def test_login_returns_429_after_three_failed_attempts() -> None:
    """Третья неудачная попытка с одного IP получает 429."""
    rate_limit._login_failures.clear()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    try:
        statuses: list[int] = []
        for attempt in range(1, 5):
            payload = json.dumps(
                {"username": "neo", "password": f"wrong-{attempt}"}
            ).encode()
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/login",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                response = urllib.request.urlopen(request, timeout=5)
                statuses.append(response.status)
            except urllib.error.HTTPError as extra:
                statuses.append(extra.code)
                if extra.code == 429:
                    body = json.loads(extra.read().decode("utf-8"))
                    assert body["error"] == LOGIN_RATE_LIMIT_ERROR

        assert statuses[:2] == [401, 401]
        assert statuses[2:] == [429, 429]
    finally:
        server.shutdown()
        thread.join(timeout=2)
        rate_limit._login_failures.clear()
