import pandas as pd
import numpy as np
from datetime import datetime


class ContextAnalyzer:
    """
    Ham sensör verisinden anlamlı bağlam (context) çıkarır.
    Örnek: saat + hareket + sıcaklık → "uyku_bağlamı" veya "evde_aktif"
    """

    def analyze(self, sensor_data: dict) -> dict:
        """
        sensor_data: {
            "temperature": 24.5,
            "humidity": 55.0,
            "motion": 1,         # 0=yok, 1=var
            "light": 300.0,      # lux
            "timestamp": "2025-01-01T23:30:00"
        }
        """
        ts = pd.Timestamp(sensor_data.get("timestamp", datetime.now().isoformat()))

        hour = ts.hour
        minute = ts.minute
        day_of_week = ts.dayofweek  # 0=Pazartesi, 6=Pazar
        is_weekend = int(day_of_week >= 5)

        temperature = float(sensor_data.get("temperature", 22.0))
        humidity = float(sensor_data.get("humidity", 50.0))
        motion = int(sensor_data.get("motion", 0))
        light = float(sensor_data.get("light", 0.0))

        # ── Zaman Dilimi Tespiti ──────────────────────────────────────
        if 0 <= hour < 7:
            time_period = "gece"
        elif 7 <= hour < 12:
            time_period = "sabah"
        elif 12 <= hour < 18:
            time_period = "ogleden_sonra"
        elif 18 <= hour < 23:
            time_period = "aksam"
        else:
            time_period = "gece_geç"

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
            light_level = "loş"
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

        return {
            # Ham feature'lar (ML modeli için sayısal)
            "hour": hour,
            "minute": minute,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "temperature": temperature,
            "humidity": humidity,
            "motion": motion,
            "light": light,

            # İnsan okunabilir bağlam etiketleri
            "time_period": time_period,
            "occupancy": occupancy,
            "thermal_comfort": thermal_comfort,
            "light_level": light_level,
            "context_label": context_label,
        }

    # def to_feature_vector(self, context: dict) -> list:
    #     """
    #     ML modeline girecek sayısal feature vektörünü döndürür.
    #     """
    #     return [
    #         context["hour"],
    #         context["minute"],
    #         context["day_of_week"],
    #         context["is_weekend"],
    #         context["temperature"],
    #         context["humidity"],
    #         context["motion"],
    #         context["light"],
    #     ]
    def to_feature_vector(self, context: dict) -> list:
        """
        ML modeline girecek sayısal feature vektörünü döndürür.
        """
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
            context.get("weather", 0),       # 0=güneşli, 1=bulutlu, 2=yağmurlu
            context.get("sentiment", 0),     # 0=nötr, placeholder
            context.get("energy_price", 1),  # 0=ucuz, 1=normal, 2=pahalı
        ]
