import os
import json
import time
import random
import math
from datetime import datetime
import paho.mqtt.client as mqtt

MQTT_BROKER  = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT    = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER    = os.getenv("MQTT_USER", "")
MQTT_PASSWORD= os.getenv("MQTT_PASSWORD", "")
INTERVAL     = float(os.getenv("PUBLISH_INTERVAL", 30))

ROOMS = ["living_room", "bedroom", "kitchen", "bathroom"]

def realistic_temperature(hour):
    base = 22.0
    daily_variation = -3 * math.cos(2 * math.pi * (hour - 14) / 24)
    return round(base + daily_variation + random.gauss(0, 0.5), 1)

def realistic_motion(hour):
    if 0 <= hour < 6:    return 1 if random.random() < 0.05 else 0
    elif 7 <= hour < 9:  return 1 if random.random() < 0.8  else 0
    elif 9 <= hour < 17: return 1 if random.random() < 0.15 else 0
    elif 17 <= hour < 23:return 1 if random.random() < 0.75 else 0
    else:                return 1 if random.random() < 0.1  else 0

def realistic_light(hour):
    natural    = (200 + 300 * math.sin(math.pi * (hour - 7) / 12)) if 7 <= hour < 19 else 0.0
    artificial = 150 if 17 <= hour < 23 else 0
    return round(max(0, natural + artificial + random.gauss(0, 20)), 1)

def generate_sensor_data(room):
    now = datetime.now()
    return {
        "temperature": realistic_temperature(now.hour),
        "humidity":    round(random.gauss(55, 8), 1),
        "motion":      realistic_motion(now.hour),
        "light":       realistic_light(now.hour),
        "timestamp":   now.isoformat(),
        "room":        room,
    }

def main():
    client = mqtt.Client(client_id="smarthome-simulator")
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    print(f"[Simulator] Broker'a bağlanılıyor: {MQTT_BROKER}:{MQTT_PORT}")
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            break
        except Exception as e:
            print(f"[Simulator] Bağlantı bekleniyor... ({e})")
            time.sleep(5)

    client.loop_start()
    print(f"[Simulator] Başladı — her {INTERVAL} saniyede veri yayınlanıyor")

    while True:
        for room in ROOMS:
            data = generate_sensor_data(room)
            client.publish(f"home/{room}/sensor/all", json.dumps(data))
            print(f"[Simulator] {room}: 🌡️{data['temperature']}°C  💧{data['humidity']}%  "
                  f"🏃{'Evet' if data['motion'] else 'Hayır'}  💡{data['light']} lux")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
