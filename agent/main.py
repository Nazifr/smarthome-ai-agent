import os
import json
import time
import threading
from datetime import datetime
from context_enricher import ContextEnricher

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from context_analyzer import ContextAnalyzer
from decision_engine import DecisionEngine
from policy_manager import PolicyManager

MQTT_BROKER   = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT     = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER     = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TLS      = os.getenv("MQTT_TLS", "false").lower() == "true"
MQTT_CA_CERT  = os.getenv("MQTT_CA_CERT", "/etc/smarthome/certs/ca.crt")
INFLUX_URL   = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "smarthome-super-secret-token")
INFLUX_ORG   = os.getenv("INFLUX_ORG", "smarthome")
INFLUX_BUCKET= os.getenv("INFLUX_BUCKET", "sensor_data")

TOPIC_SENSOR_ALL = "home/+/sensor/+"
TOPIC_CMD_PREFIX = "home"
TOPIC_FEEDBACK   = "home/+/feedback"
TOPIC_PREFERENCES= "home/preferences"
TOPIC_ALERT      = "home/alerts"
TOPIC_SENTIMENT  = "home/user/sentiment"
TOPIC_SYSTEM_MODE= "home/system/mode"
TOPIC_SYSTEM_DEMO= "home/system/demo"

SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"

ROOM_ACTUATORS = {
    "living_room": {"light", "lights", "ac", "fan"},
    "bedroom": {"light", "lights", "ac", "fan"},
    "kitchen": {"light", "lights", "fan"},
    "bathroom": {"light", "lights", "fan"},
    "hallway": {"light", "lights"},
    "office": {"light", "lights", "ac", "fan"},
}

# ── Mood-based home configuration ─────────────────────────────────────────────
# Maps user sentiment (from Telegram /mood) to per-room device states.
# Used only in the "fair_arriving" demo scenario.
MOOD_ROOM_CONFIGS: dict[str, dict[str, dict[str, str]]] = {
    "notr": {                            # 😊 Feeling good — cosy evening
        "living_room": {"lights": "ON",  "ac": "COOL_LOW", "fan": "OFF"},
        "bedroom":     {"lights": "DIM", "ac": "COOL_LOW", "fan": "OFF"},
        "kitchen":     {"lights": "ON"},
        "hallway":     {"lights": "ON"},
        "office":      {"lights": "OFF", "ac": "OFF",      "fan": "OFF"},
        "bathroom":    {"lights": "OFF"},
    },
    "yorgun": {                          # 😴 Tired — relaxation mode
        "living_room": {"lights": "DIM", "ac": "COOL_LOW", "fan": "OFF"},
        "bedroom":     {"lights": "DIM", "ac": "COOL_LOW", "fan": "OFF"},
        "kitchen":     {"lights": "DIM"},
        "hallway":     {"lights": "DIM"},
        "office":      {"lights": "OFF", "ac": "OFF",      "fan": "OFF"},
        "bathroom":    {"lights": "OFF"},
    },
    "aktif": {                           # 🏃 Active — energy mode
        "living_room": {"lights": "ON",  "ac": "COOL_HIGH", "fan": "ON"},
        "bedroom":     {"lights": "ON",  "ac": "COOL_LOW",  "fan": "OFF"},
        "kitchen":     {"lights": "ON"},
        "hallway":     {"lights": "ON"},
        "office":      {"lights": "ON",  "ac": "COOL_LOW",  "fan": "ON"},
        "bathroom":    {"lights": "ON"},
    },
    "stresli": {                         # 😤 Stressed — calm-down mode
        "living_room": {"lights": "DIM", "ac": "COOL_LOW", "fan": "OFF"},
        "bedroom":     {"lights": "DIM", "ac": "COOL_LOW", "fan": "OFF"},
        "kitchen":     {"lights": "DIM"},
        "hallway":     {"lights": "DIM"},
        "office":      {"lights": "OFF", "ac": "OFF",      "fan": "OFF"},
        "bathroom":    {"lights": "OFF"},
    },
}

