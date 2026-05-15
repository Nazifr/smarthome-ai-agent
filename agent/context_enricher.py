"""
ContextEnricher — Dış Bağlam Zenginleştirici

Sensör verisine şunları ekler:
- Hava durumu (OpenWeatherMap API, 30 dk cache)
- İç/dış sıcaklık farkı
- Nem konforu (hissedilen sıcaklık)
- Güneş ısısı etkisi
- Enerji fiyat seviyesi
- Gün tipi (hafta içi / hafta sonu / tatil)
- Kullanıcı duygu durumu (Telegram butonu ile)
"""

import os
import time
import math
import requests

WEATHER_API_KEY   = os.getenv("WEATHER_API_KEY", "")
WEATHER_LAT       = float(os.getenv("WEATHER_LAT", "38.4"))
WEATHER_LON       = float(os.getenv("WEATHER_LON", "27.1"))
WEATHER_CACHE_SEC = 1800  # 30 dakika cache

# Open-Meteo WMO weather codes → simplified categories
def _wmo_to_int(code: int) -> int:
    if code <= 3:   return 0   # clear / partly cloudy
    if code <= 48:  return 1   # fog
    if code <= 67:  return 2   # drizzle / rain
    if code <= 77:  return 2   # snow
    if code <= 82:  return 2   # rain showers
    if code <= 86:  return 2   # snow showers
    return 2                   # thunderstorm

def _wmo_to_str(code: int) -> str:
    if code <= 3:   return "güneşli"
    if code <= 48:  return "bulutlu"
    if code <= 67:  return "yağmurlu"
    if code <= 77:  return "karlı"
    if code <= 82:  return "yağmurlu"
    return "fırtınalı"

TR_HOLIDAYS = {
    (1, 1), (4, 23), (5, 1), (5, 19),
    (7, 15), (8, 30), (10, 29)
}

def get_energy_price(hour: int) -> int:
    if 23 <= hour or hour < 6:    return 0   # gece ucuz
    elif 17 <= hour < 23:         return 2   # akşam pik
    else:                         return 1   # gündüz normal

def weather_code_to_int(weather_id: int) -> int:
    if weather_id < 300:    return 2   # fırtına
    elif weather_id < 600:  return 2   # yağmur
    elif weather_id < 700:  return 2   # kar
    elif weather_id < 800:  return 1   # sis
    elif weather_id == 800: return 0   # açık
    else:                   return 1   # bulutlu

def weather_code_to_str(weather_id: int) -> str:
    return {0: "güneşli", 1: "bulutlu", 2: "yağmurlu"}[weather_code_to_int(weather_id)]

def heat_index(temp_c: float, humidity: float) -> float:
    """
    Hissedilen sıcaklık hesabı (Steadman formülü).
    Sıcaklık + nem kombinasyonunun vücut üzerindeki etkisi.
    """
    if temp_c < 27:
        return temp_c  # düşük sıcaklıkta heat index anlamlı değil
    T = temp_c
    R = humidity
    hi = (-8.78469475556 +
           1.61139411 * T +
           2.33854883889 * R +
          -0.14611605 * T * R +
          -0.012308094 * T**2 +
          -0.0164248277778 * R**2 +
           0.002211732 * T**2 * R +
           0.00072546 * T * R**2 +
          -0.000003582 * T**2 * R**2)
    return round(hi, 1)

def ac_need_score(temp_diff: float, heat_idx: float, solar_kw: float) -> float:
    """
    AC'ye ne kadar ihtiyaç var? 0=hiç, 1=kesinlikle gerek.
    Üç faktörü birleştirir:
    - İç/dış sıcaklık farkı (pozitifse ev dışarıdan sıcak)
    - Hissedilen sıcaklık
    - Güneş ısısı (solar kW)
    """
    score = 0.0
    # Ev dışarıdan sıcaksa AC yerine pencere yeterli
    if temp_diff > 3:    score += 0.4   # ev çok sıcak, AC gerekli
    elif temp_diff < -3: score -= 0.3   # dışarısı sıcak, pencere yeterli
    # Hissedilen sıcaklık
    if heat_idx > 35:    score += 0.4
    elif heat_idx > 30:  score += 0.2
    # Güneş ısısı
    if solar_kw > 2.0:   score += 0.2
    return max(0.0, min(1.0, score))


