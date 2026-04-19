"""
Sensör Simülatörü

Gerçek bir dataset yokken bile sistemi test edebilmek için
rastgele ama mantıklı sensör verisi üretir.
İleride gerçek dataset (CASAS/UCI) ile değiştirilebilir.
"""

import os
import json
import time
import random
import math
from datetime import datetime

import paho.mqtt.client as mqtt
# import sys
# sys.stdout.flush()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", 1883))
INTERVAL    = float(os.getenv("PUBLISH_INTERVAL", 5))  # saniye

ROOMS = ["living_room", "bedroom", "kitchen", "bathroom"]


def realistic_temperature(hour: int) -> float:
    """Saate göre gerçekçi iç mekan sıcaklığı üretir."""
    base = 22.0
    # Gece soğur, öğleden sonra ısınır
    daily_variation = -3 * math.cos(2 * math.pi * (hour - 14) / 24)
    noise = random.gauss(0, 0.5)
    return round(base + daily_variation + noise, 1)


def realistic_motion(hour: int) -> int:
    """Saate göre hareket olasılığı."""
    # Gece yarısı - sabah 6: düşük hareket
    if 0 <= hour < 6:
        return 1 if random.random() < 0.05 else 0
    # Sabah 7-9: yüksek (hazırlık)
    elif 7 <= hour < 9:
        return 1 if random.random() < 0.8 else 0
    # İş saatleri: düşük (ev boş)
    elif 9 <= hour < 17:
        return 1 if random.random() < 0.15 else 0
    # Akşam: yüksek
    elif 17 <= hour < 23:
        return 1 if random.random() < 0.75 else 0
    else:
        return 1 if random.random() < 0.1 else 0


def realistic_light(hour: int) -> float:
    """Doğal ışık + yapay ışık simülasyonu."""
    # Gündüz doğal ışık
    if 7 <= hour < 19:
        natural = 200 + 300 * math.sin(math.pi * (hour - 7) / 12)
    else:
        natural = 0.0

    # Akşam yapay ışık
    artificial = 150 if (17 <= hour < 23) else 0

    noise = random.gauss(0, 20)
    return round(max(0, natural + artificial + noise), 1)


def generate_sensor_data(room: str) -> dict:
    now = datetime.now()
    hour = now.hour

    return {
        "temperature": realistic_temperature(hour),
        "humidity":    round(random.gauss(55, 8), 1),
        "motion":      realistic_motion(hour),
        "light":       realistic_light(hour),
        "timestamp":   now.isoformat(),
        "room":        room,
    }


def main():
    client = mqtt.Client(client_id="smarthome-simulator")

    print(f"[Simulator] Broker'a bağlanılıyor: {MQTT_BROKER}:{MQTT_PORT}")
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            break
        except Exception as e:
            print(f"[Simulator] Bağlantı bekleniyor... ({e})")
            # INTERVAL = int(os.getenv("SENSOR_INTERVAL", "30"))
            time.sleep(INTERVAL)

    client.loop_start()
    print(f"[Simulator] Başladı — her {INTERVAL} saniyede veri yayınlanıyor")

    while True:
        for room in ROOMS:
            data = generate_sensor_data(room)
            topic = f"home/{room}/sensor/all"
            client.publish(topic, json.dumps(data))
            print(f"[Simulator] {room}: "
                  f"🌡️{data['temperature']}°C  "
                  f"💧{data['humidity']}%  "
                  f"🏃{'Evet' if data['motion'] else 'Hayır'}  "
                  f"💡{data['light']} lux")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
