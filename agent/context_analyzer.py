import pandas as pd
import numpy as np
from datetime import datetime


class ContextAnalyzer:
    """
    Ham sensör verisinden anlamlı bağlam (context) çıkarır.
    Örnek: saat + hareket + sıcaklık → "uyku_bağlamı" veya "evde_aktif"
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

        # ── Zaman Dilimi Tespiti ──────────────────────────────────────
        if 0 <= hour < 6:
            time_period  = "gece"
            time_of_day  = 0
        elif 6 <= hour < 12:
            time_period  = "sabah"
            time_of_day  = 1
        elif 12 <= hour < 18:
            time_period  = "ogleden_sonra"
            time_of_day  = 2
        else:
            time_period  = "aksam"
            time_of_day  = 3

        # ── Doluluk Tespiti ───────────────────────────────────────────
        occupancy = "dolu" if motion == 1 else "bos"

        # ── Sıcaklık Konforu ─────────────────────────────────────────
        if temperature < 18:
            thermal_comfort = "soguk"
        elif temperature <= 26:
            thermal_comfort = "konforlu"
        else:
            thermal_comfort = "sicak"

        # ── Işık Durumu ───────────────────────────────────────────────
        if light < 50:
            light_level = "karanlik"
        elif light < 300:
            light_level = "los"
        else:
            light_level = "aydinlik"

        # ── Ana Bağlam Etiketi ────────────────────────────────────────
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

        # ── Yeni Feature'lar ──────────────────────────────────────────
        # Sıcaklık × saat etkileşimi (train_model.py ile aynı formül)
        temp_hour_interaction = temperature * hour / 24.0

        # Enerji tüketim trendi — sensörden gerçek kW yok,
        # light değerini proxy olarak kullan (normalize edilmiş)
        use_kw_rolling = light / 500.0

        return {
            # Ham feature'lar (ML modeli için sayısal)
            "hour":                   hour,
            "minute":                 minute,
            "day_of_week":            day_of_week,
            "is_weekend":             is_weekend,
            "temperature":            temperature,
            "humidity":               humidity,
            "motion":                 motion,
            "light":                  light,

            # Yeni feature'lar
            "temp_hour_interaction":  temp_hour_interaction,
            "use_kw_rolling":         use_kw_rolling,
            "time_of_day":            time_of_day,

            # İnsan okunabilir bağlam etiketleri
            "time_period":            time_period,
            "occupancy":              occupancy,
            "thermal_comfort":        thermal_comfort,
            "light_level":            light_level,
            "context_label":          context_label,
        }

    def to_feature_vector(self, context: dict) -> list:
        """
        ML modeline girecek sayısal feature vektörünü döndürür.
        Sıra train_model.py'deki features listesiyle birebir aynı olmalı:
        hour, minute, day_of_week, is_weekend, day_type,
        temperature, humidity, motion, light,
        weather, sentiment, energy_price,
        temp_hour_interaction, use_kw_rolling, time_of_day
        """
        return [
            context["hour"],
            context["minute"],
            context["day_of_week"],
            context["is_weekend"],
            context.get("day_type", context["is_weekend"]),   # enricher ekler
            context["temperature"],
            context["humidity"],
            context["motion"],
            context["light"],
            context.get("weather", 0),                        # enricher ekler
            context.get("sentiment", 0),                      # enricher ekler
            context.get("energy_price", 1),                   # enricher ekler
            context["temp_hour_interaction"],
            context["use_kw_rolling"],
            context["time_of_day"],
        ]
