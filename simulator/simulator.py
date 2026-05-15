import os
import json
import time
import random
import math
from datetime import datetime
import paho.mqtt.client as mqtt

MQTT_BROKER   = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT     = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER     = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TLS      = os.getenv("MQTT_TLS", "false").lower() == "true"
MQTT_CA_CERT  = os.getenv("MQTT_CA_CERT", "/etc/smarthome/certs/ca.crt")
INTERVAL      = float(os.getenv("PUBLISH_INTERVAL", 15))

ROOMS = ["living_room", "bedroom", "kitchen", "bathroom", "hallway", "office"]

# Each room has its own base temperature and humidity profile
ROOM_PROFILES = {
    "living_room": {"temp_base": 21.5, "temp_noise": 0.6, "humidity_mean": 52, "humidity_std": 7},
    "bedroom":     {"temp_base": 20.0, "temp_noise": 0.5, "humidity_mean": 48, "humidity_std": 6},
    "kitchen":     {"temp_base": 23.5, "temp_noise": 1.2, "humidity_mean": 58, "humidity_std": 9},
    "bathroom":    {"temp_base": 24.0, "temp_noise": 0.8, "humidity_mean": 75, "humidity_std": 10},
    "hallway":     {"temp_base": 19.5, "temp_noise": 0.4, "humidity_mean": 45, "humidity_std": 6},
    "office":      {"temp_base": 22.0, "temp_noise": 0.6, "humidity_mean": 50, "humidity_std": 7},
}

def realistic_temperature(hour, room):
    profile = ROOM_PROFILES.get(room, {"temp_base": 22.0, "temp_noise": 0.5})
    base = profile["temp_base"]
    # Daytime warming peaks at 14:00, cools overnight — amplitude varies by room
    daily_variation = -2.5 * math.cos(2 * math.pi * (hour - 14) / 24)
    return round(base + daily_variation + random.gauss(0, profile["temp_noise"]), 1)

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
    profile = ROOM_PROFILES.get(room, {"humidity_mean": 55, "humidity_std": 8})
    return {
        "temperature": realistic_temperature(now.hour, room),
        "humidity":    round(max(20, min(100, random.gauss(profile["humidity_mean"], profile["humidity_std"]))), 1),
        "motion":      realistic_motion(now.hour),
        "smoke":       0,
        "light":       realistic_light(now.hour),
        "timestamp":   now.isoformat(),
        "room":        room,
    }

def main():
    client = mqtt.Client(client_id="smarthome-simulator")
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    if MQTT_TLS:
        client.tls_set(ca_certs=MQTT_CA_CERT)

    print(f"[Simulator] Broker'a bağlanılıyor: {MQTT_BROKER}:{MQTT_PORT} (TLS={MQTT_TLS})")
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
