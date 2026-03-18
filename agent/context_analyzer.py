import pandas as pd
import numpy as np
from datetime import datetime


def _heat_index(temp_c: float, humidity: float) -> float:
    if temp_c < 27:
        return temp_c
    T, R = temp_c, humidity
    hi = (-8.78469475556 + 1.61139411*T + 2.33854883889*R
          - 0.14611605*T*R - 0.012308094*T**2
          - 0.0164248277778*R**2 + 0.002211732*T**2*R
          + 0.00072546*T*R**2 - 0.000003582*T**2*R**2)
    return round(hi, 1)

def _ac_need_score(temp_diff: float, heat_idx: float, solar_kw: float) -> float:
    score = 0.0
    if temp_diff > 3:    score += 0.4
    elif temp_diff < -3: score -= 0.3
    if heat_idx > 35:    score += 0.4
    elif heat_idx > 30:  score += 0.2
    if solar_kw > 2.0:   score += 0.2
    return max(0.0, min(1.0, score))


class ContextAnalyzer:
    """
    Ham sensör verisinden anlamlı bağlam (context) çıkarır.
    """

    def analyze(self, sensor_data: dict) -> dict:
        ts = pd.Timestamp(sensor_data.get("timestamp", datetime.now().isoformat()))

        hour        = ts.hour
        minute      = ts.minute
        day_of_week = ts.dayofweek
        is_weekend  = int(day_of_week >= 5)

        temperature = float(sensor_data.get("temperature", 22.0))
        humidity    = float(sensor_data.get("humidity", 50.0))
        motion      = int(sensor_data.get("motion", 0))
        light       = float(sensor_data.get("light", 0.0))

        # ── Zaman Dilimi ──────────────────────────────────────────────
        if 0 <= hour < 6:
            time_period = "gece";      time_of_day = 0
        elif 6 <= hour < 12:
            time_period = "sabah";     time_of_day = 1
        elif 12 <= hour < 18:
            time_period = "ogleden_sonra"; time_of_day = 2
        else:
            time_period = "aksam";     time_of_day = 3

        # ── Doluluk ───────────────────────────────────────────────────
        occupancy = "dolu" if motion == 1 else "bos"

        # ── Sıcaklık Konforu ─────────────────────────────────────────
        if temperature < 18:      thermal_comfort = "soguk"
        elif temperature <= 26:   thermal_comfort = "konforlu"
        else:                     thermal_comfort = "sicak"

        # ── Işık Durumu ───────────────────────────────────────────────
        if light < 50:       light_level = "karanlik"
        elif light < 300:    light_level = "los"
        else:                light_level = "aydinlik"

        # ── Bağlam Etiketi ────────────────────────────────────────────
        if time_period == "gece" and occupancy == "bos":
            context_label = "uyku"
        elif time_period in ["sabah", "ogleden_sonra"] and occupancy == "dolu":
            context_label = "aktif_ev"
        elif occupancy == "bos":
            context_label = "bos_ev"
        elif time_period == "aksam" and occupancy == "dolu":
            context_label = "aksam_rutini"
        else:
            context_label = "genel"

        # ── Türetilmiş Feature'lar ────────────────────────────────────
        temp_hour_interaction = temperature * hour / 24.0
        solar_kw              = light / 500.0
        use_kw_rolling        = solar_kw  # proxy

        # İç/dış sıcaklık farkı — outdoor_temp enricher'dan gelir
        # Burada placeholder, enrich() sonrası güncellenecek
        outdoor_temp_est = temperature - (solar_kw * 2.0)
        temp_diff        = round(temperature - outdoor_temp_est, 1)

        # Hissedilen sıcaklık
        hi = _heat_index(temperature, humidity)

        # AC ihtiyaç skoru
        ac_score = _ac_need_score(temp_diff, hi, solar_kw)

        return {
            "hour":                   hour,
            "minute":                 minute,
            "day_of_week":            day_of_week,
            "is_weekend":             is_weekend,
            "temperature":            temperature,
            "humidity":               humidity,
            "motion":                 motion,
            "light":                  light,
            "temp_hour_interaction":  temp_hour_interaction,
            "use_kw_rolling":         use_kw_rolling,
            "time_of_day":            time_of_day,
            "temp_diff":              temp_diff,
            "heat_index":             hi,
            "ac_need_score":          ac_score,
            "time_period":            time_period,
            "occupancy":              occupancy,
            "thermal_comfort":        thermal_comfort,
            "light_level":            light_level,
            "context_label":          context_label,
        }

    def to_feature_vector(self, context: dict) -> list:
        """
        ML modeline girecek 18 feature.
        Sıra train_model.py'deki features listesiyle birebir aynı:
        hour, minute, day_of_week, is_weekend, day_type,
        temperature, humidity, motion, light,
        weather, sentiment, energy_price,
        temp_hour_interaction, use_kw_rolling, time_of_day,
        temp_diff, heat_index, ac_need_score
        """
        # Enricher'dan outdoor_temp geldiyse temp_diff'i güncelle
        outdoor_temp = context.get("outdoor_temp", None)
        if outdoor_temp is not None:
            temp_diff = round(context["temperature"] - outdoor_temp, 1)
            solar_kw  = context["light"] / 500.0
            hi        = _heat_index(context["temperature"], context["humidity"])
            ac_score  = _ac_need_score(temp_diff, hi, solar_kw)
        else:
            temp_diff = context.get("temp_diff", 0.0)
            hi        = context.get("heat_index", context["temperature"])
            ac_score  = context.get("ac_need_score", 0.0)

        return [
            context["hour"],
            context["minute"],
            context["day_of_week"],
            context["is_weekend"],
            context.get("day_type", context["is_weekend"]),
            context["temperature"],
            context["humidity"],
            context["motion"],
            context["light"],
            context.get("weather", 0),
            context.get("sentiment", 0),
            context.get("energy_price", 1),
            context["temp_hour_interaction"],
            context["use_kw_rolling"],
            context["time_of_day"],
            temp_diff,
            hi,
            ac_score,
        ]
