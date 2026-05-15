"""
Weather service using Open-Meteo (free, no API key required).
Caches results for 10 minutes to avoid hammering the API.
"""

import time
import urllib.request
import json

# Default: Izmir, Turkey 
LATITUDE = 38.3692
LONGITUDE = 27.2096

_cache = {"data": None, "expires": 0}
CACHE_TTL = 600  # 10 minutes

WMO_CODES = {
    0: "Clear sky",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Light snow showers",
    86: "Snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm + hail",
    99: "Thunderstorm + heavy hail",
}


def get_weather():
    """Fetch current weather from Open-Meteo. Returns cached data if fresh."""
    now = time.time()

    if _cache["data"] and now < _cache["expires"]:
        return _cache["data"]

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={LATITUDE}&longitude={LONGITUDE}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,rain"
            f"&timezone=auto"
        )

        req = urllib.request.Request(url, headers={"User-Agent": "NeuroNest/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = json.loads(resp.read().decode())

        current = raw.get("current", {})
        code = current.get("weather_code", 0)
        temp = current.get("temperature_2m")
        wind = current.get("wind_speed_10m", 0)
        rain = current.get("rain", 0)

        window_safe = (rain or 0) < 0.5 and (wind or 0) < 30 and 10 <= (temp or 20) <= 35

        result = {
            "temperature": temp,
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": wind,
            "rain": rain,
            "condition": WMO_CODES.get(code, "Unknown"),
            "weather_code": code,
            "window_safe": window_safe,
            "available": True,
        }

        _cache["data"] = result
        _cache["expires"] = now + CACHE_TTL
        return result

    except Exception as e:
        print(f"[Weather] Failed to fetch: {e}")
        if _cache["data"]:
            return _cache["data"]  # stale cache better than nothing
        return {
            "temperature": None,
            "humidity": None,
            "wind_speed": None,
            "condition": "Unavailable",
            "weather_code": None,
            "available": False,
        }
