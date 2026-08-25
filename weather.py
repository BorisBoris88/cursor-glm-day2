#!/usr/bin/env python3
"""Получение текущей погоды в Москве через Open-Meteo API."""

import json
import logging
import sys
import time
import urllib.error
import urllib.request

from logging_config import setup_logging

logger = logging.getLogger(__name__)

_CACHE_TTL_SEC = 60.0
_weather_cache: tuple[float, dict[str, object]] | None = None

# Координаты Москвы
MOSCOW_LAT = 55.7558
MOSCOW_LON = 37.6173

API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={MOSCOW_LAT}&longitude={MOSCOW_LON}"
    "&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
    "precipitation,weather_code,wind_speed_10m"
    "&timezone=Europe%2FMoscow"
)

# Коды погоды WMO (упрощённо)
WEATHER_DESCRIPTIONS: dict[int, str] = {
    0: "ясно",
    1: "преимущественно ясно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман",
    48: "изморозь",
    51: "морось: слабая",
    53: "морось: умеренная",
    55: "морось: сильная",
    61: "дождь: слабый",
    63: "дождь: умеренный",
    65: "дождь: сильный",
    71: "снег: слабый",
    73: "снег: умеренный",
    75: "снег: сильный",
    77: "снежная крупа",
    80: "ливень: слабый",
    81: "ливень: умеренный",
    82: "ливень: сильный",
    85: "снегопад: слабый",
    86: "снегопад: сильный",
    95: "гроза",
    96: "гроза с градом",
    99: "гроза с сильным градом",
}


def fetch_weather() -> dict[str, object]:
    """Запрашивает текущую погоду в Москве (кэш 60 с)."""
    global _weather_cache
    now = time.monotonic()
    if _weather_cache is not None:
        cached_at, payload = _weather_cache
        if now - cached_at < _CACHE_TTL_SEC:
            return payload

    request = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "moscow-weather-script/1.0"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("Некорректный ответ Open-Meteo")
    _weather_cache = (now, data)
    return data


def current_weather_snapshot() -> dict[str, float | int]:
    """Температура и код погоды для виджета на сайте."""
    data = fetch_weather()
    current = data["current"]
    if not isinstance(current, dict):
        raise KeyError("current")
    return {
        "temperature": float(current["temperature_2m"]),
        "weather_code": int(current["weather_code"]),
    }


def describe_weather(code: int) -> str:
    """Возвращает текстовое описание по коду WMO."""
    return WEATHER_DESCRIPTIONS.get(code, f"неизвестно (код {code})")


def format_weather(data: dict) -> str:
    """Форматирует данные о погоде для вывода."""
    current = data["current"]
    code = int(current["weather_code"])
    description = describe_weather(code)

    lines = [
        "Погода в Москве",
        "-" * 30,
        f"Описание:        {description}",
        f"Температура:     {current['temperature_2m']:.1f} °C",
        f"Ощущается как:   {current['apparent_temperature']:.1f} °C",
        f"Влажность:       {current['relative_humidity_2m']}%",
        f"Осадки:          {current['precipitation']:.1f} мм",
        f"Ветер:           {current['wind_speed_10m']:.1f} км/ч",
        f"Время замера:    {current['time']}",
    ]
    return "\n".join(lines)


def main() -> int:
    setup_logging()
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

        data = fetch_weather()
        logger.info("%s", format_weather(data))
        return 0
    except urllib.error.URLError:
        logger.exception("Ошибка сети")
        return 1
    except (KeyError, json.JSONDecodeError):
        logger.exception("Ошибка разбора ответа API")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