class ContextEnricher:
    def __init__(self):
        self._weather_cache      = None
        self._weather_cache_time = 0
        self._user_sentiment     = 0
        self._sentiment_str      = "nötr"

        if not WEATHER_API_KEY:
            print("[ContextEnricher] ⚠️ WEATHER_API_KEY ayarlanmamış, hava durumu devre dışı")
        else:
            print("[ContextEnricher] ✓ Hava durumu API bağlandı")

    def enrich(self, context: dict) -> dict:
        hour       = context.get("hour", 12)
        month      = context.get("month", 1)
        day        = context.get("day", 1)
        is_weekend = context.get("is_weekend", 0)
        indoor_temp = context.get("temperature", 22.0)
        humidity    = context.get("humidity", 50.0)
        solar_kw    = context.get("light", 0.0) / 500.0  # light → solar proxy

        # Hava durumu (Open-Meteo first, OpenWeatherMap fallback)
        weather_data = self._get_weather()
        outdoor_temp = weather_data["temp"]
        context["weather"]      = weather_data["code"]
        context["weather_str"]  = weather_data["description"]
        context["outdoor_temp"] = outdoor_temp
        context["rain_mm"]      = weather_data.get("rain", 0.0)
        context["wind_kmh"]     = weather_data.get("wind", 0.0)

        # Window safety: no rain, wind < 30 km/h, outdoor temp 10–35°C
        context["is_window_safe"] = (
            weather_data.get("rain", 0.0) < 0.5
            and weather_data.get("wind", 0.0) < 30
            and 10 <= outdoor_temp <= 35
        )

        # İç/dış sıcaklık farkı
        temp_diff = round(indoor_temp - outdoor_temp, 1)
        context["temp_diff"] = temp_diff

        # Nem konforu — hissedilen sıcaklık
        hi = heat_index(indoor_temp, humidity)
        context["heat_index"] = hi

        # AC ihtiyaç skoru (0-1)
        context["ac_need_score"] = ac_need_score(temp_diff, hi, solar_kw)

        # Enerji fiyatı
        context["energy_price"] = get_energy_price(hour)

        # Gün tipi
        context["is_holiday"] = 1 if (month, day) in TR_HOLIDAYS else 0
        context["day_type"]   = is_weekend

        # Duygu durumu
        context["sentiment"]     = self._user_sentiment
        context["sentiment_str"] = self._sentiment_str

        return context

    def _get_weather(self) -> dict:
        now = time.time()
        if self._weather_cache and (now - self._weather_cache_time) < WEATHER_CACHE_SEC:
            return self._weather_cache

        result = self._get_weather_openmeteo()
        if not result and WEATHER_API_KEY:
            result = self._get_weather_owm()
        if not result:
            return self._weather_cache or {
                "code": 0, "description": "bilinmiyor", "temp": 20.0,
                "rain": 0.0, "wind": 0.0,
            }

        self._weather_cache      = result
        self._weather_cache_time = now
        print(f"[ContextEnricher] Hava durumu güncellendi: {result['description']}, "
              f"{result['temp']}°C, rain={result.get('rain', 0)}mm, wind={result.get('wind', 0)}km/h")
        return result

    def _get_weather_openmeteo(self) -> dict | None:
        """Open-Meteo: free, no API key, includes rain + wind."""
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={WEATHER_LAT}&longitude={WEATHER_LON}"
                f"&current=temperature_2m,relative_humidity_2m,rain,wind_speed_10m,weather_code"
            )
            data = requests.get(url, timeout=5).json()["current"]
            wmo  = int(data["weather_code"])
            return {
                "code":        _wmo_to_int(wmo),
                "description": _wmo_to_str(wmo),
                "temp":        round(data["temperature_2m"], 1),
                "rain":        round(data.get("rain", 0.0), 1),
                "wind":        round(data.get("wind_speed_10m", 0.0), 1),
            }
        except Exception as e:
            print(f"[ContextEnricher] Open-Meteo hatası: {e}")
            return None

    def _get_weather_owm(self) -> dict | None:
        """OpenWeatherMap fallback (requires API key)."""
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?lat={WEATHER_LAT}&lon={WEATHER_LON}"
                f"&appid={WEATHER_API_KEY}&units=metric"
            )
            data       = requests.get(url, timeout=5).json()
            weather_id = data["weather"][0]["id"]
            temp       = data["main"]["temp"]
            wind       = data.get("wind", {}).get("speed", 0) * 3.6  # m/s → km/h
            rain       = data.get("rain", {}).get("1h", 0.0)
            return {
                "code":        weather_code_to_int(weather_id),
                "description": weather_code_to_str(weather_id),
                "temp":        round(temp, 1),
                "rain":        round(rain, 1),
                "wind":        round(wind, 1),
            }
        except Exception as e:
            print(f"[ContextEnricher] OpenWeatherMap hatası: {e}")
            return None

    def update_sentiment(self, sentiment: str):
        mapping = {"nötr": 0, "yorgun": 1, "aktif": 2, "stresli": 3,
                   "notr": 0}  # ASCII fallback
        self._user_sentiment = mapping.get(sentiment, 0)
        self._sentiment_str  = sentiment
        print(f"[ContextEnricher] Duygu durumu güncellendi: {sentiment}")
