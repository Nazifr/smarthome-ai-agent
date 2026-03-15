"""
ContextEnricher — Dış Bağlam Zenginleştirici

Sensör verisine şunları ekler:
- Hava durumu (OpenWeatherMap API, 30 dk cache)
- Enerji fiyat seviyesi (saate göre sabit tablo)
- Gün tipi (hafta içi / hafta sonu / tatil)
- Kullanıcı duygu durumu (Telegram butonu ile — placeholder şimdilik)
"""

import os
import time
import requests

# ── Ayarlar ───────────────────────────────────────────────────────────
WEATHER_API_KEY  = os.getenv("WEATHER_API_KEY", "")
WEATHER_LAT      = float(os.getenv("WEATHER_LAT", "38.4"))   # İzmir
WEATHER_LON      = float(os.getenv("WEATHER_LON", "27.1"))   # İzmir
WEATHER_CACHE_SEC = 1800  # 30 dakika cache

# Türkiye resmi tatilleri (ay, gün)
TR_HOLIDAYS = {
    (1, 1), (4, 23), (5, 1), (5, 19),
    (7, 15), (8, 30), (10, 29)
}

# Enerji fiyat seviyeleri (saate göre)
# 0=ucuz, 1=normal, 2=pahalı
def get_energy_price(hour: int) -> int:
    if 23 <= hour or hour < 6:
        return 0   # gece ucuz
    elif 17 <= hour < 23:
        return 2   # akşam pik
    else:
        return 1   # gündüz normal

# Hava durumu kodu → sayısal değer
# 0=güneşli, 1=bulutlu, 2=yağmurlu/karlı/fırtınalı
def weather_code_to_int(weather_id: int) -> int:
    if weather_id < 300:      # Thunderstorm
        return 2
    elif weather_id < 600:    # Drizzle + Rain
        return 2
    elif weather_id < 700:    # Snow
        return 2
    elif weather_id < 800:    # Atmosphere (sis, duman)
        return 1
    elif weather_id == 800:   # Clear sky
        return 0
    else:                     # Clouds
        return 1

def weather_code_to_str(weather_id: int) -> str:
    mapping = {0: "güneşli", 1: "bulutlu", 2: "yağmurlu"}
    return mapping[weather_code_to_int(weather_id)]


class ContextEnricher:
    def __init__(self):
        self._weather_cache = None
        self._weather_cache_time = 0
        self._user_sentiment = 0   # 0=nötr, 1=yorgun, 2=aktif, 3=stresli
        self._sentiment_str  = "nötr"

        if not WEATHER_API_KEY:
            print("[ContextEnricher] ⚠️ WEATHER_API_KEY ayarlanmamış, hava durumu devre dışı")
        else:
            print("[ContextEnricher] ✓ Hava durumu API bağlandı")

    # ── Ana Zenginleştirme Fonksiyonu ─────────────────────────────────

    def enrich(self, context: dict) -> dict:
        """
        Mevcut context'e dış bağlam bilgilerini ekler.
        """
        hour       = context.get("hour", 12)
        month      = context.get("month", 1)
        day        = context.get("day", 1)
        is_weekend = context.get("is_weekend", 0)

        # Hava durumu
        weather_data = self._get_weather()
        context["weather"]          = weather_data["code"]        # 0/1/2
        context["weather_str"]      = weather_data["description"] # güneşli/bulutlu/yağmurlu
        context["outdoor_temp"]     = weather_data["temp"]

        # Enerji fiyatı
        context["energy_price"]     = get_energy_price(hour)

        # Gün tipi
        context["is_holiday"]       = 1 if (month, day) in TR_HOLIDAYS else 0
        context["day_type"]         = is_weekend  # 0=hafta içi, 1=hafta sonu

        # Kullanıcı duygu durumu (Telegram butonu ile güncellenir)
        context["sentiment"]        = self._user_sentiment
        context["sentiment_str"]    = self._sentiment_str

        return context

    # ── Hava Durumu ───────────────────────────────────────────────────

    def _get_weather(self) -> dict:
        """
        OpenWeatherMap API'den hava durumu çek.
        30 dakika cache kullan.
        """
        now = time.time()

        # Cache geçerli mi?
        if self._weather_cache and (now - self._weather_cache_time) < WEATHER_CACHE_SEC:
            return self._weather_cache

        # API key yoksa default döndür
        if not WEATHER_API_KEY:
            return {"code": 0, "description": "bilinmiyor", "temp": 20.0}

        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?lat={WEATHER_LAT}&lon={WEATHER_LON}"
                f"&appid={WEATHER_API_KEY}&units=metric"
            )
            response = requests.get(url, timeout=5)
            data     = response.json()

            weather_id  = data["weather"][0]["id"]
            description = data["weather"][0]["description"]
            temp        = data["main"]["temp"]

            result = {
                "code":        weather_code_to_int(weather_id),
                "description": weather_code_to_str(weather_id),
                "temp":        round(temp, 1),
                "raw":         description
            }

            self._weather_cache      = result
            self._weather_cache_time = now
            print(f"[ContextEnricher] Hava durumu güncellendi: {result['description']}, {temp}°C")
            return result

        except Exception as e:
            print(f"[ContextEnricher] Hava durumu hatası: {e}")
            # Cache varsa onu kullan
            if self._weather_cache:
                return self._weather_cache
            return {"code": 0, "description": "bilinmiyor", "temp": 20.0}

    # ── Duygu Durumu Güncelleme ───────────────────────────────────────

    def update_sentiment(self, sentiment: str):
        """
        Telegram bot'tan gelen kullanıcı duygu durumunu güncelle.
        sentiment: 'nötr', 'yorgun', 'aktif', 'stresli'
        """
        mapping = {"nötr": 0, "yorgun": 1, "aktif": 2, "stresli": 3}
        self._user_sentiment = mapping.get(sentiment, 0)
        self._sentiment_str  = sentiment
        print(f"[ContextEnricher] Duygu durumu güncellendi: {sentiment}")