MOOD_MESSAGES: dict[str, str] = {
    "notr":    "😊 Welcome home! Setting up a cosy evening — lights on, AC running.",
    "yorgun":  "😴 Welcome home! Dimming the lights and setting a comfortable temperature. Rest well.",
    "aktif":   "🏃 Welcome home! Energising the house for an active evening!",
    "stresli": "😤 Welcome home. Creating a calm environment to help you unwind.",
}


class SmartHomeAgent:
    def __init__(self):
        self._last_context = {}
        self._system_mode  = "AI"   # "AI" | "Static" | "Manual"
        self._active_demo  = "live"
        self._last_sentiment_time = 0.0
        self._mood_applied        = False
        self.analyzer = ContextAnalyzer()
        self.engine   = DecisionEngine()
        self.policy   = PolicyManager()
        self.enricher = ContextEnricher()

        self.influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)

        self.mqtt_client = mqtt.Client(client_id="smarthome-agent")
        if MQTT_USER and MQTT_PASSWORD:
            self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        if MQTT_TLS:
            self.mqtt_client.tls_set(ca_certs=MQTT_CA_CERT)
        self.mqtt_client.on_connect    = self._on_connect
        self.mqtt_client.on_message    = self._on_message
        self.mqtt_client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[Agent] MQTT broker'a bağlandı ✓")
            client.subscribe(TOPIC_SENSOR_ALL)
            client.subscribe(TOPIC_FEEDBACK)
            client.subscribe(TOPIC_PREFERENCES)
            client.subscribe(TOPIC_SENTIMENT)
            client.subscribe(TOPIC_SYSTEM_MODE)
            client.subscribe(TOPIC_SYSTEM_DEMO)
            print(f"[Agent] Dinleniyor: {TOPIC_SENSOR_ALL}")
        else:
            print(f"[Agent] Bağlantı hatası, kod: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[Agent] Bağlantı kesildi (rc={rc}), yeniden bağlanılıyor...")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            print(f"[Agent] Geçersiz JSON — topic: {topic}")
            return

        if "/sensor/" in topic:
            self._handle_sensor(topic, payload)
        elif "/feedback" in topic:
            self._handle_feedback(topic, payload)
        elif topic == TOPIC_PREFERENCES:
            self.policy.update_preferences(payload)
            print(f"[Agent] Tercihler güncellendi: {payload}")
        elif topic == TOPIC_SENTIMENT:
            self._handle_sentiment(payload)
        elif topic == TOPIC_SYSTEM_MODE:
            self._handle_system_mode(payload)
        elif topic == TOPIC_SYSTEM_DEMO:
            self._handle_system_demo(payload)

    def _handle_sentiment(self, payload: dict):
        sentiment = payload.get("sentiment", "nötr")
        self.enricher.update_sentiment(sentiment)
        self._last_sentiment_time = time.time()
        print(f"[Agent] Kullanıcı duygu durumu güncellendi: {sentiment}")
        self._last_context = {}

        # In the "Arriving Home" demo, immediately personalise the house
        if self._active_demo == "fair_arriving":
            self._prepare_home_for_mood(sentiment)

    def _handle_system_mode(self, payload: dict):
        mode = payload.get("mode", "AI")
        self._system_mode = mode
        print(f"[Agent] Sistem modu değiştirildi: {mode}")
        self._last_context = {}  # force re-evaluation on next sensor tick

    def _handle_system_demo(self, payload: dict):
        self._active_demo = payload.get("active", "live")
        self._mood_applied = False
        print(f"[Agent] Demo scenario: {self._active_demo}")
        self._last_context = {}

        # Prompt the visitor to pick a mood via Telegram
        if self._active_demo == "fair_arriving":
            # If mood was selected within the last 5 minutes, apply it now
            recent_mood = (time.time() - self._last_sentiment_time) < 300
            if recent_mood:
                sentiment = self.enricher._sentiment_str
                print(f"[Agent] fair_arriving: recent mood '{sentiment}' found, applying now")
                self._prepare_home_for_mood(sentiment)
            else:
                self.mqtt_client.publish(TOPIC_ALERT, json.dumps({
                    "message": (
                        "🏠 You've arrived home!\n"
                        "Open the Telegram bot and tap /mood to personalise your space."
                    ),
                    "room": "home",
                    "timestamp": datetime.now().isoformat(),
                    "severity": "normal",
                }))
                print("[Agent] fair_arriving: Telegram prompt sent")

    def _prepare_home_for_mood(self, sentiment: str):
        """
        Immediately publish actuator commands to all rooms based on the
        user's selected mood. Called only during the 'fair_arriving' demo.
        """
        config = MOOD_ROOM_CONFIGS.get(sentiment, MOOD_ROOM_CONFIGS["notr"])
        print(f"[Agent] 🏠 Preparing home for mood: {sentiment}")

        for room, devices in config.items():
            for device, command in devices.items():
                if device not in ROOM_ACTUATORS.get(room, set()):
                    continue
                topic = f"{TOPIC_CMD_PREFIX}/{room}/{device}/command"
                self.mqtt_client.publish(topic, json.dumps({
                    "command":       command,
                    "reason":        f"Mood-based setup: {sentiment}",
                    "method":        "mood",
                    "confidence":    "100%",
                    "context_label": f"arriving_{sentiment}",
                    "timestamp":     datetime.now().isoformat(),
                }))
                print(f"[Agent] ✓ Mood setup → {topic}: {command}")

        # Notify the user via Telegram
        message = MOOD_MESSAGES.get(sentiment, f"Welcome home! Mood: {sentiment}")
        self.mqtt_client.publish(TOPIC_ALERT, json.dumps({
            "message":   message,
            "room":      "home",
            "timestamp": datetime.now().isoformat(),
            "severity":  "normal",
        }))

        # Play mood-matching playlist
        self.engine.play_for_mood(sentiment)

        self._mood_applied = True
        print(f"[Agent] 🏠 Home ready — autonomous decisions paused for this demo")

    def _handle_sensor(self, topic, payload):
        parts = topic.split("/")
        room = parts[1] if len(parts) > 1 else "unknown"
        if self._active_demo != "live" and not payload.get("demo"):
            return

        payload["timestamp"] = payload.get("timestamp", datetime.now().isoformat())
        payload["room"] = room
        self._write_to_influx(payload)
        context = self.analyzer.analyze(payload)
        context = self.enricher.enrich(context)
        features = self.analyzer.to_feature_vector(context)

        print(f"[Agent] Bağlam: {context['context_label']} | "
              f"Sıcaklık: {context['temperature']}°C | "
              f"Hareket: {context['occupancy']}")

        self._check_alerts(context, room)

        # Respect system mode — only make autonomous decisions in AI mode
        if self._system_mode != "AI":
            return

        # After mood-based setup, don't let autonomous decisions override it
        if self._mood_applied:
            return

        current_label  = context.get("context_label")
        last_label     = self._last_context.get("context_label")
        temp_diff      = abs(context.get("temperature", 0) - self._last_context.get("temperature", 0))
        motion_changed = context.get("occupancy") != self._last_context.get("occupancy")

        if current_label == last_label and temp_diff < 2.0 and not motion_changed:
            return

        self._last_context = context
        actions = self.engine.decide(context, features)

        for action in actions:
            action["room"] = room
            result = self.policy.apply(action, context)
            if result["approved"]:
                self._execute_action(action, context)
            else:
                print(f"[Agent] Karar reddedildi: {result['reason']}")

    def _execute_action(self, action: dict, context: dict):
        device         = action["device"]
        room           = action["room"]
        command        = action["command"]
        reason         = action["reason"]
        confidence     = action.get("confidence", None)
        method         = action.get("method", "heuristic")
        context_label  = context.get("context_label", "bilinmiyor")
        confidence_str = f"{confidence:.0%}" if confidence else "—"

        if device not in ROOM_ACTUATORS.get(room, {"light", "lights"}):
            print(f"[Agent] Skipped unsupported command for {room}: {device} -> {command}")
            return

        if SIMULATION_MODE:
            print(f"[Agent][SİMÜLASYON] Komut → {room}/{device}: {command}")
            print(f"         Gerekçe: {reason} | Yöntem: {method} | Güven: {confidence_str} | Bağlam: {context_label}")
        else:
            topic = f"{TOPIC_CMD_PREFIX}/{room}/{device}/command"
            self.mqtt_client.publish(topic, json.dumps({
                "command": command, "reason": reason, "method": method,
                "confidence": confidence_str, "context_label": context_label,
                "timestamp": datetime.now().isoformat(),
            }))
            print(f"[Agent] ✓ Komut → {topic}: {command}")
            print(f"         Gerekçe: {reason} | Yöntem: {method} | Güven: {confidence_str} | Bağlam: {context_label}")

        self._log_action(device, room, command, reason, context)

    def _handle_feedback(self, topic, payload):
        device  = payload.get("device")
        command = payload.get("command")
        sensor  = payload.get("sensor_data", {})
        if device and command and sensor:
            context  = self.analyzer.analyze(sensor)
            features = self.analyzer.to_feature_vector(context)
            self.engine.record_feedback(features, device, command)
            room = payload.get("room", "general")
            self.policy.set_manual_override(f"{room}_{device}", command)
            print(f"[Agent] Feedback alındı: {device} → {command} (öğrenme kaydedildi)")

    def _check_alerts(self, context: dict, room: str):
        alerts = []

        if context.get("smoke"):
            alerts.append(("🔥 Smoke detected in " + room.replace("_", " ").title() + "! Exhaust fan activated.", "high"))
        if context.get("temperature", 0) > 35:
            alerts.append((f"🌡️ Critical temperature in {room.replace('_', ' ').title()}: {context['temperature']}°C", "high"))
        if context.get("temperature", 0) < 10:
            alerts.append((f"🥶 Low temperature in {room.replace('_', ' ').title()}: {context['temperature']}°C", "warning"))

        for message, severity in alerts:
            self.mqtt_client.publish(TOPIC_ALERT, json.dumps({
                "message": message, "room": room,
                "timestamp": datetime.now().isoformat(), "severity": severity,
            }))
            print(f"[Agent] ALERT ({severity}): {message}")

    def _write_to_influx(self, data: dict):
        room = data.get("room", "unknown")
        try:
            point = (Point("sensor_reading")
                .tag("room", room)
                .field("temperature", float(data.get("temperature", 0)))
                .field("humidity",    float(data.get("humidity", 0)))
                .field("motion",      int(data.get("motion", 0)))
                .field("smoke",       int(data.get("smoke", 0)))
                .field("light",       float(data.get("light", 0))))
            self.write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        except Exception as e:
            print(f"[Agent] InfluxDB yazma hatası: room={room} → {e}")

    def _log_action(self, device, room, command, reason, context):
        try:
            point = (Point("action_log")
                .tag("device", device).tag("room", room)
                .tag("command", command).tag("context", context.get("context_label", "unknown"))
                .field("reason", reason)
                .field("temperature", float(context.get("temperature", 0))))
            self.write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        except Exception as e:
            print(f"[Agent] Action log hatası: {e}")

    def run(self):
        print("[Agent] Akıllı ev agent'ı başlatılıyor...")
        while True:
            try:
                self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                self.mqtt_client.loop_forever()
            except Exception as e:
                print(f"[Agent] Bağlantı hatası: {e} — 5 saniye sonra tekrar denenecek")
                time.sleep(5)


if __name__ == "__main__":
    agent = SmartHomeAgent()
    agent.run()
